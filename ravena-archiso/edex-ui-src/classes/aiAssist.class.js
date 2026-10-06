class AIAssist {
    constructor() {
        const path = require("path");
        const fs = require("fs");
        const { exec } = require("child_process");
        const remote = require("@electron/remote");

        this.fs = fs;
        this.path = path;
        this.exec = exec;
        this.stateFile = path.join(remote.app.getPath("userData"), "aiAssist.json");

        let state = {};
        try {
            state = JSON.parse(fs.readFileSync(this.stateFile, "utf8"));
        } catch (e) {}

        // x,y = posicao do FAB em % da viewport (esquerda/topo). Default: canto direito baixo
        this.state = Object.assign({ x: 88, y: 34, open: false }, state);

        this._drag = null;
        this._buildDom();
        this._applyPos();
        if (this.state.open) this._openPanel();
        this._checkProvider();
    }

    _buildDom() {
        const fab = document.createElement("div");
        fab.id = "ai_fab";
        fab.innerHTML = '<span style="position:relative">IA</span><span class="ai_pulse"></span>';

        const wrap = document.createElement("div");
        wrap.id = "ai_floating";
        wrap.className = "dragging";
        wrap.appendChild(fab);
        document.body.appendChild(wrap);

        const panel = document.createElement("div");
        panel.id = "ai_panel";
        panel.style.display = "none";
        panel.innerHTML = `
            <div class="ai_panel_header">
                <span>RAVENA&nbsp;IA&nbsp;LOCAL</span>
                <span class="ai_status" id="ai_status">...conectando</span>
                <button id="ai_close">&times;</button>
            </div>
            <div id="ai_log"></div>
            <div class="ai_inputrow" id="ai_inputrow" style="display:flex">
                <input id="ai_input" type="text" placeholder="pergunta para o modelo local..." />
                <button id="ai_send">SEND</button>
            </div>
        `;
        document.body.appendChild(panel);

        this.fab = fab;
        this.wrap = wrap;
        this.panel = panel;
        this.log = document.getElementById("ai_log");
        this.input = document.getElementById("ai_input");
        this.status = document.getElementById("ai_status");
        this.closeBtn = document.getElementById("ai_close");
        this.sendBtn = document.getElementById("ai_send");

        this.closeBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            this._closePanel();
        });

        this.sendBtn.addEventListener("click", () => this._send());
        this.input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") this._send();
        });

        fab.addEventListener("click", (e) => {
            e.stopPropagation();
            if (this._moved) return;
            if (this.state.open) this._closePanel();
            else this._openPanel();
        });

        // Drag: pointer events cobrem mouse + touch
        fab.addEventListener("pointerdown", (e) => {
            this._moved = false;
            this._drag = {
                startX: e.clientX,
                startY: e.clientY,
                origX: this.state.x,
                origY: this.state.y
            };
            fab.setPointerCapture(e.pointerId);
        });

        fab.addEventListener("pointermove", (e) => {
            if (!this._drag) return;
            const dx = e.clientX - this._drag.startX;
            const dy = e.clientY - this._drag.startY;
            if (Math.abs(dx) > 4 || Math.abs(dy) > 4) this._moved = true;
            this.state.x = this._clampX(this._drag.origX + (dx / window.innerWidth) * 100);
            this.state.y = this._clampY(this._drag.origY + (dy / window.innerHeight) * 100);
            this._applyPos();
            if (this.state.open) this._positionPanel();
        });

        const endDrag = (e) => {
            if (!this._drag) return;
            this._drag = null;
            this._save();
        };
        fab.addEventListener("pointerup", endDrag);
        fab.addEventListener("pointercancel", endDrag);

        window.addEventListener("resize", () => this._positionPanel());
    }

    _clampX(v) { return Math.min(92, Math.max(1, v)); }
    _clampY(v) { return Math.min(88, Math.max(1, v)); }

    _applyPos() {
        this.wrap.style.left = this.state.x + "vw";
        this.wrap.style.top = this.state.y + "vh";
    }

    _positionPanel() {
        const r = this.wrap.getBoundingClientRect();
        let top = r.top - this.panel.offsetHeight - 1;
        if (top < 0) top = r.bottom + 1;
        this.panel.style.left = Math.min(r.left, window.innerWidth - this.panel.offsetWidth - 8) + "px";
        this.panel.style.top = top + "px";
    }

    _openPanel() {
        this.state.open = true;
        this.panel.style.display = "flex";
        this._positionPanel();
        if (!this.log.children.length) {
            this._append("bot", "Provedor local: llama-server (:8080).\nSe nao estiver no ar, rode no terminal:\n  llm provedor\n  ravena-ia 'sua pergunta'");
        }
        setTimeout(() => this.input.focus(), 100);
    }

    _closePanel() {
        this.state.open = false;
        this.panel.style.display = "none";
        this._save();
    }

    _append(role, text) {
        const m = document.createElement("div");
        m.className = "msg " + role;
        m.textContent = text;
        this.log.appendChild(m);
        this.log.scrollTop = this.log.scrollHeight;
    }

    _checkProvider() {
        this.exec("curl -s -o /dev/null -w '%{http_code}' --max-time 4 http://localhost:8080/health", (e, out) => {
            const on = !e && (out.trim() === "200" || out.trim().startsWith("200"));
            this.status.textContent = on ? "PROVEDOR: ONLINE" : "PROVEDOR: OFFLINE";
            this.status.className = "ai_status " + (on ? "on" : "off");
            this.fab.querySelector(".ai_pulse").className = "ai_pulse " + (on ? "on" : "off");
        });
    }

    _send() {
        const q = this.input.value.trim();
        if (!q) return;
        this.input.value = "";
        this._append("user", q);
        const willWait = this.status && this.status.textContent.indexOf("OFFLINE") >= 0;
        if (willWait) {
            this._append("bot", "Aguardando provedor (llama-server) subir...");
        } else {
            this._append("bot", "...pensando (modelo local, pode demorar)...");
        }
        const safe = q.replace(/'/g, "'\\''");
        const started = Date.now();
        const checkSlow = setInterval(() => {
            const elapsed = Math.round((Date.now() - started) / 1000);
            const last = this.log.lastElementChild;
            if (last && (last.textContent.startsWith("...pensando") || last.textContent.startsWith("Aguardando provedor"))) {
                last.textContent = "...pensando ha " + elapsed + "s (modelo 8B em CPU e lento; ate 2-5min)";
            }
        }, 15000);
        this.exec(`ravena-ia '${safe}'`, { timeout: 600000, maxBuffer: 16 * 1024 * 1024 }, (e, out, err) => {
            clearInterval(checkSlow);
            const last = this.log.lastElementChild;
            if (last && (last.textContent.startsWith("...pensando") || last.textContent.startsWith("Aguardando provedor"))) last.remove();
            const text = (out || "").trim() || (err || "").trim() || "sem resposta.";
            if (e && !out) this._append("err", "erro ao executar ravena-ia: " + (e.message || e));
            else this._append("bot", text);
            this._checkProvider();
        });
    }

    _save() {
        try {
            this.fs.writeFileSync(this.stateFile, JSON.stringify(this.state, "", 2));
        } catch (e) {
            console.warn("AIAssist save:", e);
        }
    }
}
