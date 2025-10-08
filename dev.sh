#!/bin/bash

# News Bot 開發工具腳本

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函數定義
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  News Bot 開發工具${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# 檢查虛擬環境
check_venv() {
    if [ ! -d "venv" ]; then
        print_error "虛擬環境不存在，請先運行 setup"
        exit 1
    fi
}

# 激活虛擬環境
activate_venv() {
    source venv/bin/activate
    print_success "虛擬環境已激活"
}

# 主要命令
case "$1" in
    "setup")
        print_header
        print_info "設定開發環境..."

        # 創建虛擬環境
        if [ ! -d "venv" ]; then
            python3 -m venv venv
            print_success "虛擬環境已創建"
        else
            print_info "虛擬環境已存在"
        fi

        # 激活並安裝依賴
        activate_venv
        pip install -r requirements.txt
        print_success "依賴已安裝"

        # 檢查 .env 文件
        if [ ! -f ".env" ]; then
            cp .env.example .env
            print_info ".env 文件已創建，請編輯其中的配置"
        fi

        print_success "環境設定完成！"
        ;;

    "run")
        print_header
        check_venv
        activate_venv
        print_info "啟動本地開發服務器..."
        python linebot_app.py
        ;;

    "test")
        print_header
        check_venv
        activate_venv
        print_info "運行測試..."
        python -c "from news_bot import create_app; app = create_app(); print('✓ 模塊導入測試通過')"
        print_success "測試完成"
        ;;

    "clean")
        print_header
        print_info "清理臨時文件..."
        rm -rf __pycache__
        rm -rf .pytest_cache
        rm -rf *.pyc
        find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
        print_success "清理完成"
        ;;

    "deps")
        print_header
        check_venv
        activate_venv
        print_info "檢查依賴..."
        pip list --outdated
        ;;

    "help"|*)
        print_header
        echo "使用方法: $0 <command>"
        echo ""
        echo "可用命令:"
        echo "  setup    設定開發環境（創建虛擬環境，安裝依賴）"
        echo "  run      運行本地開發服務器"
        echo "  test     運行基本測試"
        echo "  clean    清理臨時文件"
        echo "  deps     檢查依賴更新"
        echo "  help     顯示此幫助信息"
        echo ""
        echo "範例:"
        echo "  $0 setup    # 初次設定"
        echo "  $0 run      # 啟動開發服務器"
        ;;
esac