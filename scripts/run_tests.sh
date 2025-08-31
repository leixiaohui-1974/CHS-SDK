#!/bin/bash

# CHS Simulation Platform 测试运行脚本
# 运行各种类型的测试：单元测试、集成测试、端到端测试、性能测试、安全测试

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."
TEST_RESULTS_DIR="$PROJECT_ROOT/test-results"
COVERAGE_DIR="$PROJECT_ROOT/coverage"
LOG_DIR="$PROJECT_ROOT/logs"

# 默认配置
RUN_UNIT_TESTS=true
RUN_INTEGRATION_TESTS=true
RUN_E2E_TESTS=false
RUN_PERFORMANCE_TESTS=false
RUN_SECURITY_TESTS=false
GENERATE_COVERAGE=true
VERBOSE=false
PARALLEL=true
ENVIRONMENT="test"
CLEANUP_AFTER=true

# 函数定义
print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

show_help() {
    cat << EOF
CHS Simulation Platform 测试运行脚本

用法: $0 [选项]

选项:
  -h, --help              显示此帮助信息
  -v, --verbose           详细输出
  -e, --environment ENV   测试环境 (test|staging|production) [默认: test]
  --unit                  只运行单元测试
  --integration           只运行集成测试
  --e2e                   只运行端到端测试
  --performance           只运行性能测试
  --security              只运行安全测试
  --all                   运行所有测试
  --no-coverage           不生成覆盖率报告
  --no-parallel           不使用并行测试
  --no-cleanup            测试后不清理
  --docker                在Docker环境中运行测试
  --ci                    CI模式（适用于持续集成）

示例:
  $0                      # 运行默认测试套件
  $0 --all               # 运行所有测试
  $0 --unit --integration # 只运行单元和集成测试
  $0 --e2e --verbose     # 运行端到端测试并显示详细输出
  $0 --performance --security # 运行性能和安全测试
  $0 --ci                # CI模式运行
EOF
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --unit)
                RUN_UNIT_TESTS=true
                RUN_INTEGRATION_TESTS=false
                RUN_E2E_TESTS=false
                RUN_PERFORMANCE_TESTS=false
                RUN_SECURITY_TESTS=false
                shift
                ;;
            --integration)
                RUN_UNIT_TESTS=false
                RUN_INTEGRATION_TESTS=true
                RUN_E2E_TESTS=false
                RUN_PERFORMANCE_TESTS=false
                RUN_SECURITY_TESTS=false
                shift
                ;;
            --e2e)
                RUN_UNIT_TESTS=false
                RUN_INTEGRATION_TESTS=false
                RUN_E2E_TESTS=true
                RUN_PERFORMANCE_TESTS=false
                RUN_SECURITY_TESTS=false
                shift
                ;;
            --performance)
                RUN_UNIT_TESTS=false
                RUN_INTEGRATION_TESTS=false
                RUN_E2E_TESTS=false
                RUN_PERFORMANCE_TESTS=true
                RUN_SECURITY_TESTS=false
                shift
                ;;
            --security)
                RUN_UNIT_TESTS=false
                RUN_INTEGRATION_TESTS=false
                RUN_E2E_TESTS=false
                RUN_PERFORMANCE_TESTS=false
                RUN_SECURITY_TESTS=true
                shift
                ;;
            --all)
                RUN_UNIT_TESTS=true
                RUN_INTEGRATION_TESTS=true
                RUN_E2E_TESTS=true
                RUN_PERFORMANCE_TESTS=true
                RUN_SECURITY_TESTS=true
                shift
                ;;
            --no-coverage)
                GENERATE_COVERAGE=false
                shift
                ;;
            --no-parallel)
                PARALLEL=false
                shift
                ;;
            --no-cleanup)
                CLEANUP_AFTER=false
                shift
                ;;
            --docker)
                USE_DOCKER=true
                shift
                ;;
            --ci)
                # CI模式配置
                VERBOSE=true
                PARALLEL=true
                GENERATE_COVERAGE=true
                CLEANUP_AFTER=true
                RUN_UNIT_TESTS=true
                RUN_INTEGRATION_TESTS=true
                shift
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 检查依赖
check_dependencies() {
    print_header "检查依赖"
    
    local missing_deps=()
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        missing_deps+=("node")
    fi
    
    # 检查pytest
    if ! python3 -c "import pytest" &> /dev/null; then
        missing_deps+=("pytest")
    fi
    
    # 检查Docker（如果需要）
    if [[ "$USE_DOCKER" == "true" ]] && ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "缺少依赖: ${missing_deps[*]}"
        print_info "请安装缺少的依赖后重试"
        exit 1
    fi
    
    print_success "所有依赖检查通过"
}

