#!/usr/bin/env python3
# Login no serial e verificacao do RAVENA-DATA no boot (usb_test_rv9.img)
import socket, time, os, subprocess

IMG = "/root/ravv2/usb_test_rv9.img"
VMLIN = "/root/iso_kern/vmlinuz-linux"
INITRD = "/root/iso_kern/initramfs-linux.img"
SER, MON, LOG = "/tmp/usbboot3.sock", "/tmp/usbboot3_mon.sock", "/root/ravv2/usbboot3.log"
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

def send_wait(sk, data, expect, secs=15):
    send(sk, data, 0.8)
    e = time.time() + secs
    while time.time() < e and expect not in got:
        rd(1)
    return expect in got

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

    t0 = time.time(); deadline = time.time() + 240
    rd(10)
    while time.time() < deadline:
        got = rd(10)
        if b"login:" in got: break

    # login root (senha vazia no archiso por padrao; este remaster: Dozinh@12)
    ok = send_wait(sk, "root\n", b"Password:", 10)
    if ok:
        send_wait(sk, "Dozinh@12\n", b"root@ravena", 15) or send_wait(sk, "\n", b"root@ravena", 10)
    if b"root@ravena" not in got:
        print("LOGIN FALHOU; tail:")
        print(got[-1500:].decode(errors="replace")); qemu.kill(); exit(1)
    print(f"[{time.time()-t0:.0f}s] LOGIN OK")

    # 1. pendrive / particoes
    send_wait(sk, "lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,MOUNTPOINT\n", b"sda3", 10)
    # 2. mount ravena-data
    send_wait(sk, "mount | grep -E 'ravena|sda'; echo E===FIM===\n", b"E===FIM===", 8)
    # 3. servicos
    send_wait(sk, "systemctl is-enabled ravena-data ravena-swap ravena-llm 2>&1; echo E===FIM===\n", b"E===FIM===", 8)
    # 4. conteudo da particao + swap
    send_wait(sk, "ls -la /mnt/ravena-data/ 2>&1; echo E===FIM===\n", b"E===FIM===", 8)
    send_wait(sk, "swapon --show 2>&1; echo E===FIM===\n", b"E===FIM===", 8)
    got = rd(3)
    print("===== RESULTADO =====")
    print(got.decode(errors="replace"))
    ok_data = b"RAVENA-DATA" in got and b"/mnt/ravena-data" in got
    print("VEREDITO:", "PASSOU - RAVENA-DATA montada no boot" if ok_data else "FALHOU - verificar montagem")
    open(LOG, "ab").write(b"\n===TEST-END===\n")
finally:
    try: qemu.kill()
    except: pass