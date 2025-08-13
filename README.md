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
   - 复制 `.env.example` 到 `.env`
   - 在 `.env` 文件中填入您的API密钥

## 使用方法

1. 启动服务器：
```bash
cd llm-chat-web
python server.py
```

2. 访问Web界面：
   - 打开浏览器访问 `http://localhost:8000`
   - 服务器会自动打开默认浏览器

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
├── 📁 llm-api-project/     # LLM接口实现
├── 📁 llm-chat-web/        # Web服务器和前端
├── .env.example            # 环境变量示例
├── requirements.txt        # Python依赖
└── pyproject.toml         # 项目配置
```

## 开发说明

### 添加新的提供商

1. 在 `llm-api-project` 目录下创建新的提供商类
2. 实现 `LLMInterface` 接口
3. 在 `LLMManager` 中注册新的提供商

### 贡献指南

1. Fork 本仓库
2. 创建您的特性分支
3. 提交您的改动
4. 推送到分支
5. 创建新的 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件 