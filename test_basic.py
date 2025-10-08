#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
News Bot 測試腳本
測試核心功能是否正常工作
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """測試模塊導入"""
    try:
        from news_bot import create_app
        print("✓ 模塊導入成功")
        return True
    except ImportError as e:
        print(f"✗ 模塊導入失敗: {e}")
        return False

def test_app_creation():
    """測試應用創建"""
    try:
        from news_bot import create_app
        app = create_app()
        print("✓ Flask 應用創建成功")
        return True
    except Exception as e:
        print(f"✗ Flask 應用創建失敗: {e}")
        return False

def test_news_processor():
    """測試新聞處理器"""
    try:
        from container import NewsBotContainer
        container = NewsBotContainer()
        processor = container.create_news_processor()
        print("✓ NewsProcessor 實例創建成功")
        return True
    except Exception as e:
        print(f"✗ NewsProcessor 創建失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("News Bot 測試開始")
    print("=" * 40)

    tests = [
        test_imports,
        test_app_creation,
        test_news_processor,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 40)
    print(f"測試結果: {passed}/{total} 通過")

    if passed == total:
        print("🎉 所有測試通過！")
        return 0
    else:
        print("❌ 部分測試失敗")
        return 1

if __name__ == "__main__":
    sys.exit(main())