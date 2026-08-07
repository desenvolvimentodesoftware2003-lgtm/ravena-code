const RavenaApp = {
    token: localStorage.getItem('ravena_token'),
    user: JSON.parse(localStorage.getItem('ravena_user') || 'null'),

    init() {
        if (document.getElementById('loginForm')) {
            this.initLogin();
        } else if (document.getElementById('chatMessages')) {
            this.initDashboard();
        }
    },

    initLogin() {
        if (this.token) {
            window.location.href = '/dashboard';
            return;
        }

        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });
    },

    async handleLogin() {
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        const errorEl = document.getElementById('errorMessage');
        const btn = document.querySelector('.btn-login');

        errorEl.style.display = 'none';
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Entrando...';

        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.error || 'Erro ao fazer login');
            }

            localStorage.setItem('ravena_token', data.token);
            localStorage.setItem('ravena_user', JSON.stringify(data.user));
            this.token = data.token;
            this.user = data.user;

            window.location.href = '/dashboard';
        } catch (err) {
            errorEl.textContent = err.message;
            errorEl.style.display = 'block';
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-right-to-bracket"></i> Entrar';
        }
    },

    initDashboard() {
        if (!this.token) {
            window.location.href = '/login';
            return;
        }

        document.getElementById('username').textContent = this.user?.username || '-';

        document.getElementById('btnLogout').addEventListener('click', () => this.logout());
        document.getElementById('btnSend').addEventListener('click', () => this.sendCommand());
        document.getElementById('commandInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendCommand();
        });
        document.getElementById('btnClearTerminal').addEventListener('click', () => this.clearTerminal());

        document.querySelectorAll('.task-item').forEach(item => {
            item.addEventListener('click', () => {
                document.querySelectorAll('.task-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                const action = item.dataset.action;
                this.executeTask(action);
            });
        });

        this.fetchStatus();
        setInterval(() => this.fetchStatus(), 5000);
        this.updateTime();
        setInterval(() => this.updateTime(), 1000);
    },

    async fetchStatus() {
        try {
            const res = await fetch('/api/status', {
                headers: { 'Authorization': `Bearer ${this.token}` }
            });

            if (res.status === 401) {
                this.logout();
                return;
            }

            const data = await res.json();
            this.updateUI(data);
        } catch (err) {
            console.error('Erro ao buscar status:', err);
        }
    },

    updateUI(data) {
        const cpu = data.cpu?.percent || 0;
        const ram = data.memory?.percent || 0;
        const disk = data.disk?.percent || 0;

        document.getElementById('cpuValue').textContent = `${cpu}%`;
        document.getElementById('cpuBar').style.width = `${cpu}%`;
        this.setBarColor('cpuBar', cpu);

        document.getElementById('ramValue').textContent = `${ram}%`;
        document.getElementById('ramBar').style.width = `${ram}%`;
        this.setBarColor('ramBar', ram);

        document.getElementById('diskValue').textContent = `${disk}%`;
        document.getElementById('diskBar').style.width = `${disk}%`;
        this.setBarColor('diskBar', disk);

        document.getElementById('termCpu').textContent = `${cpu}%`;
        document.getElementById('termRam').textContent = `${ram}%`;

        const desktop = data.desktop?.connected;
        const statusEl = document.getElementById('desktopStatus');
        if (desktop) {
            statusEl.className = 'status-badge online';
            statusEl.innerHTML = '<i class="fas fa-circle"></i> Desktop: Online';
        } else {
            statusEl.className = 'status-badge offline';
            statusEl.innerHTML = '<i class="fas fa-circle"></i> Desktop: Offline';
        }

        const netSent = this.formatBytes(data.network?.bytes_sent || 0);
        const netRecv = this.formatBytes(data.network?.bytes_recv || 0);
        document.getElementById('netStatus').textContent = `↑${netSent} ↓${netRecv}`;
        document.getElementById('termNet').textContent = `↑${netSent} ↓${netRecv}`;
    },

    setBarColor(id, value) {
        const bar = document.getElementById(id);
        bar.classList.remove('warning', 'danger');
        if (value >= 90) bar.classList.add('danger');
        else if (value >= 70) bar.classList.add('warning');
    },

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    },

    updateTime() {
        const now = new Date();
        const time = now.toLocaleTimeString('pt-BR');
        document.getElementById('footerTime').textContent = time;
    },

    async sendCommand() {
        const input = document.getElementById('commandInput');
        const command = input.value.trim();
        if (!command) return;

        this.addChatMessage(command, 'user');
        input.value = '';

        this.addTerminalLine(`$ ${command}`, 'command');

        try {
            const res = await fetch('/api/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify({ command })
            });

            const data = await res.json();

            if (data.sent) {
                this.addChatMessage('Comando enviado ao desktop. Aguarde resultado...', 'agent');
                this.addTerminalLine('Comando enviado ao desktop', 'system');
            } else {
                this.addChatMessage('Desktop offline. Comando na fila.', 'agent');
                this.addTerminalLine('Desktop offline - comando na fila', 'error');
            }
        } catch (err) {
            this.addChatMessage('Erro ao enviar comando.', 'agent');
            this.addTerminalLine(`Erro: ${err.message}`, 'error');
        }
    },

    async executeTask(action) {
        this.addTerminalLine(`$ ravena ${action}`, 'command');

        try {
            const res = await fetch('/api/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify({ command: action })
            });

            const data = await res.json();
            this.addTerminalLine(data.message || 'Tarefa iniciada', 'system');
        } catch (err) {
            this.addTerminalLine(`Erro: ${err.message}`, 'error');
        }
    },

    addChatMessage(text, type) {
        const container = document.getElementById('chatMessages');
        const div = document.createElement('div');
        div.className = `message ${type}-message`;

        const icon = type === 'agent' ? 'fa-robot' : 'fa-user';
        const now = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

        div.innerHTML = `
            <div class="message-avatar">
                <i class="fas ${icon}"></i>
            </div>
            <div class="message-content">
                <p>${this.escapeHtml(text)}</p>
                <span class="message-time">${now}</span>
            </div>
        `;

        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    },

    addTerminalLine(text, type) {
        const terminal = document.getElementById('terminal');
        const div = document.createElement('div');
        div.className = `terminal-line ${type}`;
        div.innerHTML = `<span class="terminal-prompt">$</span> ${this.escapeHtml(text)}`;
        terminal.appendChild(div);
        terminal.scrollTop = terminal.scrollHeight;
    },

    clearTerminal() {
        const terminal = document.getElementById('terminal');
        terminal.innerHTML = '<div class="terminal-line system"><span class="terminal-prompt">$</span> Terminal limpo</div>';
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    logout() {
        localStorage.removeItem('ravena_token');
        localStorage.removeItem('ravena_user');
        this.token = null;
        this.user = null;
        window.location.href = '/login';
    }
};

document.addEventListener('DOMContentLoaded', () => RavenaApp.init());
