document.addEventListener('DOMContentLoaded', async () => {
    const messagesContainer = document.getElementById('messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-btn');
    const modelSelect = document.getElementById('model-select');
    const newChatButton = document.querySelector('.new-chat-btn');
    const historyList = document.getElementById('history-list');

    // 检查API服务器状态
    async function checkAPIServer() {
        try {
            const response = await fetch('/api/models');
            if (!response.ok) {
                throw new Error('API服务器连接失败');
            }
            console.log('API服务器连接成功');
            return true;
        } catch (error) {
            console.error('API服务器检查失败:', error);
            appendMessage('assistant', '⚠️ 警告：无法连接到AI服务器，请确保后端服务已启动（端口8000）');
            return false;
        }
    }

    // 获取可用模型列表
    async function loadAvailableModels() {
        try {
            const response = await fetch('/api/models');
            if (!response.ok) {
                throw new Error('获取模型列表失败');
            }
            const data = await response.json();
            
            // 清空现有选项
            modelSelect.innerHTML = '';
            
            // 添加新选项
            Object.entries(data.models).forEach(([key, model]) => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                modelSelect.appendChild(option);
            });
        } catch (error) {
            console.error('加载模型列表失败:', error);
            modelSelect.innerHTML = '<option value="">无法加载模型列表</option>';
        }
    }

    // 页面加载时检查服务器并获取模型列表
    const serverAvailable = await checkAPIServer();
    if (serverAvailable) {
        await loadAvailableModels();
    }

    // 自动调整文本框高度
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = userInput.scrollHeight + 'px';
    });

    // 发送消息
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // 检查服务器状态
        if (!await checkAPIServer()) {
            appendMessage('assistant', '⚠️ 错误：AI服务器未连接，请确保后端服务已启动');
            return;
        }

        // 添加用户消息到界面
        appendMessage('user', message);
        userInput.value = '';
        userInput.style.height = 'auto';

        try {
            // 显示加载状态
            const loadingMessage = appendMessage('assistant', '正在思考...');
            
            // 调用API
            const response = await callAPI(message, modelSelect.value);
            
            // 更新助手消息
            loadingMessage.querySelector('.message-content').innerHTML = `<p>${response}</p>`;
            
        } catch (error) {
            console.error('Error:', error);
            appendMessage('assistant', `⚠️ 错误信息: ${error.message}`);
        }
    }

    // 添加消息到界面
    function appendMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${content}</p>
            </div>
        `;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return messageDiv;
    }

    // 调用API的函数
    async function callAPI(message, model) {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                messages: [{ role: 'user', content: message }],
                model: model
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('API错误详情:', errorData);
            throw new Error(`API调用失败: ${errorData.detail || response.statusText}`);
        }

        const data = await response.json();
        return data.response;
    }

    // 事件监听器
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    newChatButton.addEventListener('click', () => {
        // 清空消息
        messagesContainer.innerHTML = `
            <div class="message assistant">
                <div class="message-content">
                    <p>你好！我是AI助手。你可以：</p>
                    <ul>
                        <li>选择不同的模型进行对话</li>
                        <li>创建新的对话</li>
                        <li>查看历史对话记录</li>
                    </ul>
                </div>
            </div>
        `;
    });

    // 添加一些示例历史记录
    const exampleHistory = [
        '关于人工智能的讨论',
        '代码优化建议',
        '项目规划咨询'
    ];

    exampleHistory.forEach(title => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        historyItem.textContent = title;
        historyList.appendChild(historyItem);
    });
}); 