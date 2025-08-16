document.addEventListener('DOMContentLoaded', async () => {
    const messagesContainer = document.getElementById('messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-btn');
    const providerSelect = document.getElementById('provider-select');
    const modelSelect = document.getElementById('model-select');
    const newChatButton = document.querySelector('.new-chat-btn');
    const historyList = document.getElementById('history-list');
    const toolButtons = document.querySelectorAll('.tool-button');
    const contextRange = document.getElementById('context-range');
    const contextValueSpan = document.getElementById('context-value');

    // 初始显示上下文轮数
    contextValueSpan.textContent = contextRange.value;

    // 当前聊天的ID
    let currentChatId = generateChatId();
    
    // 当前会话ID（用于后端上下文记忆）
    let currentSessionId = localStorage.getItem('currentSessionId') || null;

    // 生成聊天ID
    function generateChatId() {
        return 'chat_' + Date.now();
    }

    // 生成聊天标题
    function generateChatTitle(messages) {
        let title = '新的对话';
        const userMessages = messages.filter(msg => msg.role === 'user');
        
        if (userMessages.length > 0) {
            // 获取第一条用户消息
            const firstMessage = userMessages[0].content;
            
            // 如果消息很短，直接使用
            if (firstMessage.length <= 20) {
                title = firstMessage;
            } else {
                // 尝试找到第一个标点符号
                const punctuation = ['.', '。', '!', '！', '?', '？', ',', '，'];
                let firstSentence = firstMessage;
                
                for (const punct of punctuation) {
                    const index = firstMessage.indexOf(punct);
                    if (index > 0 && index < 20) {
                        firstSentence = firstMessage.slice(0, index + 1);
                        break;
                    }
                }
                
                // 如果没找到合适的标点或句子仍然太长，截取前20个字符
                if (firstSentence.length > 20) {
                    firstSentence = firstMessage.slice(0, 20) + '...';
                }
                
                title = firstSentence;
            }
        }
        
        return title;
    }

    // 保存聊天记录
    function saveChatHistory(chatId, messages, model) {
        const history = JSON.parse(localStorage.getItem('chatHistory') || '{}');
        const timestamp = Date.now();
        
        history[chatId] = {
            id: chatId,
            title: generateChatTitle(messages),
            messages: messages,
            model: model,
            sessionId: currentSessionId,
            timestamp: timestamp,
            lastUpdated: timestamp
        };

        localStorage.setItem('chatHistory', JSON.stringify(history));
        updateHistoryList();
    }

    // 删除聊天记录
    function deleteChatHistory(chatId, event) {
        // 阻止事件冒泡，避免触发聊天项的点击事件
        event.stopPropagation();
        
        if (confirm('确定要删除这个对话吗？')) {
            const history = JSON.parse(localStorage.getItem('chatHistory') || '{}');
            
            // 删除聊天记录
            delete history[chatId];
            localStorage.setItem('chatHistory', JSON.stringify(history));
            
            // 如果删除的是当前聊天，创建新的聊天
            if (chatId === currentChatId) {
                currentChatId = generateChatId();
                messagesContainer.innerHTML = `
                    <div class="message assistant">
                        <div class="message-content">
                            <p>你好！我是AI助手。我可以：</p>
                            <ul>
                                <li>回答你的问题和提供帮助</li>
                                <li>协助你完成各种任务</li>
                                <li>提供创意和建议</li>
                            </ul>
                            <p>请先选择模型，然后告诉我你需要什么帮助？</p>
                        </div>
                    </div>
                `;
            }
            
            // 更新历史记录列表
            updateHistoryList();
        }
    }

    // 加载聊天记录
    function loadChatHistory(chatId) {
        const history = JSON.parse(localStorage.getItem('chatHistory') || '{}');
        const chat = history[chatId];
        if (chat) {
            // 更新当前聊天ID
            currentChatId = chatId;
            // 恢复 sessionId 以继续上下文
            currentSessionId = chat.sessionId || null;
            if (currentSessionId) {
                localStorage.setItem('currentSessionId', currentSessionId);
            } else {
                localStorage.removeItem('currentSessionId');
            }
            
            // 设置模型
            if (chat.model) {
                modelSelect.value = chat.model;
            }

            // 清空并重新显示消息
            messagesContainer.innerHTML = '';
            chat.messages.forEach(msg => {
                appendMessage(msg.role, msg.content);
            });

            // 更新最后访问时间
            chat.lastUpdated = Date.now();
            localStorage.setItem('chatHistory', JSON.stringify(history));
            updateHistoryList();
        }
    }

    // 更新历史记录列表
    function updateHistoryList() {
        const history = JSON.parse(localStorage.getItem('chatHistory') || '{}');
        historyList.innerHTML = '';

        // 按最后更新时间排序
        const sortedHistory = Object.values(history).sort((a, b) => b.lastUpdated - a.lastUpdated);

        sortedHistory.forEach(chat => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            if (chat.id === currentChatId) {
                historyItem.classList.add('active');
            }
            
            historyItem.innerHTML = `
                <div class="history-item-header">
                    <div class="history-item-title">${chat.title}</div>
                    <button class="history-item-delete" title="删除对话">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"></path>
                        </svg>
                    </button>
                </div>
                <div class="history-item-info">
                    <div class="history-item-model" title="${chat.model}">${getModelDisplayName(chat.model)}</div>
                    <div class="history-item-time">${formatTime(chat.timestamp)}</div>
                </div>
            `;

            // 添加点击事件
            historyItem.addEventListener('click', () => {
                loadChatHistory(chat.id);
                document.querySelectorAll('.history-item').forEach(item => item.classList.remove('active'));
                historyItem.classList.add('active');
            });

            // 添加删除按钮事件
            const deleteButton = historyItem.querySelector('.history-item-delete');
            deleteButton.addEventListener('click', (e) => deleteChatHistory(chat.id, e));

            historyList.appendChild(historyItem);
        });
    }

    // 格式化时间
    function formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }

    // 获取当前聊天的所有消息
    function getCurrentMessages() {
        const messages = [];
        document.querySelectorAll('.message').forEach(messageDiv => {
            const role = messageDiv.classList.contains('assistant') ? 'assistant' : 'user';
            const content = messageDiv.querySelector('.message-content').textContent;
            messages.push({ role, content });
        });
        return messages;
    }

    // 获取模型的显示名称
    function getModelDisplayName(modelId) {
        // 从完整路径中提取模型名称
        const parts = modelId.split('/');
        const name = parts[parts.length - 1]
            .replace('-Instruct', '')  // 移除一些常见的后缀
            .replace('-Chat', '')
            .replace('-Base', '');
        
        // 如果名称太长，截断显示
        if (name.length > 15) {
            return name.slice(0, 12) + '...';
        }
        return name;
    }

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
            modelSelect.innerHTML = '<option value="">正在加载模型列表...</option>';
            modelSelect.disabled = true;

            const response = await fetch('/api/models');
            if (!response.ok) {
                throw new Error('获取模型列表失败');
            }
            const data = await response.json();
            console.log('获取到的模型数据:', data);
            
            // 清空现有选项
            modelSelect.innerHTML = '<option value="">请选择模型...</option>';
            
            // 获取并过滤模型（排除Pro模型）
            const models = data.models || {};
            const filteredModels = Object.entries(models)
                .filter(([name, id]) => {
                    // 排除包含 "Pro" 或 "pro" 的模型
                    return !id.includes('Pro/') && 
                           !id.toLowerCase().includes('/pro/') && 
                           !id.toLowerCase().includes('pro-');
                })
                .sort((a, b) => a[0].localeCompare(b[0]));

            // 添加所有模型选项
            filteredModels.forEach(([displayName, modelId]) => {
                const option = document.createElement('option');
                option.value = modelId;
                option.textContent = displayName;
                modelSelect.appendChild(option);
            });

            // 如果没有模型，显示提示
            if (filteredModels.length === 0) {
                modelSelect.innerHTML = '<option value="">暂无可用模型</option>';
                appendMessage('assistant', '⚠️ 未找到可用模型，请检查API密钥是否正确设置');
            } else {
                console.log(`加载了 ${filteredModels.length} 个免费模型`);
            }

        } catch (error) {
            console.error('加载模型列表失败:', error);
            modelSelect.innerHTML = '<option value="">加载失败，请刷新重试</option>';
            appendMessage('assistant', `⚠️ 加载模型列表失败: ${error.message}`);
        } finally {
            modelSelect.disabled = false;
        }
    }

    // 自动调整文本框高度
    function adjustTextareaHeight() {
        userInput.style.height = 'auto';
        userInput.style.height = userInput.scrollHeight + 'px';
    }

    userInput.addEventListener('input', adjustTextareaHeight);

    // 导出聊天记录
    async function exportChat(format) {
        try {
            // 获取所有消息
            const messages = [];
            document.querySelectorAll('.message').forEach(messageDiv => {
                const role = messageDiv.classList.contains('assistant') ? 'AI' : '我';
                const content = messageDiv.querySelector('.message-content').textContent;
                messages.push({ role, content });
            });

            if (messages.length === 0) {
                alert('没有可导出的内容');
                return;
            }

            // 创建文档标题（使用当前时间）
            const now = new Date();
            const title = `聊天记录_${now.getFullYear()}${(now.getMonth() + 1).toString().padStart(2, '0')}${now.getDate().toString().padStart(2, '0')}_${now.getHours().toString().padStart(2, '0')}${now.getMinutes().toString().padStart(2, '0')}${now.getSeconds().toString().padStart(2, '0')}`;

            // 发送导出请求
            const response = await fetch('/api/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    messages: messages,
                    format: format,
                    title: title
                })
            });

            if (!response.ok) {
                throw new Error('导出失败');
            }

            // 获取blob数据
            const blob = await response.blob();
            
            // 创建下载链接
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${title}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

        } catch (error) {
            console.error('导出失败:', error);
            alert('导出失败: ' + error.message);
        }
    }

    // 添加导出按钮事件监听
    document.querySelectorAll('.menu-item').forEach(button => {
        button.addEventListener('click', (e) => {
            const action = e.currentTarget.dataset.action;
            if (action === 'export-word') {
                exportChat('word');
            } else if (action === 'export-pdf') {
                exportChat('pdf');
            }
        });
    });

    // 工具按钮点击事件
    toolButtons.forEach(button => {
        button.addEventListener('click', () => {
            const buttonText = button.textContent.trim();
            switch(buttonText) {
                case '图片':
                    alert('图片上传功能即将推出');
                    break;
                case '视频':
                    alert('视频功能即将推出');
                    break;
                case '更多选项':
                    alert('更多选项即将推出');
                    break;
            }
        });
    });

    // Enter发送消息，Shift+Enter换行
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 同步滑块显示
    const updateContextDisplay = () => {
        contextValueSpan.textContent = contextRange.value;
    };
    contextRange.addEventListener('input', updateContextDisplay);
    contextRange.addEventListener('change', updateContextDisplay);
    // 初始化调用一次
    updateContextDisplay();

    // 添加消息到界面
    function appendMessage(role, content) {
        // 如果是第一条消息，处理欢迎消息
        if (messagesContainer.children.length === 1 && messagesContainer.querySelector('.welcome-container')) {
            const welcomeContainer = messagesContainer.querySelector('.welcome-container');
            welcomeContainer.classList.add('collapsed');
            messagesContainer.classList.add('has-messages');
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role} fade-in`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (typeof content === 'string') {
            // 处理markdown格式
            contentDiv.innerHTML = marked.parse(content);
        } else {
            contentDiv.appendChild(content);
        }
        
        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // 发送消息
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // 检查是否选择了模型
        if (!modelSelect.value) {
            appendMessage('assistant', '⚠️ 请先选择一个模型');
            return;
        }

        // 清空输入框并重置高度
        userInput.value = '';
        userInput.style.height = 'auto';

        // 添加用户消息
        appendMessage('user', message);

        try {
            // 显示加载状态
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message assistant loading';
            loadingDiv.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
            messagesContainer.appendChild(loadingDiv);

            // 创建消息元素
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message assistant fade-in typing';
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            messageDiv.appendChild(contentDiv);

            const contextWindow = parseInt(contextRange.value, 10);

            // 发送请求到后端
            const payload = {
                session_id: currentSessionId,
                user_message: message,
                context_window: contextWindow,
                model: modelSelect.value
            };

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            // 移除加载状态
            messagesContainer.removeChild(loadingDiv);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '请求失败');
            }

            const data = await response.json();
            
            // 更新 session_id（首轮由后端生成）
            if (!currentSessionId && data.session_id) {
                currentSessionId = data.session_id;
                localStorage.setItem('currentSessionId', currentSessionId);
            }

            // 添加消息元素到界面
            messagesContainer.appendChild(messageDiv);
            
            // 流式输出文本
            await streamText(data.response, contentDiv);

            // 保存聊天记录
            saveChatHistory(currentChatId, getCurrentMessages(), modelSelect.value);

        } catch (error) {
            console.error('发送消息失败:', error);
            appendMessage('assistant', `⚠️ 发送消息失败: ${error.message}`);
        }
    }

    // 流式输出文本
    async function streamText(text, contentDiv, delay = 20) {
        let currentText = '';
        const words = text.split(/(?<=[\s\.,，。！？!?])/); // 按空格和标点符号分割

        for (const word of words) {
            currentText += word;
            contentDiv.innerHTML = marked.parse(currentText);
            
            // 如果是标点符号，稍微延长停顿
            const pauseTime = /[，。！？,.!?]/.test(word) ? delay * 3 : delay;
            await new Promise(resolve => setTimeout(resolve, pauseTime));
        }

        // 输出完成后移除打字机效果
        contentDiv.parentElement.classList.remove('typing');
    }

    // 事件监听器
    sendButton.addEventListener('click', sendMessage);
    providerSelect.addEventListener('change', handleProviderChange);
    
    // 新建聊天按钮事件
    newChatButton.addEventListener('click', () => {
        // 保存当前聊天
        if (messagesContainer.children.length > 0) {
            saveChatHistory(currentChatId, getCurrentMessages(), modelSelect.value);
        }

        // 创建新的聊天
        currentChatId = generateChatId();
        messagesContainer.innerHTML = `
            <div class="message assistant welcome-message">
                <div class="message-content">
                    <p>你好主人，妲己已准备就绪！</p>
                </div>
            </div>
        `;
        messagesContainer.classList.remove('has-messages');

        // 更新历史记录列表
        updateHistoryList();

        // 当点击新建聊天时，重置 sessionId
        currentSessionId = null;
        localStorage.removeItem('currentSessionId');
    });

    /**
     * 切换LLM供应商并刷新模型列表
     */
    async function switchProvider(provider) {
        try {
            // 显示加载状态
            modelSelect.innerHTML = '<option value="">加载中...</option>';
            modelSelect.disabled = true;

            const resp = await fetch('/api/provider/switch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ provider_name: provider })
            });

            if (!resp.ok) {
                const errData = await resp.json();
                throw new Error(errData.detail || '切换供应商失败');
            }

            const data = await resp.json();
            const models = data.models || {};

            // 渲染模型下拉框
            modelSelect.innerHTML = '<option value="">请选择模型...</option>';
            Object.entries(models).forEach(([displayName, modelId]) => {
                const opt = document.createElement('option');
                opt.value = modelId;
                opt.textContent = displayName;
                modelSelect.appendChild(opt);
            });

            // 根据供应商设置首选默认模型
            let preferredModelId = null;
            if (provider === 'google') {
                preferredModelId = 'gemini-2.5-flash';
            } else if (provider === 'silicon') {
                preferredModelId = 'Qwen/Qwen3-32B';
            } else if (provider === 'wisdom_gate') {
                preferredModelId = 'gemini-2.5-flash';
            }

            if (preferredModelId) {
                // 如果列表中存在首选模型，则选中
                const found = Array.from(modelSelect.options).find(opt => opt.value === preferredModelId);
                if (found) {
                    modelSelect.value = preferredModelId;
                } else {
                    // 若找不到，保持“请选择模型...”
                    modelSelect.selectedIndex = 0;
                }
            }

            if (Object.keys(models).length === 0) {
                modelSelect.innerHTML = '<option value="">暂无可用模型</option>';
                appendMessage('assistant', '⚠️ 未找到可用模型，请检查API密钥是否正确设置');
            }

            console.log(`切换到供应商 ${provider}，加载 ${Object.keys(models).length} 个模型`);

        } catch (error) {
            console.error('切换供应商失败:', error);
            appendMessage('assistant', `⚠️ 切换供应商失败: ${error.message}`);
        } finally {
            modelSelect.disabled = false;
        }
    }

    // 处理供应商变更事件
    async function handleProviderChange() {
        const provider = providerSelect.value;
        await switchProvider(provider);
    }

    // 初始化
    async function initialize() {
        if (await checkAPIServer()) {
            await switchProvider(providerSelect.value);
        }
        // 设置初始欢迎消息
        if (messagesContainer.children.length === 0) {
            messagesContainer.innerHTML = `
                <div class="message assistant welcome-message">
                    <div class="message-content">
                        <p>你好主人，妲己已准备就绪！</p>
                    </div>
                </div>
            `;
        }
        // 加载历史记录列表
        updateHistoryList();
    }

    initialize();
}); 