# 设置测试环境
setup_test_environment() {
    print_header "设置测试环境"
    
    # 创建必要的目录
    mkdir -p "$TEST_RESULTS_DIR"
    mkdir -p "$COVERAGE_DIR"
    mkdir -p "$LOG_DIR"
    
    # 设置环境变量
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    export NODE_ENV="test"
    export TESTING="true"
    
    # 根据环境设置配置
    case $ENVIRONMENT in
        "test")
            export DATABASE_URL="postgresql://test:test@localhost:5433/test_db"
            export REDIS_URL="redis://localhost:6380"
            ;;
        "staging")
            export DATABASE_URL="postgresql://staging:staging@localhost:5432/staging_db"
            export REDIS_URL="redis://localhost:6379"
            ;;
        "production")
            print_warning "在生产环境运行测试，请确保这是您想要的"
            ;;
    esac
    
    print_success "测试环境设置完成"
}

# 启动测试服务
start_test_services() {
    print_header "启动测试服务"
    
    if [[ "$USE_DOCKER" == "true" ]]; then
        print_info "使用Docker启动测试服务"
        
        # 启动测试数据库和Redis
        docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" up -d test-db test-redis
        
        # 等待服务就绪
        print_info "等待数据库就绪..."
        timeout 60 bash -c 'until docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" exec test-db pg_isready; do sleep 1; done'
        
        print_info "等待Redis就绪..."
        timeout 60 bash -c 'until docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" exec test-redis redis-cli ping; do sleep 1; done'
        
        # 运行数据库迁移
        print_info "运行数据库迁移"
        cd "$PROJECT_ROOT/api"
        python3 -m alembic upgrade head
        cd "$PROJECT_ROOT"
    else
        print_info "使用本地服务"
        # 这里可以添加启动本地服务的逻辑
    fi
    
    print_success "测试服务启动完成"
}

# 运行单元测试
run_unit_tests() {
    if [[ "$RUN_UNIT_TESTS" != "true" ]]; then
        return 0
    fi
    
    print_header "运行单元测试"
    
    local pytest_args=()
    
    if [[ "$VERBOSE" == "true" ]]; then
        pytest_args+=("-v")
    fi
    
    if [[ "$PARALLEL" == "true" ]]; then
        pytest_args+=("-n" "auto")
    fi
    
    if [[ "$GENERATE_COVERAGE" == "true" ]]; then
        pytest_args+=("--cov=api" "--cov-report=html:$COVERAGE_DIR/unit" "--cov-report=xml:$COVERAGE_DIR/unit.xml")
    fi
    
    pytest_args+=("--junitxml=$TEST_RESULTS_DIR/unit-tests.xml")
    pytest_args+=("$PROJECT_ROOT/tests/unit")
    
    cd "$PROJECT_ROOT"
    
    if python3 -m pytest "${pytest_args[@]}"; then
        print_success "单元测试通过"
        return 0
    else
        print_error "单元测试失败"
        return 1
    fi
}

