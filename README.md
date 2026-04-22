# 睿洁扫地机器人智能客服平台

基于 FastAPI + LangChain ReAct Agent + RAG 构建的智能对话系统，面向扫地/扫拖一体机用户提供 AI 客服、知识库检索、个人使用报告生成与邮件推送等服务。

## 功能特性

- **智能对话**：用户通过自然语言与 AI 客服进行多轮对话，支持流式实时输出（SSE）
- **RAG 知识检索**：从 PDF/TXT 构建的向量知识库中检索专业使用建议、故障排查方案
- **天气适配建议**：对接第三方天气 API，根据用户所在城市环境给出机器人使用建议
- **个人使用报告**：生成指定月份的使用报告（清洁效率、耗材状态、数据对比），支持邮件自动推送
- **维修工匹配**：基于语义相似度算法，根据设备问题自动匹配最合适的维修人员
- **用户认证**：基于 itsdangerous 签名 Cookie 的登录认证与会话管理

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI, Jinja2, itsdangerous |
| Agent | LangChain (create_agent), LangGraph (middleware) |
| LLM | 通义千问 qwen3-max (ChatTongyi) |
| Embedding | DashScope text-embedding-v4 |
| 向量库 | Chroma |
| 数据库 | SQLite |
| 配置 | YAML |

## 项目结构

```
├── main.py                  # FastAPI 入口、路由、认证、流式对话
├── agent/
│   ├── react_agent.py       # ReAct Agent 编排
│   └── tools/
│       ├── agent_tools.py   # 10 个工具函数
│       └── middleware.py    # 中间件（监控、日志、动态提示词）
├── rag/
│   ├── rag_service.py       # RAG 检索 + 总结链路
│   └── vector_store.py      # Chroma 向量库管理
├── model/
│   └── factory.py           # 模型工厂（Chat + Embedding）
├── utils/
│   ├── config_handler.py    # YAML 配置加载
│   ├── prompt_loader.py     # 提示词加载
│   ├── db.py                # SQLite 数据访问
│   ├── file_handler.py      # PDF/TXT 文件解析
│   ├── path_tool.py         # 路径工具
│   ├── logger_handler.py    # 日志
│   ├── email_sender.py      # 邮件发送
│   └── semantic_Similarity_handler.py  # 语义相似度
├── config/                  # YAML 配置文件
├── prompts/                 # 提示词模板
├── templates/               # Jinja2 页面模板
├── static/                  # 静态资源
└── data/                    # 知识库数据与 SQLite 数据库
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

`config/` 目录下有以下配置文件，按需修改：

| 文件 | 说明 |
|------|------|
| `rag.yml` | 模型名称（Chat 和 Embedding） |
| `chroma.yml` | 向量库参数（集合名、持久化路径、分片大小等） |
| `prompts.yml` | 提示词文件路径映射 |
| `agent.yml` | Agent 相关配置 |
| `email.yml` | SMTP 邮件服务配置 |

### 初始化数据库

```python
from utils.db import init_db
init_db()
```

### 加载知识库

```bash
python -m rag.vector_store
```

### 启动服务

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问 `http://localhost:8000` 即可使用。

## 工具列表

| 工具名 | 用途 |
|--------|------|
| `rag_summarize` | 从向量库检索参考资料并总结回复 |
| `get_weather` | 获取指定城市实时天气 |
| `get_user_location` | 根据用户 ID 获取所在城市 |
| `get_user_id` | 获取当前登录用户 ID |
| `get_used_month` | 获取用户最近使用月份 |
| `fetch_external_data` | 检索指定用户指定月份的使用记录 |
| `fill_context_for_report` | 触发中间件切换报告提示词 |
| `get_user_email` | 获取用户邮箱地址 |
| `send_email` | 发送邮件 |
| `get_repairman_info` | 根据问题描述匹配维修工 |

## License

MIT
