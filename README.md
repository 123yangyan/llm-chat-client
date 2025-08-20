# LLM Chat Web

一个基于多种LLM提供商的聊天应用，支持硅基流动和Google的API接入。

## 功能特点

- 支持多个LLM提供商（硅基流动、Google）
- 简洁的Web界面
- 实时流式响应
- 支持多个模型选择
- 可动态切换提供商

## 安装说明

1. 克隆仓库：
```bash
git clone [your-repository-url]
cd [repository-name]
```

2. 创建并激活虚拟环境：
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
pip install -e .
```

4. 配置环境变量：
   - 在仓库根目录创建 `.env` 文件，并填入以下键值（示例）：
```env
# LLM API Keys
SILICON_API_KEY=your_silicon_key
GOOGLE_API_KEY=your_google_key

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Redis (可选)
REDIS_URL=redis://localhost:6379/0
```

## 使用方法

1. 启动服务器（仅后端 FastAPI）：
```bash
# 开发模式（推荐）
uvicorn backend.app.main:app --reload

# 或使用提供的脚本
python scripts/run_backend.py
```

2. 访问接口文档：
   - 打开浏览器访问 `http://localhost:8000/docs` (Swagger UI)

3. 启动并访问前端（可选）：
   - 若 `frontend` 目录包含前端源码，可执行 `npm install && npm run dev`，然后访问 `http://localhost:5173`
   - 如果仅需调用 API，可跳过此步骤

## API文档

### 聊天API
- 端点：`POST /api/chat`
- 请求体：
```json
{
    "messages": [
        {"role": "user", "content": "你好"}
    ],
    "model": "deepseek-ai/DeepSeek-V2.5"
}
```

### 获取模型列表
- 端点：`GET /api/models`
- 响应：可用模型列表

### 切换提供商
- 端点：`POST /api/provider/switch`
- 请求体：
```json
{
    "provider_name": "silicon"
}
```

## 配置说明

环境变量（在 `.env` 文件中配置）：
- `SILICON_API_KEY`: 硅基流动API密钥
- `GOOGLE_API_KEY`: Google API密钥
- `DEFAULT_PROVIDER`: 默认使用的提供商（可选）

## 项目结构

```
📁 项目根目录
├── backend/              # FastAPI 后端源代码
├── frontend/             # Vite + Vue3 前端（如需开发，手动解压 frontend.zip）
├── mcp_service/          # 辅助脚本与服务
├── scripts/              # 本地运行辅助脚本
├── docker-compose.yml    # 一键启动 Redis + Backend
├── requirements.txt      # Python 依赖
└── pyproject.toml        # 项目配置
```

## 开发说明

### 添加新的提供商

1. 在 `backend/app/providers/impl` 目录下创建新的 Provider 类
2. 继承 `backend.app.providers.base_interface.LLMInterface` 并实现所需方法
3. 在 `backend.app.providers.factory.ProviderFactory` 中注册新的提供商

### 贡献指南

1. Fork 本仓库
2. 创建您的特性分支
3. 提交您的改动
4. 推送到分支
5. 创建新的 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件 