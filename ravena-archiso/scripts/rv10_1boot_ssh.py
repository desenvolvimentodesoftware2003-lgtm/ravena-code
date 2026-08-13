#!/usr/bin/env python3
# TESTE RV10 - 1o BOOT via SSH (robusto)
# Objetivo: validar 1o boot = cria LUKS na RAVENA-DATA, chave de recuperacao,
# persistencia (RAVENA-DATA montada, .ravena linkado, dotfiles), dev tools,
# OOBE, hardware panel, instalador, chave na ESP.
# Usa rede user-mode qemu + sshpass (nao depende de login serial).
import socket, time, os, subprocess, re, sys

ISO = "/root/ravv2/ravena-remaster-RV10.iso"
ESP_DISK = "/root/ravv2/vm_esp.img"
DATA_DISK = "/root/ravv2/vm_data.img"
VMLIN = "/root/iso_kern/vmlinuz-linux"
INITRD = "/root/iso_kern/initramfs-linux.img"
SSH_PORT = 2222
KEYOUT = "/root/ravv2/rv10_1boot_recovery_key.txt"
LOG = "/root/ravv2/rv10_1boot.log"
PW = "Dozinh@12"

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

def wait_ssh(timeout=600):
    end = time.time() + timeout
    while time.time() < end:
        try:
            s = socket.create_connection(("127.0.0.1", SSH_PORT), timeout=3)
            s.close()
            print("  [OK] SSH disponivel (porta 2222)")
            return True
        except OSError:
            time.sleep(3)
    print("  [FALHOU] SSH nunca respondeu")
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

