const RavenaWS = {
    socket: null,
    connected: false,

    connect() {
        if (this.socket) return;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${window.location.host}`;

        this.socket = io(url, {
            transports: ['websocket'],
            reconnection: true,
            reconnectionDelay: 2000,
            reconnectionAttempts: 10
        });

        this.socket.on('connect', () => {
            this.connected = true;
            console.log('[WS] Conectado ao servidor');
            this.updateConnectionStatus(true);
        });

        this.socket.on('disconnect', () => {
            this.connected = false;
            console.log('[WS] Desconectado');
            this.updateConnectionStatus(false);
        });

        this.socket.on('connect_error', (err) => {
            console.error('[WS] Erro de conexão:', err.message);
        });

        this.socket.on('message', (data) => {
            this.handleMessage(data);
        });

        this.socket.on('result', (data) => {
            this.handleResult(data);
        });

        this.socket.on('status_update', (data) => {
            this.handleStatusUpdate(data);
        });

        this.socket.on('desktop_status', (data) => {
            this.handleDesktopStatus(data);
        });
    },

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            this.connected = false;
        }
    },

    send(event, data) {
        if (this.socket && this.connected) {
            this.socket.emit(event, data);
            return true;
        }
        return false;
    },

    handleMessage(data) {
        if (RavenaApp && RavenaApp.addChatMessage) {
            RavenaApp.addChatMessage(data.text || JSON.stringify(data), 'agent');
        }
    },

    handleResult(data) {
        if (RavenaApp && RavenaApp.addTerminalLine) {
            const text = data.output || data.result || JSON.stringify(data);
            RavenaApp.addTerminalLine(text, 'result');
        }
    },

    handleStatusUpdate(data) {
        if (RavenaApp && RavenaApp.updateUI) {
            RavenaApp.updateUI(data);
        }
    },

    handleDesktopStatus(data) {
        const statusEl = document.getElementById('desktopStatus');
        if (statusEl) {
            if (data.connected) {
                statusEl.className = 'status-badge online';
                statusEl.innerHTML = '<i class="fas fa-circle"></i> Desktop: Online';
            } else {
                statusEl.className = 'status-badge offline';
                statusEl.innerHTML = '<i class="fas fa-circle"></i> Desktop: Offline';
            }
        }
    },

    updateConnectionStatus(connected) {
        const statusEl = document.getElementById('footerStatus');
        if (statusEl) {
            statusEl.textContent = connected ? 'ONLINE' : 'OFFLINE';
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('chatMessages')) {
        setTimeout(() => RavenaWS.connect(), 1000);
    }
});
