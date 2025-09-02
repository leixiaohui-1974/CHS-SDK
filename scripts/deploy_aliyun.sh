#!/bin/bash
# CHS-SDK 阿里云自动化部署脚本
# 使用阿里云CLI和Docker进行部署

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 配置变量
PROJECT_NAME="chs-sdk"
REGION="cn-hangzhou"
IMAGE_NAME="chs-sdk-api"
CONTAINER_NAME="chs-api"
DOCKER_REGISTRY="registry.cn-hangzhou.aliyuncs.com"
NAMESPACE="your-namespace"  # 请替换为您的命名空间

# 检查必要的工具
check_dependencies() {
    log_info "检查部署依赖..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查阿里云CLI
    if ! command -v aliyun &> /dev/null; then
        log_error "阿里云CLI未安装，请先安装aliyun-cli"
        exit 1
    fi
    
    # 检查环境变量
    if [[ -z "$ALIYUN_ACCESS_KEY_ID" || -z "$ALIYUN_ACCESS_KEY_SECRET" ]]; then
        log_error "请设置阿里云访问密钥环境变量 ALIYUN_ACCESS_KEY_ID 和 ALIYUN_ACCESS_KEY_SECRET"
        exit 1
    fi
    
    log_success "依赖检查完成"
}

# 构建Docker镜像
build_image() {
    log_info "构建Docker镜像..."
    
    # 构建镜像
    docker build -t $IMAGE_NAME:latest .
    
    # 标记镜像
    docker tag $IMAGE_NAME:latest $DOCKER_REGISTRY/$NAMESPACE/$IMAGE_NAME:latest
    docker tag $IMAGE_NAME:latest $DOCKER_REGISTRY/$NAMESPACE/$IMAGE_NAME:$(date +%Y%m%d-%H%M%S)
    
    log_success "Docker镜像构建完成"
}

# 推送镜像到阿里云容器镜像服务
push_image() {
    log_info "推送镜像到阿里云容器镜像服务..."
    
    # 登录到阿里云容器镜像服务
    docker login --username=$ALIYUN_ACCESS_KEY_ID $DOCKER_REGISTRY
    
    # 推送镜像
    docker push $DOCKER_REGISTRY/$NAMESPACE/$IMAGE_NAME:latest
    docker push $DOCKER_REGISTRY/$NAMESPACE/$IMAGE_NAME:$(date +%Y%m%d-%H%M%S)
    
    log_success "镜像推送完成"
}

# 创建ECS实例（如果不存在）
create_ecs_instance() {
    log_info "检查ECS实例..."
    
    # 检查实例是否存在
    INSTANCE_ID=$(aliyun ecs DescribeInstances --RegionId $REGION --InstanceName $PROJECT_NAME-server --output cols=InstanceId --quiet 2>/dev/null || echo "")
    
    if [[ -z "$INSTANCE_ID" ]]; then
        log_info "创建新的ECS实例..."
        
        # 创建ECS实例
        INSTANCE_ID=$(aliyun ecs CreateInstance \
            --RegionId $REGION \
            --ImageId $ALIYUN_ECS_IMAGE_ID \
            --InstanceType $ALIYUN_ECS_INSTANCE_TYPE \
            --SecurityGroupId $ALIYUN_ECS_SECURITY_GROUP_ID \
            --VSwitchId $ALIYUN_ECS_VSWITCH_ID \
            --InstanceName $PROJECT_NAME-server \
            --Description "CHS-SDK API Server" \
            --InternetMaxBandwidthOut 100 \
            --InstanceChargeType PostPaid \
            --output cols=InstanceId --quiet)
        
        # 启动实例
        aliyun ecs StartInstance --InstanceId $INSTANCE_ID
        
        log_success "ECS实例创建完成: $INSTANCE_ID"
    else
        log_info "使用现有ECS实例: $INSTANCE_ID"
    fi
    
    # 等待实例运行
    log_info "等待ECS实例启动..."
    while true; do
        STATUS=$(aliyun ecs DescribeInstances --RegionId $REGION --InstanceIds "['$INSTANCE_ID']" --output cols=Status --quiet)
        if [[ "$STATUS" == "Running" ]]; then
            break
        fi
        sleep 5
    done
    
    # 获取公网IP
    PUBLIC_IP=$(aliyun ecs DescribeInstances --RegionId $REGION --InstanceIds "['$INSTANCE_ID']" --output cols=PublicIpAddress --quiet)
    log_success "ECS实例运行中，公网IP: $PUBLIC_IP"
}

