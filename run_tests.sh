#!/bin/bash
# run_tests.sh - 执行所有测试的脚本

echo "==== MANDAS V1.1 & V1.2 合并PR测试 ===="
echo "正在启动测试环境..."

# 设置错误处理
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

# 检查Docker是否运行
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker未运行，请启动Docker服务"
        exit 1
    fi
    log_success "Docker服务正常运行"
}

# 启动服务
start_services() {
    log_info "启动测试服务..."
    
    # 如果存在docker-compose文件，使用它启动服务
    if [ -f "docker-compose.yml" ]; then
        log_info "使用docker-compose启动服务..."
        docker-compose down --remove-orphans || true
        docker-compose up -d
        
        log_info "等待服务启动完成..."
        sleep 30
        
        # 检查服务状态
        docker-compose ps
    else
        log_warning "未找到docker-compose.yml文件，跳过服务启动"
    fi
}

# 设置Python环境
setup_python_env() {
    log_info "设置Python测试环境..."
    
    # 检查Python版本
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    log_info "Python版本: $python_version"
    
    # 创建虚拟环境（如果不存在）
    if [ ! -d "venv" ]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装测试依赖
    log_info "安装测试依赖..."
    pip install pytest pytest-cov pytest-asyncio pytest-mock requests websocket-client psycopg
    
    # 安装项目依赖
    if [ -f "requirements.txt" ]; then
        log_info "安装项目依赖..."
        pip install -r requirements.txt
    fi
    
    if [ -f "requirements-dev.txt" ]; then
        log_info "安装开发依赖..."
        pip install -r requirements-dev.txt
    fi
    
    log_success "Python环境设置完成"
}

# 设置环境变量
setup_env_vars() {
    log_info "设置环境变量..."
    
    export DATABASE_URL="postgresql://postgres:test_password@localhost:5432/mandas_test"
    export REDIS_URL="redis://localhost:6379"
    export DB_HOST="localhost"
    export DB_PORT="5432"
    export DB_NAME="mandas_test"
    export DB_USER="postgres"
    export DB_PASSWORD="test_password"
    
    log_success "环境变量设置完成"
}

# 运行单个测试套件
run_test_suite() {
    local test_name=$1
    local test_file=$2
    local description=$3
    
    echo ""
    echo "==== $test_name ===="
    log_info "$description"
    
    if [ -f "$test_file" ]; then
        if python -m pytest "$test_file" -v --tb=short; then
            log_success "$test_name 通过"
            return 0
        else
            log_warning "$test_name 失败或跳过"
            return 1
        fi
    else
        log_warning "测试文件不存在: $test_file"
        return 1
    fi
}

# 运行所有测试
run_all_tests() {
    log_info "开始执行测试套件..."
    
    local total_tests=0
    local passed_tests=0
    
    # 测试列表
    declare -a tests=(
        "数据库迁移测试|tests/test_database_migration.py|验证数据库结构和迁移"
        "端到端测试|tests/test_end_to_end.py|验证完整的任务执行流程"
    )
    
    # 运行每个测试套件
    for test_info in "${tests[@]}"; do
        IFS='|' read -r test_name test_file description <<< "$test_info"
        total_tests=$((total_tests + 1))
        
        if run_test_suite "$test_name" "$test_file" "$description"; then
            passed_tests=$((passed_tests + 1))
        fi
    done
    
    # 显示测试结果摘要
    echo ""
    echo "==== 测试结果摘要 ===="
    log_info "总测试套件: $total_tests"
    log_info "通过测试套件: $passed_tests"
    log_info "失败/跳过测试套件: $((total_tests - passed_tests))"
    
    if [ $passed_tests -eq $total_tests ]; then
        log_success "所有测试套件通过！"
        return 0
    else
        log_warning "部分测试套件失败或被跳过"
        return 1
    fi
}

# 清理函数
cleanup() {
    log_info "清理测试环境..."
    
    # 停止Docker服务
    if [ -f "docker-compose.yml" ]; then
        docker-compose down --remove-orphans || true
    fi
    
    # 停用虚拟环境
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate || true
    fi
    
    log_success "清理完成"
}

# 主函数
main() {
    # 设置清理陷阱
    trap cleanup EXIT
    
    log_info "开始MANDAS-2.0测试流程"
    
    # 检查Docker
    check_docker
    
    # 启动服务
    start_services
    
    # 设置Python环境
    setup_python_env
    
    # 设置环境变量
    setup_env_vars
    
    # 运行测试
    if run_all_tests; then
        log_success "🎉 所有测试完成！系统准备就绪。"
        exit 0
    else
        log_warning "⚠️  部分测试未通过，请检查日志。"
        exit 1
    fi
}

# 检查是否直接运行脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