# 运行集成测试
run_integration_tests() {
    if [[ "$RUN_INTEGRATION_TESTS" != "true" ]]; then
        return 0
    fi
    
    print_header "运行集成测试"
    
    local pytest_args=()
    
    if [[ "$VERBOSE" == "true" ]]; then
        pytest_args+=("-v")
    fi
    
    if [[ "$GENERATE_COVERAGE" == "true" ]]; then
        pytest_args+=("--cov=api" "--cov-report=html:$COVERAGE_DIR/integration" "--cov-report=xml:$COVERAGE_DIR/integration.xml")
    fi
    
    pytest_args+=("--junitxml=$TEST_RESULTS_DIR/integration-tests.xml")
    pytest_args+=("$PROJECT_ROOT/tests/integration")
    
    cd "$PROJECT_ROOT"
    
    if python3 -m pytest "${pytest_args[@]}"; then
        print_success "集成测试通过"
        return 0
    else
        print_error "集成测试失败"
        return 1
    fi
}

# 运行前端测试
run_frontend_tests() {
    print_header "运行前端测试"
    
    cd "$PROJECT_ROOT/frontend"
    
    # 安装依赖
    if [[ ! -d "node_modules" ]]; then
        print_info "安装前端依赖"
        npm install
    fi
    
    # 运行测试
    local npm_args=()
    
    if [[ "$VERBOSE" == "true" ]]; then
        npm_args+=("--verbose")
    fi
    
    if [[ "$GENERATE_COVERAGE" == "true" ]]; then
        npm_args+=("--coverage" "--coverageDirectory=$COVERAGE_DIR/frontend")
    fi
    
    if npm test "${npm_args[@]}"; then
        print_success "前端测试通过"
        cd "$PROJECT_ROOT"
        return 0
    else
        print_error "前端测试失败"
        cd "$PROJECT_ROOT"
        return 1
    fi
}

# 运行端到端测试
run_e2e_tests() {
    if [[ "$RUN_E2E_TESTS" != "true" ]]; then
        return 0
    fi
    
    print_header "运行端到端测试"
    
    # 启动应用服务
    print_info "启动应用服务进行E2E测试"
    
    if [[ "$USE_DOCKER" == "true" ]]; then
        docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" up -d test-api test-frontend
        
        # 等待服务就绪
        print_info "等待API服务就绪..."
        timeout 120 bash -c 'until curl -f http://localhost:8000/health; do sleep 2; done'
        
        print_info "等待前端服务就绪..."
        timeout 120 bash -c 'until curl -f http://localhost:3000; do sleep 2; done'
    else
        # 启动本地服务
        print_info "启动本地API服务"
        cd "$PROJECT_ROOT/api"
        python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
        API_PID=$!
        
        print_info "启动本地前端服务"
        cd "$PROJECT_ROOT/frontend"
        npm start &
        FRONTEND_PID=$!
        
        cd "$PROJECT_ROOT"
        
        # 等待服务就绪
        sleep 10
    fi
    
    # 运行E2E测试
    local pytest_args=()
    
    if [[ "$VERBOSE" == "true" ]]; then
        pytest_args+=("-v" "-s")
    fi
    
    pytest_args+=("--junitxml=$TEST_RESULTS_DIR/e2e-tests.xml")
    pytest_args+=("$PROJECT_ROOT/tests/e2e")
    
    local e2e_result=0
    
    if python3 -m pytest "${pytest_args[@]}"; then
        print_success "端到端测试通过"
    else
        print_error "端到端测试失败"
        e2e_result=1
    fi
    
    # 清理服务
    if [[ "$USE_DOCKER" == "true" ]]; then
        docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" stop test-api test-frontend
    else
        if [[ -n "$API_PID" ]]; then
            kill $API_PID 2>/dev/null || true
        fi
        if [[ -n "$FRONTEND_PID" ]]; then
            kill $FRONTEND_PID 2>/dev/null || true
        fi
    fi
    
    return $e2e_result
}

