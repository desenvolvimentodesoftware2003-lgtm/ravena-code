#!/usr/bin/env python3
# Boot REAL do pendrive simulado (via BIOS, sem -kernel) - testa MBR+isohybrid+boot
import socket, time, os, subprocess

IMG = "/root/ravv2/usb_test_rv9.img"
SER, MON, LOG = "/tmp/usbboot.sock", "/tmp/usbboot_mon.sock", "/tmp/usbboot.log"
for p in (SER, MON):
    try: os.unlink(p)
    except: pass

qemu = subprocess.Popen([
    "qemu-system-x86_64", "-enable-kvm",
    "-m", "4096", "-smp", "4", "-cpu", "host",
    "-drive", f"file={IMG},format=raw,if=ide",   # boot pelo MBR (nao -kernel)
    "-boot", "order=c",
    "-display", "none",
    "-serial", f"unix:{SER},server,nowait",
    "-monitor", f"unix:{MON},server,nowait",
    "-netdev", "user,id=net0",
    "-device", "e1000,netdev=net0",
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

def type_wait(data, expect, secs):
    send(sk, data, 0.4)
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

    t0 = time.time()
    deadline = time.time() + 420
    got = rd(10)
    # espera qualquer coisa do boot real
    while time.time() < deadline:
        got = rd(10)
        # mark: chegou no menu/initramfs/kernel?
        if b"ISOLINUX" in got or b"SYSLINUX" in got or b"GRUB" in got or b"initramfs" in got or b"Linux version" in got:
            print(f"[{time.time()-t0:.0f}s] BOOTLOADER/KERNEL ACIONADO")
            break
    got = rd(30)
    # tenta login
    ok_login = type_wait("\r", b"login:", 60) or type_wait("\r", b"archiso login", 60)
    # espera o prompt do archiso (root) - autologin pode dar direto no prompt
    ok_shell = type_wait("\r", b"root@archiso", 120)
    print(f"[{time.time()-t0:.0f}s] login={ok_login} shell={ok_shell}")

    # verifica ravena-data (particao montada? label?)
    if ok_shell:
        type_wait("lsblk -o NAME,SIZE,FSTYPE,LABEL; echo ===FIMLSBLK===\n", b"===FIMLSBLK===", 15)
        type_wait("systemctl is-enabled ravena-data; ls /mnt/ravena-data 2>/dev/null; echo ===FIMDATA===\n", b"===FIMDATA===", 15)
        type_wait("mount | grep ravena; echo ===FIMMOUNT===\n", b"===FIMMOUNT===", 10)

    dur = time.time() - t0
    print(f"TOTAL: {dur:.0f}s")
    print("RESULTADO:", "BOOT OK" if ok_shell else "BOOT PARCIAL" if ok_login else "BOOT FALHOU")
    open(LOG, "ab").write(b"\n===TEST-END===\n")
finally:
    try: qemu.kill()
    except: pass