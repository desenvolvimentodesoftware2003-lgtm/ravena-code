class NetManager {
    constructor() {
        const path = require("path");
        const fs = require("fs");
        const { exec } = require("child_process");
        const remote = require("@electron/remote");

        this.fs = fs;
        this.path = path;
        this.exec = exec;
        this.stateFile = path.join(remote.app.getPath("userData"), "netmanager.json");

        let state = {};
        try {
            state = JSON.parse(fs.readFileSync(this.stateFile, "utf8"));
        } catch (e) {}

        // x,y = posicao do FAB em % da viewport. Default: canto esquerdo, acima da IA
        this.state = Object.assign({ x: 88, y: 62, open: false }, state);

        this._drag = null;
        this._moved = false;
        this._scanning = false;
        this._networks = [];
        this._pendingSsid = null;
        this._buildDom();
        this._applyPos();
        if (this.state.open) this._openPanel();
        this._refreshStatus();
        this._timer = setInterval(() => {
            if (this.state.open) this._refreshStatus();
        }, 10000);
    }

    _buildDom() {
        const fab = document.createElement("div");
        fab.id = "net_fab";
        fab.innerHTML = '<span>NET</span><span class="net_pulse"></span>';

        const wrap = document.createElement("div");
        wrap.id = "net_floating";
        wrap.className = "dragging";
        wrap.appendChild(fab);
        document.body.appendChild(wrap);

        const panel = document.createElement("div");
        panel.id = "net_panel";
        panel.style.display = "none";
        panel.innerHTML = `
            <div class="net_panel_header">
                <span>RAVENA&nbsp;REDE</span>
                <span class="net_status" id="net_status">...verificando</span>
                <button id="net_close">&times;</button>
            </div>
            <div id="net_current">verificando conexao...</div>
            <div class="net_list_header">
                <span>REDES WIFI DISPONIVEIS</span>
                <button id="net_scan">ESCANEAR</button>
            </div>
            <div id="net_list"></div>
            <input id="net_password" type="password" placeholder="senha da rede (Enter para conectar)" style="display:none" />
            <div id="net_log"></div>
            <div class="net_actions">
                <button id="net_wifi_toggle">WIFI: ...</button>
                <button id="net_disconnect">DESCONECTAR</button>
                <button id="net_advanced">CONFIG AVANCADA</button>
            </div>
        `;
        document.body.appendChild(panel);

        this.fab = fab;
        this.wrap = wrap;
        this.panel = panel;
        this.current = document.getElementById("net_current");
        this.status = document.getElementById("net_status");
        this.list = document.getElementById("net_list");
        this.logEl = document.getElementById("net_log");
        this.password = document.getElementById("net_password");
        this.closeBtn = document.getElementById("net_close");
        this.scanBtn = document.getElementById("net_scan");
        this.wifiToggleBtn = document.getElementById("net_wifi_toggle");
        this.disconnectBtn = document.getElementById("net_disconnect");
        this.advancedBtn = document.getElementById("net_advanced");

        this.closeBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            this._closePanel();
        });

        this.scanBtn.addEventListener("click", () => this._scan(true));

        this.password.addEventListener("keydown", (e) => {
            if (e.key === "Enter") this._connectPending();
        });

        this.disconnectBtn.addEventListener("click", () => this._disconnect());

        this.advancedBtn.addEventListener("click", () => {
            this._exec("nmtui", (err, out) => {
                this._log("nmtui fechado (use-o para IP manual / editar conexoes)");
                this._scan(true);
            });
        });

        this.wifiToggleBtn.addEventListener("click", () => this._toggleWifi());

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
        this._refreshStatus();
        this._scan(true);
    }

    _closePanel() {
        this.state.open = false;
        this.panel.style.display = "none";
        this._save();
    }

    _log(msg, cls) {
        const d = document.createElement("div");
        if (cls) d.className = cls;
        d.textContent = msg;
        this.logEl.appendChild(d);
        this.logEl.scrollTop = this.logEl.scrollHeight;
    }

    _exec(cmd, cb) {
        this.exec(cmd, { timeout: 60000, maxBuffer: 4 * 1024 * 1024 }, (err, out, errout) => {
            cb && cb(err, (out || "").trim(), (errout || "").trim());
        });
    }

    _refreshStatus() {
        // internet + conexao ativa + radio wifi
        this._exec("curl -s -o /dev/null -w '%{http_code}' --max-time 3 http://1.1.1.1", (e, code) => {
            const net = code && code.indexOf("200") === 0;
            const state = net ? "on" : "off";
            this.status.textContent = net ? "INTERNET: OK" : "SEM INTERNET";
            this.status.className = "net_status " + state;
            this.fab.querySelector(".net_pulse").className = "net_pulse " + state;
        });

        this._exec("nmcli -t -f TYPE,NAME,DEVICE connection show --active 2>/dev/null | head -5", (e, out) => {
            const conns = out.split("\n").filter(l => l.length > 0);
            if (conns.length) {
                const first = conns[0].split(":");
                const name = first[1] || "(desconhecida)";
                const dev = first[2] || "";
                this._exec("ip -4 -br addr show " + dev + " 2>/dev/null | awk '{print $3}'", (e2, ip) => {
                    this.current.innerHTML = '<span class="connected">CONECTADO</span> a <b>' + this._esc(name) + "</b>" +
                        (ip ? "<br>IP: " + this._esc(ip) : "") +
                        "<br>interfaces ativas: " + this._esc(conns.map(c => c.split(":")[2]).join(", "));
                });
            } else {
                this.current.innerHTML = '<span class="disconnected">DESCONECTADO</span><br>Nenhuma conexao ativa. Escaneie o WiFi e clique em uma rede para conectar.';
            }
        });

        this._exec("nmcli -t radio wifi", (e, out) => {
            const on = (out || "").trim() === "enabled";
            this.wifiToggleBtn.textContent = "WIFI: " + (on ? "LIGADO" : "DESLIGADO");
        });
    }

    _toggleWifi() {
        this._exec("nmcli -t radio wifi", (e, out) => {
            const isOn = (out || "").trim() === "enabled";
            const next = isOn ? "off" : "on";
            this._exec("nmcli radio wifi " + next, (e2, o2, er2) => {
                if (!e2) {
                    this._log("WiFi " + (next === "on" ? "ligado" : "desligado") + ". Escaneando...", "ok");
                    setTimeout(() => this._scan(true), 2500);
                } else {
                    this._log("falha ao " + (next === "on" ? "ligar" : "desligar") + " WiFi: " + (er2 || e2.message), "err");
                }
                this._refreshStatus();
            });
        });
    }

    _scan(force) {
        if (this._scanning) return;
        this._scanning = true;
        this.list.innerHTML = '<div class="net_msg">escaneando redes wifi... (aguarde alguns segundos)</div>';
        if (force) {
            this._exec("nmcli device wifi rescan 2>/dev/null; sleep 2", () => {
                this._doScan();
            });
        } else {
            this._doScan();
        }
    }

    _doScan() {
        this._exec("nmcli -t -f IN-USE,SSID,SIGNAL,SECURITY,BARS device wifi list 2>/dev/null", (err, out) => {
            this._scanning = false;
            const lines = (out || "").split("\n").filter(l => l.length > 0);
            this._networks = lines.map(l => {
                const p = l.split(":");
                return {
                    inUse: p[0] === "*",
                    ssid: p[1] || "(oculto)",
                    signal: parseInt(p[2], 10) || 0,
                    security: p[3] || "",
                    bars: p[4] || ""
                };
            }).filter(n => n.ssid !== "(oculto)");

            if (!this._networks.length) {
                this._noWifiFound();
                return;
            }
            this.list.innerHTML = "";
            const seen = {};
            this._networks.forEach(n => {
                if (seen[n.ssid]) return;
                seen[n.ssid] = true;
                this._renderRow(n);
            });
        });
    }

    _noWifiFound() {
        // Diagnostico: existe adaptador WiFi? radio ligado? roteador alcancavel?
        this._exec("nmcli -t -f DEVICE,TYPE,STATE device status 2>/dev/null", (err, out) => {
            const hasWifiDev = (out || "").split("\n").some(l => l.indexOf("wifi") >= 0);
            if (!hasWifiDev) {
                this.list.innerHTML = '<div class="net_msg">Nenhum adaptador WiFi foi detectado neste sistema.<br><br>Verifique:<br>1) O hardware WiFi esta presente (notebook/PC com placa WiFi)?<br>2) No PC de mesa, a antena/placa esta instalada?<br>3) O WiFi esta habilitado no BIOS do notebook?<br>4) Se nao houver WiFi, use o CABO LAN (botao CONFIG AVANCADA).<br><br>Diagnostico detalhado no terminal: <b>rede-diag</b></div>';
                this._log("Sem adaptador WiFi detectado. Rode 'rede-diag' no terminal para detalhes (driver/rfkill/BIOS).");
                return;
            }
            this._exec("nmcli -t radio wifi", (e2, radio) => {
                const radioOn = (radio || "").trim() === "enabled";
                if (!radioOn) {
                    this.list.innerHTML = '<div class="net_msg">O radio WiFi esta DESLIGADO.<br><br>Clique no botao "WIFI: DESLIGADO" abaixo para ligar e tente ESCANEAR de novo.</div>';
                    return;
                }
                this.list.innerHTML = '<div class="net_msg">Nenhuma rede WiFi encontrada no momento.<br><br>Verifique o ROTEADOR:<br>1) O roteador esta LIGADO e com a internet funcionando?<br>2) Outros aparelhos (celular, notebook) conseguem ver/conectar na rede?<br>3) Aproxime o notebook do roteador (sinal fraco)?<br>4) Clique ESCANEAR de novo em alguns segundos.</div>';
                this._log("WiFi ligado mas nenhuma rede vista. Verificar roteador / sinal.");
            });
        });
    }

    _renderRow(n) {
        const row = document.createElement("div");
        row.className = "net_row" + (n.inUse ? " current" : "");
        const sec = n.security.indexOf("WPA") >= 0 || n.security.indexOf("WEP") >= 0 ? '<span class="net_sec">senha</span>' : '<span class="net_sec">aberta</span>';
        row.innerHTML = '<span class="net_ssid">' + this._esc(n.ssid) + "</span>" +
            '<span class="net_meta">' + (n.inUse ? "CONECTADO | " : "") + "sinal " + n.signal + "%</span>" + sec;
        row.addEventListener("click", () => this._pickNetwork(n));
        this.list.appendChild(row);
    }

    _pickNetwork(n) {
        if (n.inUse) {
            this._log("Ja conectado a " + n.ssid);
            return;
        }
        this._pendingSsid = n.ssid;
        const openNet = n.security.indexOf("WPA") < 0 && n.security.indexOf("WEP") < 0;
        if (openNet) {
            this._connectPending("");
        } else {
            this.password.style.display = "block";
            this.password.placeholder = "senha da rede '" + n.ssid + "' (Enter para conectar)";
            this.password.value = "";
            this.password.focus();
            this._log("Rede " + n.ssid + " protegida. Digite a senha e Enter.");
        }
    }

    _connectPending() {
        const ssid = this._pendingSsid;
        const pass = this.password.value;
        if (!ssid) return;
        this.password.style.display = "none";
        this.password.value = "";
        this._pendingSsid = null;
        this._log("Conectando a " + ssid + "...");
        let cmd = "nmcli device wifi connect '" + ssid.replace(/'/g, "'\\''") + "'";
        if (pass) cmd += " password '" + pass.replace(/'/g, "'\\''") + "'";
        this._exec(cmd, (err, out, erout) => {
            const ok = !err && (out.indexOf("successfully") >= 0 || out.indexOf("ativado") >= 0 || out.indexOf("activated") >= 0);
            if (ok) {
                this._log("CONECTADO a " + ssid + "!", "ok");
                this._scan(false);
                this._refreshStatus();
            } else {
                this._log("falha ao conectar: " + (erout || out || err.message), "err");
            }
        });
    }

    _disconnect() {
        this._exec("nmcli -t -f NAME connection show --active 2>/dev/null", (err, out) => {
            const names = (out || "").split("\n").filter(l => l.length > 0);
            if (!names.length) {
                this._log("Nenhuma conexao ativa para desconectar.");
                return;
            }
            const list = names.map(n => "'" + n.replace(/'/g, "'\\''") + "'").join(" ");
            this._exec("nmcli connection down " + list + " 2>&1", () => {
                this._log("Desconectado. Redes WiFi continuam disponiveis para conectar.", "ok");
                this._scan(false);
                this._refreshStatus();
            });
        });
    }

    _esc(s) {
        return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    _save() {
        try {
            this.fs.writeFileSync(this.stateFile, JSON.stringify(this.state, "", 2));
        } catch (e) {
            console.warn("NetManager save:", e);
        }
    }
}

module.exports = NetManager;