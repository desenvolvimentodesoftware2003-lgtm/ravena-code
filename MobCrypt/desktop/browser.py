import logging
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("mobcrypt.browser")


def _find_browser() -> str | None:
    candidates = [
        ("firefox", [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        ]),
        ("chrome", [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"~\AppData\Local\Google\Chrome\Application\chrome.exe",
        ]),
        ("msedge", [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]),
    ]

    for name, paths in candidates:
        for p in paths:
            expanded = Path(p).expanduser()
            if expanded.exists():
                return str(expanded)
        which = shutil.which(name)
        if which:
            return which

    return None


def open_via_tor(url: str, socks_host: str = "127.0.0.1", socks_port: int = 9050, tor_available: bool = True) -> bool:
    browser = _find_browser()
    if not browser:
        logger.error("Nenhum navegador encontrado")
        return False

    name = Path(browser).stem.lower()

    if tor_available:
        proxy = f"socks5://{socks_host}:{socks_port}"
        logger.info("Abrindo %s via %s com proxy %s", url, name, proxy)
        if "firefox" in name:
            cmd = [browser, "--new-tab", url, "--proxy-server", proxy]
        elif "chrome" in name or "msedge" in name or "edge" in name:
            cmd = [browser, f"--proxy-server={proxy}", "--incognito", url]
        else:
            cmd = [browser, url]
    else:
        logger.warning("Tor indisponivel — abrindo %s diretamente (sem proxy)", url)
        cmd = [browser, url]

    logger.info("Abrindo %s via %s com proxy %s", url, name, proxy)
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        logger.error("Navegador não encontrado: %s", browser)
        return False
