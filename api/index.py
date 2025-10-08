#!/usr/bin/env python3
import sys
import os

# 添加父目錄到 Python 路徑，以便正確導入模塊
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news_bot import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)