# 运行性能测试
run_performance_tests() {
    if [[ "$RUN_PERFORMANCE_TESTS" != "true" ]]; then
        return 0
    fi
    
    print_header "运行性能测试"
    
    # 确保服务运行
    print_info "确保服务运行以进行性能测试"
    
    if [[ "$USE_DOCKER" == "true" ]]; then
        docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" up -d test-api
        timeout 60 bash -c 'until curl -f http://localhost:8000/health; do sleep 2; done'
    fi
    
    # 运行性能测试
    local pytest_args=()
    
    if [[ "$VERBOSE" == "true" ]]; then
        pytest_args+=("-v" "-s")
    fi
    
    pytest_args+=("--junitxml=$TEST_RESULTS_DIR/performance-tests.xml")
    pytest_args+=("$PROJECT_ROOT/tests/performance")
    
    cd "$PROJECT_ROOT"
    
    if python3 -m pytest "${pytest_args[@]}"; then
        print_success "性能测试通过"
        return 0
    else
        print_error "性能测试失败"
        return 1
    fi
}

# 运行安全测试
run_security_tests() {
    if [[ "$RUN_SECURITY_TESTS" != "true" ]]; then
        return 0
    fi
    
    print_header "运行安全测试"
    
    # 确保服务运行
    print_info "确保服务运行以进行安全测试"
    
    if [[ "$USE_DOCKER" == "true" ]]; then
        docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" up -d test-api
        timeout 60 bash -c 'until curl -f http://localhost:8000/health; do sleep 2; done'
    fi
    
    # 运行安全测试
    local pytest_args=()
    
    if [[ "$VERBOSE" == "true" ]]; then
        pytest_args+=("-v" "-s")
    fi
    
    pytest_args+=("--junitxml=$TEST_RESULTS_DIR/security-tests.xml")
    pytest_args+=("$PROJECT_ROOT/tests/security")
    
    cd "$PROJECT_ROOT"
    
    if python3 -m pytest "${pytest_args[@]}"; then
        print_success "安全测试通过"
        return 0
    else
        print_error "安全测试失败"
        return 1
    fi
}

