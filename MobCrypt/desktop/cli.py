import argparse
import logging
import sys
import threading

from .browser import open_via_tor
from .delay import generate_delay, format_delay, wait
from .server import MobCryptServer
from .tor import TorManager

logger = logging.getLogger("mobcrypt")


def main():
    parser = argparse.ArgumentParser(description="MobCrypt Desktop")
    parser.add_argument("--host", default="0.0.0.0", help="IP do servidor (0.0.0.0 para todos)")
    parser.add_argument("--port", type=int, default=8765, help="Porta do servidor")
    parser.add_argument("--socks-host", default="127.0.0.1", help="Host SOCKS5 do Tor")
    parser.add_argument("--socks-port", type=int, default=9050, help="Porta SOCKS5 do Tor")
    parser.add_argument("--control-port", type=int, default=9051, help="Porta de controle do Tor")
    parser.add_argument("--delay-min", type=float, default=300.0, help="Delay mínimo em segundos")
    parser.add_argument("--delay-max", type=float, default=900.0, help="Delay máximo em segundos")
    parser.add_argument("--tor-binary", default=None, help="Caminho para o tor.exe")
    parser.add_argument("--rotate", type=float, default=0, help="Trocar identidade Tor a cada N segundos (0=desligado)")
    parser.add_argument("--rotate-min", type=float, default=120, help="Intervalo minimo de rotacao")
    parser.add_argument("--rotate-max", type=float, default=300, help="Intervalo maximo de rotacao")
    parser.add_argument("--verbose", "-v", action="store_true", help="Log detalhado")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    tor = TorManager(
        socks_host=args.socks_host,
        socks_port=args.socks_port,
        control_port=args.control_port,
        tor_binary=args.tor_binary,
    )

    if not tor.is_running():
        logger.warning("Tor nao esta rodando em %s:%s", args.socks_host, args.socks_port)
        logger.info("Tentando iniciar Tor...")
        if not tor.start():
            logger.info("Tor nao encontrado. Tentando baixar Expert Bundle...")
            path = tor.download_expert_bundle()
            if path:
                logger.info("Tor baixado. Iniciando...")
                tor.start()
            else:
                logger.error(
                    "Nao foi possivel obter Tor.\n"
                    "  Baixe o Tor Browser em: https://www.torproject.org/download/\n"
                    "  Ou configure --socks-host/--socks-port se ja tiver Tor rodando."
                )
    else:
        logger.info("Tor detectado em %s:%s", args.socks_host, args.socks_port)

    line = "=" * 50
    print(line)
    print("  MobCrypt Desktop")
    print(line)
    print()
    ip = _get_local_ip()
    print(f"  Escaneie o QR code no celular e envie POST para:")
    print(f"  http://{ip}:{args.port}/scan")
    print(f'  Body: {{"url": "https://exemplo.com/auth/qr..."}}')
    print()
    print(f"  Delay QR: {args.delay_min}s ~ {args.delay_max}s (aleatorio quebrado)")
    if args.rotate > 0:
        print(f"  Rotacao IP: a cada ~{args.rotate}s (NEWNYM periodico)")
    else:
        print(f"  Rotacao IP: desligada (use --rotate)")
    print(f"  Proxy Tor: {tor.proxy_url}")
    print(line)
    print()

    tor_ok = tor.is_running()

    def handle_scan(url: str):
        delay = generate_delay(args.delay_min, args.delay_max)
        logger.info("URL recebida: %s", url)
        logger.info("Delay gerado: %s", format_delay(delay))

        def task():
            logger.info("Aguardando %s...", format_delay(delay))
            wait(delay)
            if tor_ok:
                logger.info("Solicitando nova identidade Tor...")
                tor.new_identity()
                logger.info("Abrindo navegador via Tor...")
            else:
                logger.warning("Tor indisponivel — abrindo sem proxy")
            ok = open_via_tor(url, args.socks_host, args.socks_port, tor_available=tor_ok)
            if ok:
                logger.info("URL aberta com sucesso")
            else:
                logger.error("Falha ao abrir URL")

        threading.Thread(target=task, daemon=True).start()

    if args.rotate > 0:
        def rotate_loop():
            while True:
                interval = generate_delay(args.rotate_min, args.rotate_max)
                logger.info("Proxima troca de identidade em %s", format_delay(interval))
                wait(interval)
                logger.info("Rodando nova identidade Tor...")
                tor.new_identity()
        threading.Thread(target=rotate_loop, daemon=True).start()

    server = MobCryptServer(args.host, args.port, handle_scan)

    try:
        server.start()
    except KeyboardInterrupt:
        print()
        logger.info("Encerrando...")
        server.stop()
        tor.stop()
        sys.exit(0)


def _get_local_ip() -> str:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


if __name__ == "__main__":
    main()