def main():
    print("=== RV10 1o BOOT (via SSH) ===")
    try:
        os.unlink("/root/ravv2/rv10_ssh.sock")
    except FileNotFoundError:
        pass
    qemu = run_vm()
    try:
        if not wait_ssh(720):
            print("RESULTADO: FALHOU - SSH indisponivel")
            sys.exit(1)

        PASS = 0
        def ok(cond, label):
            nonlocal PASS
            if cond:
                PASS += 1
                print(f"  [CHECK OK] {label}")
            else:
                print(f"  [CHECK FALHOU] {label}")

        # primeiros comandos podem vir antes do boot completar; aguarda o systemd
        rc, out, err = "", "", ""
        for _ in range(6):
            rc, out, err = ssh_cmd("systemctl is-system-running 2>/dev/null; echo RC=$?")
            if "RC=0" in out or "degraded" in out:
                break
            time.sleep(15)

        print("--- quem sou / uptime ---")
        rc, out, err = ssh_cmd("id; uptime -p")
        print(" [ssh root] rc=", rc, "out=", out.strip()[:200], "err=", err.strip()[:200])

        print("--- RAVENA-DATA montada? (LUKS criado no 1o boot) ---")
        rc, out, err = ssh_cmd("mountpoint /mnt/ravena-data && echo MONTADA_OK; ls /mnt/ravena-data/ 2>/dev/null")
        ok(("MONTADA_OK" in out), "RAVENA-DATA montada (LUKS criado)")
        print("   lista:", out.strip())

        print("--- chave de recuperacao no /etc ---")
        rc, out, err = ssh_cmd("test -f /etc/ravena/recovery.key && cat /etc/ravena/recovery.key")
        key = out.strip()[:40]
        print("   recovery.key:", key)

        print("--- .ravena linkado? ---")
        rc, out, err = ssh_cmd("ls -ld /home/ravena/.ravena; ls /home/ravena/.ravena/ 2>/dev/null")
        ok(("/mnt/ravena-data" in out or "ravena-data" in out), ".ravena -> RAVENA-DATA")
        print("   ", out.strip()[:200])

        print("--- RAVENA-DATA/ravena estrutura ---")
        rc, out, err = ssh_cmd("find /mnt/ravena-data/ravena -maxdepth 2 | head -20")
        print("   ", out.strip()[:300])

        print("--- dotfiles persistidos na particao ---")
        rc, out, err = ssh_cmd("ls -a /mnt/ravena-data/ravena/config/dotfiles/ 2>/dev/null; echo ---; grep -c 'oobe\\|hardware\\|instalar\\|sync-rede' /home/ravena/.bashrc 2>/dev/null")
        ok((".bashrc" in out), "dotfiles .bashrc persistido")
        print("   ", out.strip()[:200])

        print("--- dev tools ---")
        rc, out, err = ssh_cmd("for c in npm go cargo rustc rg fzf btop nvim git python3; do command -v $c >/dev/null 2>&1 && echo $c-OK; done")
        tools = re.findall(r"(\w+)-OK", out)
        ok(len(tools) >= 7, f"dev tools presentes ({len(tools)}): {' '.join(tools)}")
        print("   ", " ".join(tools))

        print("--- sem rede (offline) esperado ---")
        rc, out, err = ssh_cmd("ping -c1 -W2 1.1.1.1 >/dev/null 2>&1 && echo TEM_REDE || echo SEM_REDE_ESPERADO")
        ok(("SEM_REDE_ESPERADO" in out), "VM offline (sem internet)")

        print("--- OOBE funcional (sem rede -> tela de boas-vindas) ---")
        rc, out, err = ssh_cmd("timeout 40 su - ravena -c 'echo n | timeout 35 /usr/local/bin/ravena-oobe.sh' 2>&1 | head -18", timeout=50)
        ok(("BEM-VINDO AO RAVENA" in out), "OOBE exibe tela de boas-vindas (offline)")
        print("   ", out.strip()[:250])
        print("--- OOBE silencioso com marcador (supressao apos concluir) ---")
        rc, out, err = ssh_cmd("mkdir -p /etc/ravena && touch /etc/ravena/oobe-done; timeout 20 su - ravena -c 'timeout 18 /usr/local/bin/ravena-oobe.sh' 2>&1 | head -5", timeout=30)
        ok(("BEM-VINDO" not in out), "OOBE NAO re-exibe quando ja concluido (marcador)")
        print("   saida: [" + out.strip()[:120] + "]")

        print("--- ravena-hardware ---")
        rc, out, err = ssh_cmd("echo | su - ravena -c '/usr/local/bin/ravena-hardware.sh' 2>&1 | head -12", timeout=40)
        ok(("RAVENA HARDWARE" in out), "painel de hardware responde")
        print("   ", out.strip()[:250])

        print("--- instalador / sync-rede presentes ---")
        rc, out, err = ssh_cmd("test -x /usr/local/bin/ravena-instalar.sh && echo INSTALADOR_OK; test -x /usr/local/bin/ravena-sync-rede.sh && echo SYNC_OK")
        ok(("INSTALADOR_OK" in out and "SYNC_OK" in out), "ravena-instalar + ravena-sync-rede presentes")

        print("--- chave gravada na ESP (disco do pendrive simulado) ---")
        rc, out, err = ssh_cmd("lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS; echo ---; for d in /dev/sda1 /dev/sdb1 /dev/sdc1; do blkid $d 2>/dev/null; done")
        print("   ", out.strip()[:500])
        ok(("vfat" in out), "ESP vfat visivel (chaves serao gravadas pelo persist_keys)")

        print("--- JOURNAL COMPLETO ravena-data.service (diagnostico persist) ---")
        rc, out, err = ssh_cmd("journalctl -b -u ravena-data.service --no-pager 2>/dev/null")
        print("   journal:\n" + "\n".join("     " + ln for ln in out.strip().splitlines()[-40:]))
        ok(("gravadas na particao EFI" in out or "gravadas no pendrive" in out), "persist_keys gravou chaves na ESP")
        ok(("CHAVE DE RECUPERACAO" in out or "criando criptografia" in out), "1o boot criou LUKS e exibiu chave")

        print("--- ESP montada manual: ravena-keys la? ---")
        rc, out, err = ssh_cmd("mkdir -p /mnt/chk; for p in /dev/sda1 /dev/sdb1; do t=$(blkid -p -o value -s TYPE $p 2>/dev/null); [ \"$t\" = vfat ] && { mount -o ro $p /mnt/chk 2>/dev/null && { ls -la /mnt/chk/ravena-keys/ 2>/dev/null; umount /mnt/chk 2>/dev/null; }; }; done")
        print("   ", out.strip().replace("\n", " | ") or "(vazio)")
        ok(("data.key" in out and "recovery.key" in out), "ravena-keys/data.key + recovery.key na ESP (persistencia de chaves OK)")

        print(f"=== RESULTADO 1o BOOT: {PASS} checks OK ===")
        # desligamento amigavel
        try:
            ssh_cmd("poweroff", timeout=15)
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
    print("DONE_1BOOT_SSH")

if __name__ == "__main__":
    main()