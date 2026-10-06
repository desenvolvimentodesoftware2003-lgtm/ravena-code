class LocationGlobe {
    constructor(parentId) {
        if (!parentId) throw "Missing parameters";

        const path = require("path");

        this._geodata = require(path.join(__dirname, "assets/misc/grid.json"));
        require(path.join(__dirname, "assets/vendor/encom-globe.js"));
        this.ENCOM = window.ENCOM;

        // Create DOM and include lib
        this.parent = document.getElementById(parentId);
        this.parent.innerHTML += `<div id="mod_globe">
            <div id="mod_globe_innercontainer">
                <h1>WORLD VIEW<i>GLOBAL NETWORK MAP</i></h1>
                <h2>ENDPOINT LAT/LON<i class="mod_globe_headerInfo">0.0000, 0.0000</i></h2>
                <div id="mod_globe_canvas_placeholder"></div>
                <h3 id="mod_globe_status">OFFLINE</h3>
            </div>
        </div>`;

        this.lastgeo = {};
        this.conns = [];


        setTimeout(() => {
            let container = document.getElementById("mod_globe_innercontainer");
            let placeholder = document.getElementById("mod_globe_canvas_placeholder");

            // Create Globe
            this.globe = new this.ENCOM.Globe(placeholder.offsetWidth, placeholder.offsetHeight, {
                font: window.theme.cssvars.font_main,
                data: [],
                tiles: this._geodata.tiles,
                baseColor: window.theme.globe.base || `rgb(${window.theme.r},${window.theme.g},${window.theme.b})`,
                markerColor: window.theme.globe.marker || `rgb(${window.theme.r},${window.theme.g},${window.theme.b})`,
                pinColor: window.theme.globe.pin || `rgb(${window.theme.r},${window.theme.g},${window.theme.b})`,
                satelliteColor: window.theme.globe.satellite || `rgb(${window.theme.r},${window.theme.g},${window.theme.b})`,
                scale: 1.1,
                viewAngle: 0.630,
                dayLength: 1000 * 120,
                introLinesDuration: 2000,
                introLinesColor: window.theme.globe.marker || `rgb(${window.theme.r},${window.theme.g},${window.theme.b})`,
                maxPins: 300,
                maxMarkers: 100
            });

            // Place Globe
            placeholder.remove();
            container.append(this.globe.domElement);

            // Init animations
            this._animate = () => {
                if (window.mods.globe.globe) {
                    window.mods.globe.globe.tick();
                }
                if (window.mods.globe._animate) {
                    setTimeout(() => {
                        try {
                            requestAnimationFrame(window.mods.globe._animate);
                        } catch(e) {
                            // We probably got caught in a theme change. Print it out but everything should keep running fine.
                            console.warn(e);
                        }
                    }, 1000 / 8);
                }
            };
            this.globe.init(window.theme.colors.light_black, () => {
                this._animate();
                window.audioManager.scan.play();
            });

            // resize handler
            this.resizeHandler = () => {
                let canvas = document.querySelector("div#mod_globe canvas");
                window.mods.globe.globe.camera.aspect = canvas.offsetWidth / canvas.offsetHeight;
                window.mods.globe.globe.camera.updateProjectionMatrix();
                window.mods.globe.globe.renderer.setSize(canvas.offsetWidth, canvas.offsetHeight);
            };
            window.addEventListener("resize", this.resizeHandler);

            // Connections
            this.conns = [];
            this.addConn = ip => {
                let data = null;
                try {
                    data = window.mods.netstat.geoLookup.get(ip);
                } catch {
                    // do nothing
                }
                let geo = (data && data.location) ? data.location : {};
                if (geo.latitude && geo.longitude) {
                    const lat = Number(geo.latitude);
                    const lon = Number(geo.longitude);
                    window.mods.globe.conns.push({
                        ip,
                        pin: window.mods.globe.globe.addPin(lat, lon, "", 1.2),
                    });
                }
            };
            this.removeConn = ip => {
                let index = this.conns.findIndex(x => x.ip === ip);
                this.conns[index].pin.remove();
                this.conns.splice(index, 1);
            };

            // Add random satellites
            let constellation = [];
            for(var i = 0; i< 2; i++){
                for(var j = 0; j< 3; j++){
                    constellation.push({
                        lat: 50 * i - 30 + 15 * Math.random(),
                        lon: 120 * j - 120 + 30 * i,
                        altitude: Math.random() * (1.7 - 1.3) + 1.3
                    });
                }
            }

            this.globe.addConstellation(constellation);

            // ===== RAVENA RV9: tooltip de informacoes no hover do globo =====
            // Feed de noticias do WarWatch (impacto mercado) + status de rede
            this.intelNews = [];
            this._intelFetch = () => {
                const kw = /(energy|oil|petro|gas|commodit|gold|dollar|sanction|tariff|war|missile|nuclear|naval|shipping|supply|market|stock|debt|inflation|export|import|trade|bank|rate|bond|barrel)/i;
                fetch("https://www.war-watch.com/api/articles?limit=40").then(r => r.json()).then(d => {
                    const arts = (d.articles || []).filter(a => {
                        const t = (a.title || "") + " " + (a.summary || "");
                        const srcN = (a.source || "");
                        const spamTitle = /^(Trump|clash report)[\s:]*$/i.test(a.title || "");
                        return t.length > 20 && !(srcN === "Clash Report" && spamTitle) && kw.test(t.slice(0, 400));
                    });
                    const order = {CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3};
                    arts.sort((a, b) => (order[(a.priority || "LOW").toUpperCase()] ?? 9) - (order[(b.priority || "LOW").toUpperCase()] ?? 9));
                    this.intelNews = arts.slice(0, 6);
                }).catch(() => {
                    // offline: usa cache local (escrito pelo 'intel')
                    try {
                        const { execFileSync } = require("child_process");
                        const txt = execFileSync("cat", ["/home/ravena/.ravena/cache/intel.json"],
                            {encoding: "utf8", timeout: 3000});
                        const d = JSON.parse(txt);
                        this.intelNews = (d.articles || []).slice(0, 6).map(a => ({
                            priority: a.priority, publishedAt: a.publishedAt, title: a.title
                        }));
                        this.intelCache = true;
                    } catch (e2) {}
                });
            };
            this._intelFetch();
            this._intelTimer = setInterval(this._intelFetch, 5 * 60 * 1000);

            this._intelCache = false;

            const ttip = document.createElement("div");
            ttip.id = "mod_globe_tooltip";
            ttip.style.cssText = "position:fixed;z-index:99999;display:none;background:rgba(8,10,14,0.96);color:#c8d3e0;border:1px solid #2a6cff;border-radius:4px;padding:8px 10px;font:11px/1.45 monospace;max-width:430px;max-height:340px;overflow-y:auto;pointer-events:none;box-shadow:0 0 14px rgba(42,108,255,0.35);";
            document.body.appendChild(ttip);
            this._ttip = ttip;

            const canvasEl = this.globe.domElement.querySelector("canvas") || this.globe.domElement;
            canvasEl.addEventListener("mousemove", (e) => {
                const ms = window.mods.netstat.lastPing;
                const st = window.mods.netstat.offline ? "OFFLINE" : (ms ? "ONLINE " + Math.round(ms) + "ms" : "ONLINE");
                const vpn = (window.mods.netstat.ipinfo && window.mods.netstat.ipinfo.ip) ? window.mods.netstat.ipinfo.ip : "VPN OFF";
                let html = "<b style='color:#2a6cff'>RAVENA INTEL</b><br/><span style='color:#8fe08f'>" + st + "</span> | " + vpn + "<hr style='border-color:#223'/>";
                if (this.intelNews.length) {
                    this.intelNews.forEach(n => {
                        const pr = (n.priority || "LOW").toUpperCase();
                        const col = pr === "CRITICAL" ? "#ff5a5a" : pr === "HIGH" ? "#ffb44a" : "#8fe08f";
                        const ag = this._timeAgo(n.publishedAt);
                        html += "<div style='margin:3px 0'><span style='color:" + col + "'><b>" + pr + "</b></span> <span style='color:#889'>" + ag + "</span> " + this._esc(n.title || "") + "</div>";
                    });
                } else if (window.mods.netstat && window.mods.netstat.offline) {
                    html += "<span style='color:#778'>OFFLINE - noticias indisponiveis sem rede</span>";
                } else {
                    html += "<span style='color:#889'>carregando noticias...</span>";
                }
                ttip.innerHTML = html;
                ttip.style.left = Math.min(e.clientX + 16, window.innerWidth - 450) + "px";
                ttip.style.top = Math.min(e.clientY + 16, window.innerHeight - 360) + "px";
                ttip.style.display = "block";
            });
            canvasEl.addEventListener("mouseleave", () => { ttip.style.display = "none"; });
            this._esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
            this._timeAgo = (iso) => {
                try {
                    const t = new Date(iso);
                    const s = Math.max(0, (Date.now() - t.getTime()) / 1000);
                    if (s < 3600) return Math.floor(s / 60) + "m";
                    if (s < 86400) return Math.floor(s / 3600) + "h";
                    return Math.floor(s / 86400) + "d";
                } catch (e) { return "?"; }
            };
        }, 2000);

        // Init updaters when intro animation is done
        setTimeout(() => {
            this.updateLoc();
            this.locUpdater = setInterval(() => {
                this.updateLoc();
            }, 1000);

            this.updateConns();
            this.connsUpdater = setInterval(() => {
                this.updateConns();
            }, 3000);
        }, 4000);
    }

    addRandomConnectedMarkers() {
        const randomLat = this.getRandomInRange(40, 90, 3);
        const randomLong = this.getRandomInRange(-180, 0, 3);
        this.globe.addMarker(randomLat, randomLong, '');
        this.globe.addMarker(randomLat - 20, randomLong + 150, '', true);
    }
    addTemporaryConnectedMarker(ip) {
        let data = window.mods.netstat.geoLookup.get(ip);
        let geo = (data && data.location) ? data.location : {};
        if (geo.latitude && geo.longitude) {
            const lat = Number(geo.latitude);
            const lon = Number(geo.longitude);

            window.mods.globe.conns.push({
                ip,
                pin: window.mods.globe.globe.addPin(lat, lon, "", 1.2)
            });
            let mark = window.mods.globe.globe.addMarker(lat, lon, '', true);
            setTimeout(() => {
                mark.remove();
            }, 3000);
        }
    }
    removeMarkers() {
        this.globe.markers.forEach(marker => { marker.remove(); });
        this.globe.markers = [];
    }
    removePins() {
        this.globe.pins.forEach(pin => {
            pin.remove();
        });
        this.globe.pins = [];
    }
    getRandomInRange(from, to, fixed) {
        return (Math.random() * (to - from) + from).toFixed(fixed) * 1;
    }
    updateLoc() {
        if (window.mods.netstat.offline) {
            document.querySelector("div#mod_globe").setAttribute("class", "offline");
            document.querySelector("i.mod_globe_headerInfo").innerText = "(OFFLINE)";
            document.querySelector("#mod_globe_status").innerText = "OFFLINE";

            this.removePins();
            this.removeMarkers();
            this.conns = [];
            this.lastgeo = {
                latitude: 0,
                longitude: 0
            };
        } else {
            this.updateConOnlineConnection().then(() => {
                document.querySelector("div#mod_globe").setAttribute("class", "");
                document.querySelector("#mod_globe_status").innerText = "ONLINE";
            }).catch(() => {
                document.querySelector("i.mod_globe_headerInfo").innerText = "UNKNOWN";
            })
        }
    }
    async updateConOnlineConnection() {
        // RAVENA ANONIMIZADO: se nao ha ipinfo (VPN OFF), nao exibe localizacao alguma
        if (!window.mods.netstat.ipinfo || !window.mods.netstat.ipinfo.geo) {
            document.querySelector("i.mod_globe_headerInfo").innerText = "VPN OFF";
            this.removePins();
            this.removeMarkers();
            this.conns = [];
            return;
        }
        let newgeo = window.mods.netstat.ipinfo.geo;
        if (!newgeo || !newgeo.latitude) {
            document.querySelector("i.mod_globe_headerInfo").innerText = "VPN OFF";
            return;
        }
        newgeo.latitude = Math.round(newgeo.latitude*10000)/10000;
        newgeo.longitude = Math.round(newgeo.longitude*10000)/10000;

        if (newgeo.latitude !== this.lastgeo.latitude || newgeo.longitude !== this.lastgeo.longitude) {

            document.querySelector("i.mod_globe_headerInfo").innerText = `${newgeo.latitude}, ${newgeo.longitude}`;
            this.removePins();
            this.removeMarkers();
            //this.addRandomConnectedPoints();
            this.conns = [];

            this._locPin = this.globe.addPin(newgeo.latitude, newgeo.longitude, "", 1.2);
            this._locMarker = this.globe.addMarker(newgeo.latitude, newgeo.longitude, "", false, 1.2);
        }

        this.lastgeo = newgeo;
        document.querySelector("div#mod_globe").setAttribute("class", "");
    }
    updateConns() {
        if (!window.mods.globe.globe || window.mods.netstat.offline) return false;
        window.si.networkConnections().then(conns => {
            let newconns = [];
            conns.forEach(conn => {
                let ip = conn.peeraddress;
                let state = conn.state;
                if (state === "ESTABLISHED" && ip !== "0.0.0.0" && ip !== "127.0.0.1" && ip !== "::") {
                    newconns.push(ip);
                }
            });

            this.conns.forEach(conn => {
                if (newconns.indexOf(conn.ip) !== -1) {
                    newconns.splice(newconns.indexOf(conn.ip), 1);
                } else {
                    this.removeConn(conn.ip);
                }
            });

            newconns.forEach(ip => {
                this.addConn(ip);
            });
        });
    }
}

module.exports = {
    LocationGlobe
};