# 部署应用到ECS
deploy_to_ecs() {
    log_info "部署应用到ECS实例..."
    
    # 创建部署脚本
    cat > deploy_script.sh << EOF
#!/bin/bash
# 安装Docker（如果未安装）
if ! command -v docker &> /dev/null; then
    yum update -y
    yum install -y docker
    systemctl start docker
    systemctl enable docker
fi

# 安装Docker Compose（如果未安装）
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 停止现有容器
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# 拉取最新镜像
docker login --username=$ALIYUN_ACCESS_KEY_ID $DOCKER_REGISTRY
docker pull $DOCKER_REGISTRY/$NAMESPACE/$IMAGE_NAME:latest

# 运行新容器
docker run -d \
    --name $CONTAINER_NAME \
    --restart unless-stopped \
    -p 80:8000 \
    -p 443:8000 \
    -e ENVIRONMENT=production \
    -e DATABASE_URL=\"postgresql://\${POSTGRES_USER}:\${POSTGRES_PASSWORD}@postgres:5432/\${POSTGRES_DB}\" \
    -e REDIS_URL=\"redis://:\${REDIS_PASSWORD}@redis:6379/0\" \
    -e SECRET_KEY=\"\${SECRET_KEY}\" \
    -e ALIYUN_ACCESS_KEY_ID=\"\${ALIYUN_ACCESS_KEY_ID}\" \
    -e ALIYUN_ACCESS_KEY_SECRET=\"\${ALIYUN_ACCESS_KEY_SECRET}\" \
    -e ALIYUN_REGION=\"\${ALIYUN_REGION}\" \
    -v /app/logs:/app/logs \
    -v /app/data:/app/data \
    -v /app/uploads:/app/uploads \
    $DOCKER_REGISTRY/$NAMESPACE/$IMAGE_NAME:latest

echo "部署完成"
EOF

    # 上传并执行部署脚本
    scp -o StrictHostKeyChecking=no deploy_script.sh root@$PUBLIC_IP:/tmp/
    ssh -o StrictHostKeyChecking=no root@$PUBLIC_IP "chmod +x /tmp/deploy_script.sh && /tmp/deploy_script.sh"
    
    # 清理临时文件
    rm deploy_script.sh
    
    log_success "应用部署完成"
}

# 配置负载均衡器
setup_load_balancer() {
    log_info "配置负载均衡器..."
    
    # 检查SLB实例是否存在
    SLB_ID=$(aliyun slb DescribeLoadBalancers --RegionId $REGION --LoadBalancerName $PROJECT_NAME-slb --output cols=LoadBalancerId --quiet 2>/dev/null || echo "")
    
    if [[ -z "$SLB_ID" ]]; then
        log_info "创建负载均衡器..."
        
        # 创建SLB实例
        SLB_ID=$(aliyun slb CreateLoadBalancer \
            --RegionId $REGION \
            --LoadBalancerName $PROJECT_NAME-slb \
            --LoadBalancerSpec $ALIYUN_SLB_INSTANCE_SPEC \
            --InternetChargeType $ALIYUN_SLB_INTERNET_CHARGE_TYPE \
            --output cols=LoadBalancerId --quiet)
        
        log_success "负载均衡器创建完成: $SLB_ID"
    else
        log_info "使用现有负载均衡器: $SLB_ID"
    fi
    
    # 添加后端服务器
    aliyun slb AddBackendServers \
        --LoadBalancerId $SLB_ID \
        --BackendServers "[{'ServerId':'$INSTANCE_ID','Weight':100}]"
    
    # 创建监听器
    aliyun slb CreateLoadBalancerHTTPListener \
        --LoadBalancerId $SLB_ID \
        --ListenerPort 80 \
        --BackendServerPort 80 \
        --Bandwidth -1 \
        --HealthCheck on \
        --HealthCheckURI "/api/monitor/health" 2>/dev/null || true
    
    # 启动监听器
    aliyun slb StartLoadBalancerListener --LoadBalancerId $SLB_ID --ListenerPort 80
    
    # 获取SLB地址
    SLB_ADDRESS=$(aliyun slb DescribeLoadBalancers --RegionId $REGION --LoadBalancerId $SLB_ID --output cols=Address --quiet)
    
    log_success "负载均衡器配置完成，访问地址: http://$SLB_ADDRESS"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 等待服务启动
    sleep 30
    
    # 检查服务状态
    if curl -f http://$PUBLIC_IP/api/monitor/health > /dev/null 2>&1; then
        log_success "服务健康检查通过"
    else
        log_error "服务健康检查失败"
        exit 1
    fi
}

# 清理函数
cleanup() {
    log_info "清理临时文件..."
    rm -f deploy_script.sh
}

# 主函数
main() {
    log_info "开始CHS-SDK阿里云部署..."
    
    # 设置清理陷阱
    trap cleanup EXIT
    
    # 加载环境变量
    if [[ -f ".env.aliyun" ]]; then
        source .env.aliyun
        log_info "已加载阿里云环境变量"
    else
        log_warning "未找到.env.aliyun文件，使用默认配置"
    fi
    
    # 执行部署步骤
    check_dependencies
    build_image
    push_image
    create_ecs_instance
    deploy_to_ecs
    setup_load_balancer
    health_check
    
    log_success "CHS-SDK部署完成！"
    log_info "访问地址: http://$SLB_ADDRESS"
    log_info "API文档: http://$SLB_ADDRESS/docs"
}

# 执行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi