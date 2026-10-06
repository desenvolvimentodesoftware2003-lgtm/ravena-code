class Netstat {
    constructor(parentId) {
        if (!parentId) throw "Missing parameters";

        // Create DOM
        this.parent = document.getElementById(parentId);
        this.parent.innerHTML += `<div id="mod_netstat">
            <div id="mod_netstat_inner">
                <h1>NETWORK STATUS<i id="mod_netstat_iname"></i></h1>
                <div id="mod_netstat_innercontainer">
                    <div>
                        <h1>STATE</h1>
                        <h2>UNKNOWN</h2>
                    </div>
                    <div>
                        <h1>IPv4</h1>
                        <h2>--.--.--.--</h2>
                    </div>
                    <div>
                        <h1>PING</h1>
                        <h2>--ms</h2>
                    </div>
                </div>
            </div>
        </div>`;

        this.offline = false;
        this.lastconn = {finished: false}; // Prevent geoip lookup attempt until maxminddb is loaded
        this.iface = null;
        this.failedAttempts = {};
        this.lastPing = null; // RAVENA RV9: ultimo ping (tooltip globo)
        this.runsBeforeGeoIPUpdate = 0;


        // Init updaters
        this.updateInfo();
        this.infoUpdater = setInterval(() => {
            this.updateInfo();
        }, 5000);

        // Init GeoIP integrated backend
        this.geoLookup = {
            get: () => null
        };
        // FIX RAVENA RV6: religado GeoIP. Pacotes CJS (geolite2-redist 2.0.4, maxmind 4.3.2)
        // baixam o banco MaxMind para userData/geoIPcache no primeiro boot.
        try {
            let geolite2 = require("geolite2-redist");
            let maxmind = require("maxmind");
            const geoCache = require("path").join(require("@electron/remote").app.getPath("userData"), "geoIPcache");
            geolite2.downloadDbs(geoCache).then(() => {
                return geolite2.open("GeoLite2-City", p => {
                    return maxmind.open(p);
                });
            }).then(lookup => {
                this.geoLookup = lookup;
                this.lastconn.finished = true;
            }).catch(e => {
                // Sem internet no boot ou falha de download: usa fallback vazio ate ter rede.
                console.warn("GeoIP db indisponivel (sem net?): " + e.message);
            });
        } catch (e) {
            console.warn("GeoIP disabled: " + e.message);
        }
    }
    updateInfo() {
        window.si.networkInterfaces().then(async data => {
            let offline = false;

            let net = data[0];
            let netID = 0;

            if (typeof window.settings.iface === "string") {
                while (net.iface !== window.settings.iface) {
                    netID++;
                    if (data[netID]) {
                        net = data[netID];
                    } else {
                        // No detected interface has the custom iface name, fallback to automatic detection on next loop
                        window.settings.iface = false;
                        return false;
                    }
                }
            } else {
                // Find the first external, IPv4 connected networkInterface that has a MAC address set

                while (net.operstate !== "up" || net.internal === true || net.ip4 === "" || net.mac === "") {
                    netID++;
                    if (data[netID]) {
                        net = data[netID];
                    } else {
                        // No external connection!
                        this.iface = null;
                        document.getElementById("mod_netstat_iname").innerText = "Interface: (offline)";

                        this.offline = true;
                        document.querySelector("#mod_netstat_innercontainer > div:first-child > h2").innerHTML = "OFFLINE";
                        document.querySelector("#mod_netstat_innercontainer > div:nth-child(2) > h2").innerHTML = "--.--.--.--";
                        document.querySelector("#mod_netstat_innercontainer > div:nth-child(3) > h2").innerHTML = "--ms";
                        break;
                    }
                }
            }

            if (net.ip4 !== this.internalIPv4) this.runsBeforeGeoIPUpdate = 0;

            this.iface = net.iface;
            this.internalIPv4 = net.ip4;
            document.getElementById("mod_netstat_iname").innerText = "Interface: "+net.iface;

            if (net.ip4 === "127.0.0.1") {
                offline = true;
            } else {
                // RAVENA ANONIMIZADO: nunca mostra o IP real.
                // Pede ao processo principal o IP publico (via tunel wg0 se ativo).
                if (this.runsBeforeGeoIPUpdate === 0 && this.lastconn.finished) {
                    const electron = require("electron");
                    const vpnIp = electron.ipcRenderer.sendSync("rav-get-public-ip");
                    if (vpnIp && vpnIp !== "0.0.0.0" && !vpnIp.startsWith("VPN")) {
                        const _geo = this.geoLookup.get(vpnIp);
                        this.ipinfo = {
                            ip: vpnIp,
                            geo: (_geo && _geo.location) ? _geo.location : null
                        };
                        document.querySelector("#mod_netstat_innercontainer > div:nth-child(2) > h2").innerHTML = window._escapeHtml(vpnIp);
                        this.runsBeforeGeoIPUpdate = 10;
                    } else {
                        // VPN OFF ou sem tunel: exibe "VPN OFF" - IP real NUNCA aparece
                        document.querySelector("#mod_netstat_innercontainer > div:nth-child(2) > h2").innerHTML = "VPN OFF";
                        this.runsBeforeGeoIPUpdate = 10;
                    }
                } else if (this.runsBeforeGeoIPUpdate !== 0) {
                    this.runsBeforeGeoIPUpdate = this.runsBeforeGeoIPUpdate - 1;
                }

                let p = await this.pingMulti(net.ip4).catch(() => { offline = true });

                this.offline = offline;
                this.lastPing = offline ? null : p;
                if (offline) {
                    document.querySelector("#mod_netstat_innercontainer > div:first-child > h2").innerHTML = "OFFLINE";
                    document.querySelector("#mod_netstat_innercontainer > div:nth-child(2) > h2").innerHTML = "--.--.--.--";
                    document.querySelector("#mod_netstat_innercontainer > div:nth-child(3) > h2").innerHTML = "--ms";
                } else {
                    document.querySelector("#mod_netstat_innercontainer > div:first-child > h2").innerHTML = "ONLINE";
                    document.querySelector("#mod_netstat_innercontainer > div:nth-child(3) > h2").innerHTML = Math.round(p)+"ms";
                }
            }
        });
    }
    // RAVENA RV9: ping multi-alvo (443/53/80) p/ evitar falso OFFLINE
    // Muitos ISPs bloqueiam TCP na porta 80 (default antigo) - tentamos varios alvos
    pingMulti(local) {
        const targets = [
            ["1.1.1.1", 443],
            ["1.1.1.1", 53],
            ["8.8.8.8", 443],
            ["1.1.1.1", 80],
            ["8.8.8.8", 53]
        ];
        const tryNext = i => {
            if (i >= targets.length) return Promise.reject(new Error("all targets failed"));
            const [host, port] = targets[i];
            return this.ping(host, port, local).catch(() => tryNext(i + 1));
        };
        return tryNext(0);
    }
    ping(target, port, local) {
        return new Promise((resolve, reject) => {
            let s = new require("net").Socket();
            let start = process.hrtime();

            s.connect({
                port,
                host: target,
                localAddress: local,
                family: 4
            }, () => {
                let time_arr = process.hrtime(start);
                let time = (time_arr[0] * 1e9 + time_arr[1]) / 1e6;
                resolve(time);
                s.destroy();
            });
            s.on('error', e => {
                s.destroy();
                reject(e);
            });
            s.setTimeout(1900, function() {
                s.destroy();
                reject(new Error("Socket timeout"));
            });
        });
    }
}

module.exports = {
    Netstat
};