# 生成测试报告
generate_test_report() {
    print_header "生成测试报告"
    
    local report_file="$TEST_RESULTS_DIR/test-report.html"
    
    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>CHS Simulation Platform 测试报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .success { background-color: #d4edda; border-color: #c3e6cb; }
        .failure { background-color: #f8d7da; border-color: #f5c6cb; }
        .warning { background-color: #fff3cd; border-color: #ffeaa7; }
        .info { background-color: #d1ecf1; border-color: #bee5eb; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>CHS Simulation Platform 测试报告</h1>
        <p>生成时间: $(date)</p>
        <p>测试环境: $ENVIRONMENT</p>
    </div>
EOF
    
    # 添加测试结果摘要
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    
    # 统计测试结果
    if [[ -f "$TEST_RESULTS_DIR/unit-tests.xml" ]]; then
        local unit_stats=$(python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('$TEST_RESULTS_DIR/unit-tests.xml')
root = tree.getroot()
print(f'{root.attrib.get(\"tests\", 0)} {root.attrib.get(\"failures\", 0)} {root.attrib.get(\"errors\", 0)}')
" 2>/dev/null || echo "0 0 0")
        
        read unit_total unit_failures unit_errors <<< "$unit_stats"
        total_tests=$((total_tests + unit_total))
        failed_tests=$((failed_tests + unit_failures + unit_errors))
        passed_tests=$((passed_tests + unit_total - unit_failures - unit_errors))
    fi
    
    # 添加更多测试类型的统计...
    
    cat >> "$report_file" << EOF
    <div class="section info">
        <h2>测试摘要</h2>
        <table>
            <tr><th>测试类型</th><th>总数</th><th>通过</th><th>失败</th><th>状态</th></tr>
            <tr><td>单元测试</td><td>$unit_total</td><td>$((unit_total - unit_failures - unit_errors))</td><td>$((unit_failures + unit_errors))</td><td>$([ $((unit_failures + unit_errors)) -eq 0 ] && echo "✅" || echo "❌")</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>覆盖率报告</h2>
        <p>详细的覆盖率报告请查看 <a href="../coverage/index.html">coverage/index.html</a></p>
    </div>
    
    <div class="section">
        <h2>测试文件</h2>
        <ul>
EOF
    
    # 列出所有测试结果文件
    for file in "$TEST_RESULTS_DIR"/*.xml; do
        if [[ -f "$file" ]]; then
            echo "            <li><a href=\"$(basename "$file")\">${file##*/}</a></li>" >> "$report_file"
        fi
    done
    
    cat >> "$report_file" << EOF
        </ul>
    </div>
</body>
</html>
EOF
    
    print_success "测试报告生成完成: $report_file"
}

# 清理测试环境
cleanup_test_environment() {
    if [[ "$CLEANUP_AFTER" != "true" ]]; then
        return 0
    fi
    
    print_header "清理测试环境"
    
    if [[ "$USE_DOCKER" == "true" ]]; then
        print_info "停止Docker测试服务"
        docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" down
    fi
    
    # 清理临时文件
    find "$PROJECT_ROOT" -name "*.pyc" -delete 2>/dev/null || true
    find "$PROJECT_ROOT" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    print_success "测试环境清理完成"
}

# 主函数
main() {
    local start_time=$(date +%s)
    local exit_code=0
    
    print_header "CHS Simulation Platform 测试套件"
    
    # 解析参数
    parse_args "$@"
    
    # 显示配置
    if [[ "$VERBOSE" == "true" ]]; then
        print_info "测试配置:"
        echo "  环境: $ENVIRONMENT"
        echo "  单元测试: $RUN_UNIT_TESTS"
        echo "  集成测试: $RUN_INTEGRATION_TESTS"
        echo "  端到端测试: $RUN_E2E_TESTS"
        echo "  性能测试: $RUN_PERFORMANCE_TESTS"
        echo "  安全测试: $RUN_SECURITY_TESTS"
        echo "  生成覆盖率: $GENERATE_COVERAGE"
        echo "  并行执行: $PARALLEL"
        echo "  使用Docker: ${USE_DOCKER:-false}"
    fi
    
    # 检查依赖
    check_dependencies
    
    # 设置测试环境
    setup_test_environment
    
    # 启动测试服务
    start_test_services
    
    # 运行测试
    local test_results=()
    
    # 单元测试
    if run_unit_tests; then
        test_results+=("单元测试: ✅")
    else
        test_results+=("单元测试: ❌")
        exit_code=1
    fi
    
    # 前端测试
    if run_frontend_tests; then
        test_results+=("前端测试: ✅")
    else
        test_results+=("前端测试: ❌")
        exit_code=1
    fi
    
    # 集成测试
    if run_integration_tests; then
        test_results+=("集成测试: ✅")
    else
        test_results+=("集成测试: ❌")
        exit_code=1
    fi
    
    # 端到端测试
    if run_e2e_tests; then
        test_results+=("端到端测试: ✅")
    else
        test_results+=("端到端测试: ❌")
        exit_code=1
    fi
    
    # 性能测试
    if run_performance_tests; then
        test_results+=("性能测试: ✅")
    else
        test_results+=("性能测试: ❌")
        exit_code=1
    fi
    
    # 安全测试
    if run_security_tests; then
        test_results+=("安全测试: ✅")
    else
        test_results+=("安全测试: ❌")
        exit_code=1
    fi
    
    # 生成测试报告
    generate_test_report
    
    # 清理环境
    cleanup_test_environment
    
    # 显示结果
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_header "测试结果摘要"
    
    for result in "${test_results[@]}"; do
        echo "  $result"
    done
    
    echo
    print_info "测试耗时: ${duration}秒"
    print_info "测试结果保存在: $TEST_RESULTS_DIR"
    
    if [[ "$GENERATE_COVERAGE" == "true" ]]; then
        print_info "覆盖率报告保存在: $COVERAGE_DIR"
    fi
    
    if [[ $exit_code -eq 0 ]]; then
        print_success "所有测试通过！"
    else
        print_error "部分测试失败，请检查测试结果"
    fi
    
    exit $exit_code
}

# 运行主函数
main "$@"