"""InsightBrowser Hosting - Configuration"""

import os

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Server config
HOST = os.getenv("INSIGHTBROWSER_HOSTING_HOST", "127.0.0.1")
PORT = int(os.getenv("INSIGHTBROWSER_HOSTING_PORT", "7001"))
DEBUG = os.getenv("INSIGHTBROWSER_HOSTING_DEBUG", "0") == "1"

# Database
DATABASE = os.path.join(BASE_DIR, "data", "hosting.db")

# Registry URL (for auto-registration)
REGISTRY_URL = os.getenv("INSIGHTBROWSER_REGISTRY_URL", "http://localhost:7000")

# 对外可达的基础地址（用于生成绝对 endpoint 注册到 Registry）。
# 公网部署必须显式设置，例如 https://hosting.example.com
PUBLIC_BASE_URL = os.getenv("INSIGHTBROWSER_HOSTING_PUBLIC_URL", f"http://localhost:{PORT}")

# 本地管理端默认 owner 与 API key（用于页面路由的演示模式）
DEFAULT_OWNER = os.getenv("INSIGHTBROWSER_HOSTING_OWNER", "default")

# Asset paths
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
WECHAT_PAY = os.path.join(ASSETS_DIR, "wechat_pay.jpg")
ALIPAY = os.path.join(ASSETS_DIR, "alipay.jpg")

# Pricing plans
PLANS = {
    "free": {
        "name": "免费版",
        "price": 0,
        "price_label": "免费",
        "max_sites": 1,
        "max_calls": 100,
        "priority": False,
        "features": ["1个托管站", "100次调用/月", "基础支持"]
    },
    "standard": {
        "name": "标准版",
        "price": 199,
        "price_label": "¥199/月",
        "max_sites": 5,
        "max_calls": -1,  # unlimited
        "priority": False,
        "features": ["5个托管站", "无限调用", "优先技术支持"]
    },
    "pro": {
        "name": "专业版",
        "price": 499,
        "price_label": "¥499/月",
        "max_sites": 20,
        "max_calls": -1,
        "priority": True,
        "features": ["20个托管站", "无限调用", "优先排名", "API访问"]
    },
    "enterprise": {
        "name": "企业版",
        "price": 1999,
        "price_label": "¥1999/月",
        "max_sites": -1,
        "max_calls": -1,
        "priority": True,
        "features": ["无限托管站", "无限调用", "优先排名", "私有部署", "专属客服"]
    }
}

# Site types
SITE_TYPES = [
    {"id": "news", "name": "新闻资讯"},
    {"id": "analysis", "name": "数据分析"},
    {"id": "aggregator", "name": "信息聚合"},
    {"id": "tool", "name": "工具服务"},
    {"id": "other", "name": "其他"}
]
