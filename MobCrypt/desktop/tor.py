import logging
import os
import socket
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

logger = logging.getLogger("mobcrypt.tor")

SOCKS_PORT = 9050
CONTROL_PORT = 9051
TOR_EXPERT_URL = "https://archive.torproject.org/tor-package-archive/torbrowser/15.0.18/tor-expert-bundle-windows-x86_64-15.0.18.tar.gz"
TORRC_TEMPLATE = """SocksPort {socks_port}
ControlPort {control_port}
DataDirectory {data_dir}
Log notice file {log_file}
"""


class TorManager:
    def __init__(
        self,
        socks_host: str = "127.0.0.1",
        socks_port: int = SOCKS_PORT,
        control_port: int = CONTROL_PORT,
        tor_binary: str | None = None,
    ):
        self.socks_host = socks_host
        self.socks_port = socks_port
        self.control_port = control_port
        self.tor_binary = tor_binary or self._find_tor_binary()
        self.process: subprocess.Popen | None = None
        self.data_dir: Path | None = None

    def download_expert_bundle(self, dest_dir: Path | None = None) -> str | None:
        if self._find_tor_binary():
            return self._find_tor_binary()

        dest = dest_dir or (Path.home() / "AppData" / "Local" / "MobCrypt" / "tor")
        dest.mkdir(parents=True, exist_ok=True)
        tor_exe = dest / "Tor" / "tor.exe"
        if tor_exe.exists():
            self.tor_binary = str(tor_exe)
            return self.tor_binary

        tgz_path = dest / "tor.tar.gz"
        logger.info("Baixando Tor Expert Bundle de %s...", TOR_EXPERT_URL)
        try:
            resp = urlopen(TOR_EXPERT_URL, timeout=120)
            with open(tgz_path, "wb") as f:
                f.write(resp.read())
            logger.info("Extraindo...")
            with tarfile.open(tgz_path, "r:gz") as tf:
                tf.extractall(dest)
            tgz_path.unlink()
            found = list(dest.rglob("tor.exe"))
            if found:
                self.tor_binary = str(found[0])
                logger.info("Tor baixado em %s", self.tor_binary)
                return self.tor_binary
        except Exception as e:
            logger.error("Falha ao baixar Tor: %s", e)
        return None

    def _find_tor_binary(self) -> str | None:
        user = Path.home()
        candidates = [
            user / "Desktop" / "Tor Browser" / "Browser" / "Tor" / "tor.exe",
            user / "Desktop" / "Tor Browser" / "Tor" / "tor.exe",
            user / "AppData" / "Local" / "Tor Browser" / "Browser" / "Tor" / "tor.exe",
            Path("C:\\Program Files\\Tor\\tor.exe"),
            Path("C:\\Program Files (x86)\\Tor\\tor.exe"),
            Path("C:\\Tor\\tor.exe"),
        ]
        for c in candidates:
            if c.exists():
                return str(c)
        try:
            which = subprocess.run("where tor.exe 2>nul", shell=True, capture_output=True, text=True)
            if which.returncode == 0 and which.stdout.strip():
                return which.stdout.strip().splitlines()[0].strip()
        except Exception:
            pass
        return None

    def is_running(self) -> bool:
        try:
            s = socket.create_connection((self.socks_host, self.socks_port), timeout=2)
            s.close()
            return True
        except (OSError, socket.error):
            return False

    def start(self) -> bool:
        if self.is_running():
            logger.info("Tor já está rodando em %s:%s", self.socks_host, self.socks_port)
            return True

        if not self.tor_binary:
            logger.error("Tor binary não encontrado. Instale Tor Browser ou Expert Bundle")
            return False

        self.data_dir = Path(tempfile.mkdtemp(prefix="mobcrypt_tor_"))
        log_file = self.data_dir / "tor.log"
        torrc = self.data_dir / "torrc"

        torrc.write_text(TORRC_TEMPLATE.format(
            socks_port=self.socks_port,
            control_port=self.control_port,
            data_dir=self.data_dir,
            log_file=log_file,
        ))

        logger.info("Iniciando Tor de %s", self.tor_binary)
        self.process = subprocess.Popen(
            [self.tor_binary, "-f", str(torrc)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        for _ in range(30):
            if self.is_running():
                logger.info("Tor iniciado com sucesso")
                return True
            time.sleep(1)

        logger.error("Timeout ao iniciar Tor")
        return False

    def stop(self) -> None:
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            logger.info("Tor parado")

    def new_identity(self) -> bool:
        try:
            s = socket.create_connection((self.socks_host, self.control_port), timeout=5)
            s.sendall(b"AUTHENTICATE\r\n")
            response = s.recv(1024)
            if b"250" not in response:
                s.close()
                return self._new_identity_via_socks()
            s.sendall(b"SIGNAL NEWNYM\r\n")
            response = s.recv(1024)
            s.close()
            if b"250" in response:
                logger.info("Nova identidade Tor solicitada (control port)")
                return True
            return False
        except (OSError, socket.error) as e:
            logger.warning("ControlPort não disponível (%s), tentando via SOCKS", e)
            return self._new_identity_via_socks()

    def _new_identity_via_socks(self) -> bool:
        try:
            s = socket.create_connection((self.socks_host, self.socks_port), timeout=5)
            s.sendall(b"AUTHENTICATE\r\nSIGNAL NEWNYM\r\n")
            s.close()
            logger.info("Nova identidade Tor solicitada (SOCKS port)")
            return True
        except (OSError, socket.error) as e:
            logger.error("Falha ao solicitar nova identidade: %s", e)
            return False

    @property
    def proxy_url(self) -> str:
        return f"socks5://{self.socks_host}:{self.socks_port}"
