#!/bin/bash

# CHS仿真平台备份系统启动脚本
# 用于启动完整的备份系统服务

set -e

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

# 检查Docker和Docker Compose
check_dependencies() {
    log_info "检查系统依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装或不在PATH中"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装或不在PATH中"
        exit 1
    fi
    
    log_success "系统依赖检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建备份系统目录..."
    
    mkdir -p backups/{database,files,full,temp}
    mkdir -p logs/backup
    mkdir -p config/backup
    
    log_success "目录创建完成"
}

# 检查配置文件
check_config() {
    log_info "检查配置文件..."
    
    local config_files=(
        "config/backup/scheduler_config.json"
        "config/backup/database_backup.json"
        "config/backup/file_backup.json"
        "config/backup/disaster_recovery.yaml"
    )
    
    for config_file in "${config_files[@]}"; do
        if [[ ! -f "$config_file" ]]; then
            log_error "配置文件不存在: $config_file"
            exit 1
        fi
    done
    
    log_success "配置文件检查通过"
}

# 检查环境变量
check_env() {
    log_info "检查环境变量..."
    
    local required_vars=(
        "POSTGRES_PASSWORD"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "缺少必需的环境变量: ${missing_vars[*]}"
        log_info "请在.env文件中设置这些变量"
        exit 1
    fi
    
    log_success "环境变量检查通过"
}

# 构建Docker镜像
build_images() {
    log_info "构建备份系统Docker镜像..."
    
    docker-compose -f docker-compose.backup.yml build
    
    if [[ $? -eq 0 ]]; then
        log_success "Docker镜像构建完成"
    else
        log_error "Docker镜像构建失败"
        exit 1
    fi
}

# 启动备份系统
start_backup_system() {
    log_info "启动备份系统..."
    
    # 启动备份调度器
    docker-compose -f docker-compose.backup.yml up -d backup-scheduler
    
    if [[ $? -eq 0 ]]; then
        log_success "备份调度器启动成功"
    else
        log_error "备份调度器启动失败"
        exit 1
    fi
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    if docker-compose -f docker-compose.backup.yml ps | grep -q "Up"; then
        log_success "备份系统启动成功"
    else
        log_error "备份系统启动失败"
        docker-compose -f docker-compose.backup.yml logs
        exit 1
    fi
}

# 显示服务状态
show_status() {
    log_info "备份系统服务状态:"
    docker-compose -f docker-compose.backup.yml ps
    
    log_info "\n备份调度器日志:"
    docker-compose -f docker-compose.backup.yml logs --tail=20 backup-scheduler
}

# 显示使用说明
show_usage() {
    echo "CHS仿真平台备份系统管理脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  start     启动备份系统"
    echo "  stop      停止备份系统"
    echo "  restart   重启备份系统"
    echo "  status    显示服务状态"
    echo "  logs      显示日志"
    echo "  backup    手动执行备份"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start          # 启动备份系统"
    echo "  $0 backup db      # 手动执行数据库备份"
    echo "  $0 backup files   # 手动执行文件备份"
    echo "  $0 backup full    # 手动执行完整备份"
}

# 手动执行备份
manual_backup() {
    local backup_type="$1"
    
    case "$backup_type" in
        "db"|"database")
            log_info "执行数据库备份..."
            docker-compose -f docker-compose.backup.yml run --rm database-backup
            ;;
        "files")
            log_info "执行文件备份..."
            docker-compose -f docker-compose.backup.yml run --rm file-backup
            ;;
        "full")
            log_info "执行完整备份..."
            docker-compose -f docker-compose.backup.yml run --rm backup-scheduler \
                python /app/scripts/backup/backup_scheduler.py \
                --config /app/config/backup/scheduler_config.json \
                --run weekly_full_backup
            ;;
        *)
            log_error "未知的备份类型: $backup_type"
            log_info "支持的备份类型: db, files, full"
            exit 1
            ;;
    esac
}

# 主函数
main() {
    local action="${1:-help}"
    
    case "$action" in
        "start")
            check_dependencies
            create_directories
            check_config
            check_env
            build_images
            start_backup_system
            show_status
            ;;
        "stop")
            log_info "停止备份系统..."
            docker-compose -f docker-compose.backup.yml down
            log_success "备份系统已停止"
            ;;
        "restart")
            log_info "重启备份系统..."
            docker-compose -f docker-compose.backup.yml restart
            log_success "备份系统已重启"
            ;;
        "status")
            show_status
            ;;
        "logs")
            docker-compose -f docker-compose.backup.yml logs -f
            ;;
        "backup")
            manual_backup "$2"
            ;;
        "help"|"--help"|"")
            show_usage
            ;;
        *)
            log_error "未知的操作: $action"
            show_usage
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"