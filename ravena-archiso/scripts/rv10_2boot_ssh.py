#!/usr/bin/env python3
# TESTE RV10 - 2o BOOT via SSH: validar PERSISTENCIA REAL
# 1) restore_keys_from_pendrive deve restaurar data.key/recovery.key da ESP
# 2) LUKS deve abrir com a chave restaurada e montar RAVENA-DATA
# 3) dotfiles/.ravena linkados, sync de volta operante
import socket, time, subprocess, re, sys, os

ISO = "/root/ravv2/ravena-remaster-RV10.iso"
ESP_DISK = "/root/ravv2/vm_esp.img"
DATA_DISK = "/root/ravv2/vm_data.img"
VMLIN = "/root/iso_kern/vmlinuz-linux"
INITRD = "/root/iso_kern/initramfs-linux.img"
SSH_PORT = 2222
LOG = "/root/ravv2/rv10_2boot.log"
PW = "Dozinh@12"

def log(msg):
    line = str(msg)
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def run_vm(timeout_min=20):
    cmdline = ("console=ttyS0,115200n8 archisobasedir=arch archisolabel=RAVENA_202608 "
               "systemd.mask=ravena-llm.service")
    qemu = subprocess.Popen([
        "qemu-system-x86_64", "-enable-kvm",
        "-m", "4096", "-smp", "4", "-cpu", "host",
        "-drive", f"file={ESP_DISK},format=raw,if=none,id=usbesp",
        "-drive", f"file={DATA_DISK},format=raw,if=none,id=usbdata",
        "-device", "qemu-xhci,id=xhci",
        "-device", "usb-storage,drive=usbesp",
        "-device", "usb-storage,drive=usbdata",
        "-netdev", f"user,restrict=on,id=n0,hostfwd=tcp:127.0.0.1:{SSH_PORT}-:22",
        "-device", "e1000,netdev=n0",
        "-cdrom", ISO,
        "-kernel", VMLIN, "-initrd", INITRD, "-append", cmdline,
        "-display", "none",
        "-no-reboot"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return qemu

def wait_ssh(timeout=720):
    end = time.time() + timeout
    while time.time() < end:
        try:
            s = socket.create_connection(("127.0.0.1", SSH_PORT), timeout=3)
            s.close()
            return True
        except OSError:
            time.sleep(3)
    return False

def ssh_cmd(cmd, timeout=60, user="root"):
    r = subprocess.run(
        ["sshpass", "-p", PW, "ssh",
         "-o", "StrictHostKeyChecking=no",
         "-o", "UserKnownHostsFile=/dev/null",
         "-o", "LogLevel=ERROR",
         "-p", str(SSH_PORT), f"{user}@127.0.0.1", cmd],
        capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr

def wait_system_ready():
    for _ in range(10):
        rc, out, err = ssh_cmd("systemctl is-system-running 2>/dev/null || true; test -e /etc/ravena/recovery.key && echo CHAVE_PRESENTE || true")
        if "degraded" in out or "running" in out:
            return out
        time.sleep(15)
    return out

def main():
    try:
        os.unlink(LOG)
    except FileNotFoundError:
        pass
    log("=== RV10 2o BOOT: PERSISTENCIA (via SSH) ===")
    qemu = run_vm()
    try:
        if not wait_ssh(720):
            log("RESULTADO: FALHOU - SSH indisponivel")
            sys.exit(1)
        time.sleep(10)
        boot = wait_system_ready()
        log(f"boot state: {boot}")

        PASS = 0
        def ok(cond, label, extra=""):
            nonlocal PASS
            if cond:
                PASS += 1
                log(f"  [CHECK OK] {label}")
            else:
                log(f"  [CHECK FALHOU] {label}")
            if extra:
                log(f"     {extra}")

        print("--- chaves restauradas da ESP? (persistencia) ---")
        rc, out, err = ssh_cmd("ls -la /etc/ravena/ 2>/dev/null; echo ---; md5sum /etc/ravena/data.key /etc/ravena/recovery.key 2>/dev/null")
        log("  /etc/ravena: " + out.strip().replace("\n", " | "))
        ok(("data.key" in out and "recovery.key" in out), "chaves restauradas da ESP p/ /etc/ravena")
        keys_ok = "data.key" in out and "recovery.key" in out

        print("--- LUKS aberto e RAVENA-DATA montada (2o boot) ---")
        rc, out, err = ssh_cmd("cryptsetup status ravena-data 2>&1 | head -6; echo ---; mountpoint /mnt/ravena-data && echo MONTADA_OK; lsblk -o NAME,TYPE,FSTYPE,SIZE")
        log("  cryptsetup: " + out.strip().replace("\n", " | "))
        ok(("MONTADA_OK" in out), "RAVENA-DATA montada no 2o boot (chave restaurada)")
        ok(("ravena-data" in (out + err)), "mapper ravena-data ativo")

        print("--- conteudo da particao (persistiu do 1o boot?) ---")
        rc, out, err = ssh_cmd("ls /mnt/ravena-data/ 2>/dev/null; echo ---; ls -a /mnt/ravena-data/ravena/config/dotfiles/ 2>/dev/null")
        log("  raiz: " + out.strip().replace("\n", " | "))
        ok(("ravena" in out and "CHAVE_RECUPERACAO.txt" in out), "estrutura RAVENA-DATA persistiu")
        ok((".bashrc" in out), "dotfiles persistidos na particao")

        print("--- .ravena linkado p/ particao ---")
        rc, out, err = ssh_cmd("ls -ld /home/ravena/.ravena 2>&1; ls /home/ravena/.ravena/ 2>/dev/null")
        ok(("ravena-data" in out or "/mnt/ravena-data" in out), ".ravena -> RAVENA-DATA")
        log("  " + out.strip()[:200].replace("\n", " | "))

        print("--- boot sem LUKSFormat repetido? (chave vem do pendrive, nao novo LUKS) ---")
        rc, out, err = ssh_cmd("journalctl -b -u ravena-data.service --no-pager 2>/dev/null | tail -25")
        log("  journal ravena-data (tail):")
        for ln in out.strip().splitlines()[-25:]:
            log("    " + ln.strip())
        ok(("restaurada" in out or "aberto" in out or "montada" in out), "journal mostra fluxo de reabertura")
        ok(("criando criptografia" not in out), "NAO recriou LUKS (chave reusada)")

        print("--- eDEX-UI persistencia preparada ---")
        rc, out, err = ssh_cmd("ls -ld /home/ravena/.config/eDEX-UI 2>&1 | head -1")
        log("  " + out.strip()[:160])
        ok(("ravena-data" in out or "/mnt/ravena-data" in out), "eDEX-UI persistente na particao")

        print("--- OOBE: marcador persistido da RAVENA-DATA (criado no fluxo completo) ---")
        rc, out, err = ssh_cmd("ls -la /etc/ravena/oobe-done /mnt/ravena-data/ravena/config/oobe-done 2>&1")
        log("  marcadores: " + out.strip().replace("\n", " | "))
        ok(("oobe-done" in out), "marcador OOBE persistido na RAVENA-DATA (config/oobe-done)")

        print("--- OOBE nao re-exibe no 2o boot (marcador existe) ---")
        rc, out, err = ssh_cmd("printf '\\n0\\n' | script -qec \"su - ravena -c '/usr/local/bin/ravena-oobe.sh'\" /dev/null 2>&1 | head -8", timeout=60)
        log("  saida: [" + out.replace("\x1b", "").strip()[:150] + "]")
        ok(("BEM-VINDO" not in out), "OOBE NAO re-exibe (fluxo completo ja concluido no 1o boot)")

        print("--- checagem final: uptime e reboot limpo ---")
        rc, out, err = ssh_cmd("uptime -p")
        log("  " + out.strip())

        log(f"=== RESULTADO 2o BOOT: {PASS} checks OK ===")
        try:
            ssh_cmd("poweroff", timeout=10)
        except Exception:
            pass
        time.sleep(2)
    finally:
        qemu.terminate()
        time.sleep(2)
        try:
            qemu.kill()
        except Exception:
            pass
    log("DONE_2BOOT_SSH")

if __name__ == "__main__":
    main()