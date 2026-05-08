// 登录页面逻辑
if (document.getElementById('loginForm')) {
    document.getElementById('loginForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const messageEl = document.getElementById('loginMessage');
        
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await response.json();
            
            if (data.success) {
                window.location.href = '/';
            } else {
                messageEl.textContent = data.message;
                messageEl.style.color = '#e74c3c';
            }
        } catch (error) {
            messageEl.textContent = '登录失败，请重试';
            messageEl.style.color = '#e74c3c';
        }
    });
}

// 主页面逻辑
if (document.getElementById('sendBtn')) {
    const chatMessages = document.getElementById('chatMessages');
    const questionInput = document.getElementById('questionInput');
    const sendBtn = document.getElementById('sendBtn');
    
    // 发送消息
    async function sendMessage() {
        const question = questionInput.value.trim();
        if (!question) return;
        
        // 添加用户消息
        addMessage(question, 'user');
        questionInput.value = '';
        
        // 添加AI思考中
        const thinkingId = addThinkingMessage();
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            });
            const data = await response.json();
            
            // 移除思考中消息
            document.getElementById(thinkingId).remove();
            
            if (data.success) {
                addMessage(data.answer, 'ai');
            } else {
                addMessage('抱歉，发生错误: ' + data.message, 'ai');
            }
        } catch (error) {
            document.getElementById(thinkingId).remove();
            addMessage('网络错误，请重试', 'ai');
        }
    }
    
    function addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const avatar = type === 'ai' ? '🤖' : '👤';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">${content.replace(/\n/g, '<br>')}</div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function addThinkingMessage() {
        const id = 'thinking-' + Date.now();
        const messageDiv = document.createElement('div');
        messageDiv.id = id;
        messageDiv.className = 'message ai-message';
        messageDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">正在思考中...</div>
        `;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return id;
    }
    
    sendBtn.addEventListener('click', sendMessage);
    questionInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 退出登录
    document.getElementById('logoutBtn').addEventListener('click', async function() {
        await fetch('/api/logout');
        window.location.href = '/login';
    });
    
    // 文件上传
    const uploadBtn = document.getElementById('uploadBtn');
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');
    
    uploadBtn.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        uploadStatus.textContent = '上传中...';
        uploadStatus.style.color = '#667eea';
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            if (data.success) {
                uploadStatus.textContent = '✓ 上传成功！';
                uploadStatus.style.color = '#27ae60';
                // 添加到文档列表
                const docList = document.getElementById('docList');
                const li = document.createElement('li');
                li.textContent = file.name;
                docList.appendChild(li);
            } else {
                uploadStatus.textContent = '上传失败: ' + data.message;
                uploadStatus.style.color = '#e74c3c';
            }
        } catch (error) {
            uploadStatus.textContent = '上传失败，请重试';
            uploadStatus.style.color = '#e74c3c';
        }
    });
}

// 检查管理员权限（在主页面上运行）
async function checkAdminRole() {
    const adminCodesBtn = document.getElementById('adminCodesBtn');
    const adminUsersBtn = document.getElementById('adminUsersBtn');
    const userInfoSpan = document.getElementById('userInfo');
    
    if (!adminCodesBtn) return; // 不是主页面
    
    try {
        const response = await fetch('/api/user/info');
        const data = await response.json();
        if (data.success) {
            if (userInfoSpan) userInfoSpan.textContent = data.user.username;
            if (data.user.role === 'admin') {
                if (adminCodesBtn) adminCodesBtn.style.display = 'inline-block';
                if (adminUsersBtn) adminUsersBtn.style.display = 'inline-block';
                if (adminCodesBtn) {
                    adminCodesBtn.addEventListener('click', () => {
                        window.location.href = '/admin/codes';
                    });
                }
                if (adminUsersBtn) {
                    adminUsersBtn.addEventListener('click', () => {
                        window.location.href = '/admin/users';
                    });
                }
            }
        }
    } catch (error) {
        console.error('检查权限失败:', error);
    }
}

// 页面加载完成后检查管理员权限
if (document.getElementById('adminCodesBtn')) {
    checkAdminRole();
}