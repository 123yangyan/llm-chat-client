# LLM Chat Client

一个支持多种大语言模型的聊天客户端，目前支持：

- 硅基流动（SiliconFlow）API
- Google Gemini API

## 特性

- 支持多个LLM提供商之间的灵活切换
- 支持流式输出
- 支持异步调用
- 完整的错误处理和重试机制
- 模块化设计，易于扩展

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/your-username/llm-chat-client.git
cd llm-chat-client
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 配置

在项目根目录创建 `.env` 文件：

```env
# 硅基流动API配置
SILICON_API_KEY=your_silicon_api_key

# Google API配置
GOOGLE_API_KEY=your_google_api_key
```

## 使用方法

1. 运行程序：
```bash
python llm_api_project/main.py
```

2. 可用命令：
- 输入'切换'：在不同API提供商之间切换
- 输入'模型'：切换当前提供商的可用模型
- 输入'退出'：结束对话
- 输入'帮助'：查看命令列表

## 支持的模型

### 硅基流动
- DeepSeek V2.5/V3
- DeepSeek R1系列
- 书生系列
- Qwen系列
- GLM系列

### Google Gemini
- Gemini 2.5 Pro
- Gemini 2.5 Flash
- Gemini 2.5 Flash-Lite
- Gemini Pro Vision

## 开发说明

项目使用模块化设计，便于扩展：

- `llm_interface.py`: 定义LLM提供商接口
- `silicon_provider.py`: 硅基流动API实现
- `google_provider.py`: Google Gemini API实现
- `main.py`: 主程序和管理器

要添加新的提供商，只需：
1. 创建新的提供商类，继承`LLMInterface`
2. 实现所有必需的方法
3. 在`LLMManager`中注册新的提供商

## 许可证

MIT License 