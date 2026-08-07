#!/usr/bin/env python3
# Boot da imagem do pendrive MODIFICADA (ISO + RAVENA-DATA p3) usando -kernel/-initrd
# (mesmo metodo dos testes rv7/rv9), deixando passar o boot completo.
import socket, time, os, subprocess

IMG = "/root/ravv2/usb_test_rv9.img"
VMLIN = "/root/iso_kern/vmlinuz-linux"
INITRD = "/root/iso_kern/initramfs-linux.img"
SER, MON, LOG = "/tmp/usbboot2.sock", "/tmp/usbboot2_mon.sock", "/root/ravv2/usbboot2.log"
for p in (SER, MON):
    try: os.unlink(p)
    except: pass

cmdline = ("console=ttyS0,115200n8 archisobasedir=arch archisolabel=RAVENA_202608 "
           "systemd.getty_autologin=root")
qemu = subprocess.Popen([
    "qemu-system-x86_64", "-enable-kvm",
    "-m", "4096", "-smp", "4", "-cpu", "host",
    "-drive", f"file={IMG},format=raw,if=ide",
    "-kernel", VMLIN, "-initrd", INITRD, "-append", cmdline,
    "-display", "none",
    "-serial", f"unix:{SER},server,nowait",
    "-monitor", f"unix:{MON},server,nowait",
    "-no-reboot"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

got = b""
def send(sk, data, delay=0.3):
    sk.sendall(data.encode())
    if delay: time.sleep(delay)

def rd(secs):
    global got
    end = time.time() + secs
    while time.time() < end:
        try:
            d = sk.recv(65536)
            if d:
                got += d
                with open(LOG, "wb") as f: f.write(got)
        except socket.timeout:
            pass
    return got

try:
    for i in range(150):
        if os.path.exists(SER): break
        time.sleep(0.2)
    sk = None
    for _ in range(100):
        try:
            sk = socket.socket(socket.AF_UNIX); sk.settimeout(0.5); sk.connect(SER); break
        except Exception:
            time.sleep(0.1)
    if not sk:
        print("FALHA: sem serial"); qemu.kill(); exit(1)

    t0 = time.time(); deadline = time.time() + 300
    rd(10)
    # fluxo: kernel -> squashfs -> prompt -> autologin root
    while time.time() < deadline:
        got = rd(10)
        if b"root@archiso" in got:
            print(f"[{time.time()-t0:.0f}s] SHELL PRONTO") 
            break
    if b"root@archiso" not in got:
        print("SHELL NÃO APARECEU; tail do log:")
        print(got[-2000:].decode(errors="replace"))
        qemu.kill(); exit(1)

    # 1. verifica pendrive e particao
    send(sk, "lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL\n", 1.5)
    rd(5)
    send(sk, "mount | grep ravena; echo E===FIM===\n", 1.0)
    rd(3)
    # 2. servico ravena-data
    send(sk, "systemctl is-enabled ravena-data ravena-swap 2>&1; echo E===FIM===\n", 1.5)
    rd(3)
    # 3. conteudo da particao
    send(sk, "ls -la /mnt/ravena-data/ 2>&1; echo E===FIM===\n", 1.0)
    rd(3)
    # 4. swap?
    send(sk, "swapon --show; echo E===FIM===\n", 1.0)
    rd(3)
    got = rd(3)
    print("===== LOG FINAL =====")
    print(got.decode(errors="replace"))
    open(LOG,"ab").write(b"\n===TEST-END===\n")
    print("RESULTADO: BOOT OK COM RAVENA-DATA" if b"/mnt/ravena-data" in got else "VERIFICAR MANUALMENTE")
finally:
    try: qemu.kill()
    except: pass