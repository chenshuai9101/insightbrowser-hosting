# InsightBrowser Hosting

> Agent 托管平台 — 让每个人都能拥有自己的 Agent 站

## 简介

InsightBrowser Hosting 是 InsightBrowser 平台的第二核心组件，对标人类互联网中的「云服务器 + 域名服务」。
它允许没有技术能力运行 Agent 站的个人和公司，将 Agent 站托管在我们的平台上。

### 核心流程

1. 提交 Agent 能力描述（无需写代码）
2. 平台自动生成 `agent.json` + 运行环境
3. 平台托管运行
4. 自动向 Registry 注册
5. 按月收费

## 技术栈

- **后端**: Python FastAPI
- **数据库**: SQLite
- **模板**: Jinja2
- **端口**: 7001

## 快速开始

```bash
# 安装依赖
pip3 install -r requirements.txt

# 启动
python3 main.py
```

访问 http://localhost:7001

## 页面路由

| 路径 | 说明 |
|------|------|
| `/` | 首页 |
| `/create` | 创建托管站 |
| `/my-sites` | 我的托管站列表 |
| `/site/{id}` | 托管站管理 |
| `/pricing` | 定价页（含收款码） |

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/sites` | 创建托管站 |
| GET | `/api/sites` | 列出我的托管站 |
| GET | `/api/site/{id}` | 查看详情 |
| PUT | `/api/site/{id}` | 编辑托管站 |
| DELETE | `/api/site/{id}` | 删除托管站 |
| GET | `/api/site/{id}/agent.json` | 获取 agent.json |
| GET | `/api/site/{id}/template` | 获取运行模板 |

## 定价

| 方案 | 价格 | 说明 |
|------|------|------|
| 免费版 | 免费 | 1个站，100次调用/月 |
| 标准版 | ¥199/月 | 5个站，无限调用 |
| 专业版 | ¥499/月 | 20个站，无限调用 + 优先排名 |
| 企业版 | ¥1999/月 | 无限站，私有部署 |

## 项目结构

```
insightbrowser-hosting/
├── main.py              # 入口文件
├── config.py            # 配置
├── models.py            # 数据库模型
├── routes/
│   ├── api.py           # API 路由
│   └── pages.py         # 页面路由
├── services/
│   └── hosting.py       # 核心业务逻辑
├── templates/           # Jinja2 模板
├── static/              # 静态文件
├── assets/              # 收款码等资源
├── scripts/             # 工具脚本
└── data/                # 数据库
```

## 许可证

InsightLabs © 2026
