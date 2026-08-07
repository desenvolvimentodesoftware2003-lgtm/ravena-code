#!/usr/bin/env python3
"""
XiaomiFRPTool v1.0
Ferramenta nativa para remocao de FRP em dispositivos Xiaomi/Redmi
Baseada na engenharia reversa do Tenorshare 4uKey for Android v2.15.2.0

Metodos implementados:
  [1] ADB Bypass  - Remove conta Google via ADB (quando ADB esta disponivel)
  [2] Fastboot    - Apaga particoes FRP/userdata (bootloader destravado)
  [3] EDL Mode    - Usa protocolo Firehose Qualcomm (requer modo 9008)
  [4] MTK BROM    - Usa Download Agent MediaTek (requer modo BROM)
"""

import os
import sys
import json
import time
import shutil
import subprocess
import threading
from datetime import datetime
from pathlib import Path

# Modulo EDL real (Sahara + Firehose)
from edl_firehose import (
    remove_frp_edl,
    check_edl_mode,
    list_available_loaders,
    get_loader_for_soc,
    XIAOMI_LOADERS,
    EDLDevice,
)

# --- Configuracoes ------------------------------------------------------------

try:
    TOOL_DIR = Path(__file__).parent
except NameError:
    TOOL_DIR = Path(".").resolve()
LOG_FILE = TOOL_DIR / "frp_tool.log"

# Caminhos do 4uKey (se instalado)
FOURKEY_DIR = Path("C:/Program Files (x86)/4uKey for Android")
ADB_PATH = FOURKEY_DIR / "TS_Android" / "adb" / "adb.exe"
FASTBOOT_PATH = FOURKEY_DIR / "adb" / "fastboot.exe"
EDL_EXE = FOURKEY_DIR / "edl_exe" / "edl.exe"
MTK_EXE = FOURKEY_DIR / "MTKEXE" / "main.exe"
EDL_LOADERS = FOURKEY_DIR / "edl_exe" / "Loaders"
MTK_LOADERS = FOURKEY_DIR / "MTKEXE" / "My_Code" / "Loader"
MTK_PAYLOADS = FOURKEY_DIR / "MTKEXE" / "My_Code" / "payloads"

# VID/PID Xiaomi (do AndroidVID.ini / AndroidPIDWhite.ini)
XIAOMI_VID = 10007
XIAOMI_PIDS = {65344, 65352}

# --- Logging ------------------------------------------------------------------

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:12]
    line = f"{ts} [{level}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass

# --- Utilitarios --------------------------------------------------------------

def run_cmd(cmd, timeout=30, check=True):
    """Executa um comando e retorna (stdout, stderr, rc)."""
    log(f"$ {cmd}")
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        out = proc.stdout.strip()
        err = proc.stderr.strip()
        rc = proc.returncode
        if out:
            log(f"> {out[:500]}")
        if err:
            log(f"! {err[:500]}", "WARN")
        return out, err, rc
    except subprocess.TimeoutExpired:
        log(f"Comando excedeu {timeout}s", "ERROR")
        return "", "timeout", -1
    except FileNotFoundError:
        log(f"Comando nao encontrado: {cmd[0]}", "ERROR")
        return "", "not_found", -1

def check_tool(path, name):
    if not path.exists():
        log(f"{name} nao encontrado em: {path}", "WARN")
        return False
    return True

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

# --- Deteccao de dispositivos -------------------------------------------------

def get_adb_devices():
    """Retorna lista de dispositivos ADB conectados."""
    out, _, _ = run_cmd([str(ADB_PATH), "devices"], timeout=5)
    devices = []
    for line in out.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] in ("device", "recovery", "sideload"):
            devices.append(parts[0])
    return devices

def get_fastboot_devices():
    """Retorna lista de dispositivos fastboot."""
    out, _, _ = run_cmd([str(FASTBOOT_PATH), "devices"], timeout=5)
    devices = []
    for line in out.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "fastboot":
            devices.append(parts[0])
    return devices

def get_device_info_adb(serial):
    """Obtem informacoes do dispositivo via ADB."""
    info = {}
    props = [
        ("manufacturer", "ro.product.manufacturer"),
        ("model", "ro.product.model"),
        ("device", "ro.product.device"),
        ("miui_version", "ro.miui.ui.version.name"),
        ("android_version", "ro.build.version.release"),
        ("sdk", "ro.build.version.sdk"),
    ]
    for key, prop in props:
        out, _, _ = run_cmd(
            [str(ADB_PATH), "-s", serial, "shell", f"getprop {prop}"],
            timeout=5
        )
        info[key] = out.strip()
    return info

def get_device_info_fastboot(serial):
    """Obtem informacoes do dispositivo via fastboot."""
    info = {}
    out, _, _ = run_cmd(
        [str(FASTBOOT_PATH), "-s", serial, "getvar", "all"],
        timeout=5
    )
    for line in out.splitlines():
        line = line.replace("(bootloader) ", "").strip()
        if ":" in line:
            key, val = line.split(":", 1)
            info[key.strip()] = val.strip()
    return info

def detect_device():
    """Detecta o estado atual do dispositivo e retorna um dicionario."""
    device = {
        "serial": None,
        "mode": None,  # "adb", "fastboot", "edl", "mtk_brom"
        "manufacturer": None,
        "model": None,
        "product": None,
        "bootloader_unlocked": None,
        "info": {}
    }

    # Verifica ADB
    adb_devs = get_adb_devices()
    if adb_devs:
        serial = adb_devs[0]
        log(f"Dispositivo encontrado via ADB: {serial}")
        info = get_device_info_adb(serial)
        mfr = info.get("manufacturer", "").lower()
        device["serial"] = serial
        device["mode"] = "adb"
        device["manufacturer"] = info.get("manufacturer")
        device["model"] = info.get("model")
        device["info"] = info

        if "xiaomi" in mfr or "redmi" in mfr:
            log(f"Xiaomi/Redmi detectado: {info.get('model')} | MIUI: {info.get('miui_version', 'N/A')}")
        return device

    # Verifica Fastboot
    fb_devs = get_fastboot_devices()
    if fb_devs:
        serial = fb_devs[0]
        log(f"Dispositivo encontrado via Fastboot: {serial}")
        info = get_device_info_fastboot(serial)
        device["serial"] = serial
        device["mode"] = "fastboot"
        device["info"] = info
        device["product"] = info.get("product")
        device["bootloader_unlocked"] = info.get("unlocked") == "yes"
        
        log(f"Produto: {info.get('product', 'N/A')} | Bootloader: {'[OK] DESTRAVADO' if device['bootloader_unlocked'] else '[BL] TRAVADO'}")
        return device

    # Verifica EDL 9008 (Qualcomm)
    try:
        result = subprocess.run(
            'powershell "Get-PnpDevice | Where-Object { $_.FriendlyName -match \'9008|QDLoader|EDL\' } | Select-Object -ExpandProperty FriendlyName"',
            capture_output=True, text=True, shell=True, timeout=5
        )
        if result.stdout.strip():
            log(f"Modo EDL 9008 detectado via USB!")
            device["mode"] = "edl"
            return device
    except:
        pass

    # Verifica MTK BROM
    try:
        result = subprocess.run(
            'powershell "Get-PnpDevice | Where-Object { $_.FriendlyName -match \'MediaTek|MTK|BROM|DA\' } | Select-Object -ExpandProperty FriendlyName"',
            capture_output=True, text=True, shell=True, timeout=5
        )
        if result.stdout.strip():
            log(f"Modo MTK BROM detectado via USB!")
            device["mode"] = "mtk_brom"
            return device
    except:
        pass

    log("Nenhum dispositivo Xiaomi/Redmi detectado", "WARN")
    return device

# --- Estrategias ADB Bypass --------------------------------------------------

class ADBBypass:
    """Implementa as estrategias de bypass via ADB (analisadas do 4uKey)."""

    def __init__(self, serial):
        self.serial = serial
        self.adb = [str(ADB_PATH), "-s", serial]
        self.results = []

    def _adb(self, cmd, timeout=10):
        full_cmd = self.adb + cmd.split()
        return run_cmd(full_cmd, timeout=timeout)

    def _shell(self, cmd, timeout=10):
        return self._adb(f"shell {cmd}", timeout)

    def check_locked_state(self):
        """Verifica se o dispositivo esta bloqueado (equivalente a AdbCheckLockedState)."""
        out, _, _ = self._shell("dumpsys window policy | grep showing", timeout=5)
        locked = "showing" in out and "false" not in out
        log(f"Estado de bloqueio: {'BLOQUEADO' if locked else 'DESTRAVADO'}")
        return locked

    def get_miui_version(self):
        """Obtem versao MIUI (equivalente a AdbGetMiuiVersion)."""
        out, _, _ = self._shell("getprop ro.miui.ui.version.name", timeout=5)
        log(f"Versao MIUI: {out.strip() or 'N/A'}")
        return out.strip()

    def get_miui_region(self):
        """Obtem regiao MIUI (equivalente a AdbGetMiuiBuildRegin)."""
        out, _, _ = self._shell("getprop ro.miui.region", timeout=5)
        log(f"Regiao MIUI: {out.strip() or 'N/A'}")
        return out.strip()

    # -- Planos de remocao (FRPPlanO, FRPPlanT, FRPPlanTH, FRPNewPlan) --

    def plan_o_disable_gsf(self):
        """FRPPlanO: Desativa Google Services Framework."""
        log("--- FRPPlanO: Desativando GSF ---")
        cmds = [
            "pm disable-user --user 0 com.google.android.gsf",
            "pm clear com.google.android.gsf",
            "pm clear com.google.android.gms",
        ]
        for cmd in cmds:
            out, err, rc = self._shell(cmd)
            self.results.append(("plan_o", cmd, rc == 0))
        return any(r[2] for r in self.results if r[0] == "plan_o")

    def plan_t_add_account(self):
        """FRPPlanT: Tenta adicionar conta via settings."""
        log("--- FRPPlanT: Adicionando conta via Settings ---")
        cmds = [
            "am start -a android.settings.ADD_ACCOUNT_SETTINGS",
            "am start -a android.settings.SYNC_SETTINGS",
        ]
        for cmd in cmds:
            out, err, rc = self._shell(cmd)
            self.results.append(("plan_t", cmd, rc == 0))
        return any(r[2] for r in self.results if r[0] == "plan_t")

    def plan_th_open_settings(self):
        """FRPPlanTH: Abre Settings diretamente."""
        log("--- FRPPlanTH: Abrindo Settings ---")
        cmds = [
            "am start -n com.android.settings/.Settings",
            "am start -a android.settings.SETTINGS",
        ]
        for cmd in cmds:
            out, err, rc = self._shell(cmd)
            self.results.append(("plan_th", cmd, rc == 0))
        return any(r[2] for r in self.results if r[0] == "plan_th")

    def plan_new_remove_accounts(self):
        """FRPNewPlan: Remove arquivos de conta FRP."""
        log("--- FRPNewPlan: Removendo arquivos de conta ---")
        files_to_remove = [
            "/data/system/accounts.db",
            "/data/system/locksettings.db",
            "/data/system/locksettings.db-shm",
            "/data/system/locksettings.db-wal",
            "/data/system/device_policies.xml",
            "/data/system/users/0/accounts.db",
            "/data/system/users/0/package-restrictions.xml",
        ]
        success = False
        for f in files_to_remove:
            out, err, rc = self._shell(f"rm -f {f}")
            if rc == 0:
                log(f"  Removido: {f}")
                success = True
        return success

    def adb_android_bypass(self):
        """ADBAndroidBypass: Tenta bypass completo."""
        log("--- ADBAndroidBypass: Bypass completo ---")
        cmds = [
            "content insert --uri content://settings/secure --bind name:s:user_setup_complete --bind value:s:1",
            "content insert --uri content://settings/secure --bind name:s:device_provisioned --bind value:s:1",
            "settings put secure user_setup_complete 1",
            "settings put global device_provisioned 1",
            "pm disable com.google.android.setupwizard",
            "pm disable com.android.setupwizard",
        ]
        for cmd in cmds:
            out, err, rc = self._shell(cmd)
            self.results.append(("bypass", cmd, rc == 0))
        return any(r[2] for r in self.results if r[0] == "bypass")

    def remove_xm_frp(self):
        """RemoveXMFRP: Metodo especifico Xiaomi."""
        log("--- RemoveXMFRP: Metodo Xiaomi ---")
        cmds = [
            "am start -a android.settings.SETTINGS",
            "settings put secure user_setup_complete 1",
            "settings put global device_provisioned 1",
            "pm uninstall -k --user 0 com.google.android.gms",
            "pm uninstall -k --user 0 com.google.android.gsf",
        ]
        for cmd in cmds:
            out, err, rc = self._shell(cmd)
            self.results.append(("xm_frp", cmd, rc == 0))
        return any(r[2] for r in self.results if r[0] == "xm_frp")

    def usa_remove_frp(self):
        """USARemoveFRP: Metodo alternativo."""
        log("--- USARemoveFRP: Metodo USA ---")
        cmds = [
            "pm clear com.google.android.gms",
            "pm clear com.google.android.gsf",
            "pm clear com.android.phone",
            "content insert --uri content://settings/secure --bind name:s:user_setup_complete --bind value:s:1",
        ]
        for cmd in cmds:
            out, err, rc = self._shell(cmd)
            self.results.append(("usa", cmd, rc == 0))
        return any(r[2] for r in self.results if r[0] == "usa")

    def remove_frp_all_steps(self):
        """RemoveFrpAllStep: Executa todas as estrategias em sequencia."""
        log("========== RemoveFrpAllStep: Executando todas as estrategias ==========")
        
        strategies = [
            ("FRPNewPlan", self.plan_new_remove_accounts),
            ("FRPPlanO", self.plan_o_disable_gsf),
            ("ADBAndroidBypass", self.adb_android_bypass),
            ("RemoveXMFRP", self.remove_xm_frp),
            ("USARemoveFRP", self.usa_remove_frp),
            ("FRPPlanTH", self.plan_th_open_settings),
            ("FRPPlanT", self.plan_t_add_account),
        ]
        
        for name, func in strategies:
            log(f"[{name}] Executando...")
            try:
                result = func()
                log(f"[{name}] {'SUCESSO' if result else 'FALHOU'}")
            except Exception as e:
                log(f"[{name}] ERRO: {e}", "ERROR")

        return self.results

# --- Fastboot -----------------------------------------------------------------

def fastboot_erase_all(serial):
    """Executa fastboot erase quando bootloader esta destravado."""
    log("========== Fastboot: Apagando particoes ==========")
    fb = [str(FASTBOOT_PATH), "-s", serial]
    
    partitions = ["frp", "userdata", "cache", "misc"]
    results = {}
    
    for part in partitions:
        log(f"Apagando {part}...")
        out, err, rc = run_cmd(fb + ["erase", part], timeout=30)
        if rc == 0:
            log(f"  {part}: OK")
            results[part] = True
        else:
            log(f"  {part}: FALHOU - {err[:100]}", "WARN")
            results[part] = False
    
    # Se erase falhou, tenta format
    if not results.get("userdata"):
        log("Tentando format userdata...")
        run_cmd(fb + ["format", "userdata"], timeout=60)
    
    return results

def fastboot_reboot(serial):
    """Reinicia via fastboot."""
    log("Reiniciando dispositivo...")
    run_cmd([str(FASTBOOT_PATH), "-s", serial, "reboot"], timeout=10)

# --- EDL Mode -----------------------------------------------------------------

def edl_check_9008():
    """Verifica se dispositivo esta em modo EDL 9008."""
    try:
        result = subprocess.run(
            'powershell "Get-PnpDevice | Where-Object { $_.FriendlyName -match \'9008|QDLoader\' } | Select-Object FriendlyName, InstanceId"',
            capture_output=True, text=True, shell=True, timeout=5
        )
        if "9008" in result.stdout:
            log("Dispositivo em modo EDL 9008 detectado!")
            return True
    except:
        pass
    return False

def edl_remove_frp():
    """Usa o EDL tool do 4uKey para remover FRP via protocolo Firehose.
       Equivalente a: My_EDL_frp::Frp_Edl_Remove() e Config_Edl_Remove()"""
    
    if not EDL_EXE.exists():
        log("EDL tool do 4uKey nao encontrado", "ERROR")
        return False

    if not edl_check_9008():
        log("Dispositivo NAO esta em modo EDL 9008", "ERROR")
        log("Instrucoes para entrar em modo EDL:")
        log("  1. Desligue o celular")
        log("  2. Conecte um cabo EDL ou faca test point")
        log("  3. Conecte o USB - deve aparecer como 'Qualcomm HS-USB QDLoader 9008'")
        return False

    log("========== EDL Mode: Removendo FRP ==========")
    
    # Tenta encontrar loader apropriado nos loaders do 4uKey
    loaders = []
    if EDL_LOADERS.exists():
        for root, dirs, files in os.walk(EDL_LOADERS):
            for f in files:
                if f.endswith(".bin") or f.endswith(".mbn") or f.endswith(".elf"):
                    loaders.append(Path(root) / f)
    
    if not loaders:
        log("Nenhum loader firehose encontrado", "ERROR")
        return False
    
    log(f"Loaders disponiveis: {len(loaders)}")
    
    # Tenta cada loader
    # O 4uKey usa edl.exe com: --loader=<path> --memory=ufs --lun=<n>
    # Edl_Get_UfsOrEmmcAndLun() detecta UFS vs eMMC e qual LUN usar
    
    for loader in loaders:
        log(f"Tentando loader: {loader.name}")
        
        # --memory=ufs (Redmi Note 9S e UFS, mas pode ser emmc)
        for mem_type in ["ufs", "emmc"]:
            cmd = [
                str(EDL_EXE),
                f"--loader={loader}",
                f"--memory={mem_type}",
                "erase",
                "frp",
            ]
            out, err, rc = run_cmd(cmd, timeout=60)
            if rc == 0 and "error" not in out.lower():
                log(f"SUCESSO com loader {loader.name} (memoria={mem_type})!")
                return True
            log(f"Falhou com {loader.name} (memoria={mem_type})", "WARN")

    log("Nenhum loader funcionou para este dispositivo", "ERROR")
    return False

# --- MTK BROM Mode ------------------------------------------------------------

def mtk_enter_brom():
    """Verifica se dispositivo esta em modo MTK BROM."""
    try:
        result = subprocess.run(
            'powershell "Get-PnpDevice | Where-Object { $_.FriendlyName -match \'MediaTek|MTK|BROM|DA\' } | Select-Object FriendlyName"',
            capture_output=True, text=True, shell=True, timeout=5
        )
        if "MediaTek" in result.stdout or "MTK" in result.stdout:
            log("Dispositivo em modo MTK BROM!")
            return True
    except:
        pass
    return False

def mtk_remove_frp():
    """Usa o MTK tool do 4uKey para remover FRP.
       Equivalente a: MTKFrpSupportWrapper::EnterMTKMode() + removeFRP_MTK()"""
    
    if not MTK_EXE.exists():
        log("MTK tool do 4uKey nao encontrado", "ERROR")
        return False

    if not mtk_enter_brom():
        log("Dispositivo NAO esta em modo MTK BROM", "ERROR")
        log("Instrucoes para MTK:")
        log("  1. Desligue o celular")
        log("  2. Remova a bateria (se possivel)")
        log("  3. Segure Volume+ e conecte USB")
        log("  4. Deve aparecer como 'MediaTek DA USB VCOM' ou similar")
        return False

    log("========== MTK BROM: Removendo FRP ==========")
    
    # Busca DA especifico para Xiaomi
    da_files = []
    if MTK_LOADERS.exists():
        da_files = list(MTK_LOADERS.glob("*.bin"))
    
    xiaomi_da = [d for d in da_files if "xiaomi" in d.name.lower()]
    if xiaomi_da:
        log(f"DA Xiaomi encontrado: {xiaomi_da[0].name}")
    elif da_files:
        log(f"Usando DA generico: {da_files[0].name}")
    
    # O main.exe e um PyInstaller bundle, nao temos args exatos
    # Mas podemos tentar executa-lo diretamente com o DA
    log("O MTK tool do 4uKey requer parametros especificos.")
    log("Tente executar manualmente pelo terminal de depuracao:")
    log(f'  cd /d "{MTK_EXE.parent}"')
    log(f'  {MTK_EXE} --da=xiaomi_9_DA_6765_6785_6768_6873_6885_6853.bin')
    
    return False

# --- Interface do Usuario -----------------------------------------------------

def print_banner():
    clear_screen()
    banner =     """
    +---------------------------------------+
    |       XiaomiFRPTool v1.0             |
    |  Ferramenta Nativa de Remocao FRP    |
    |  Eng. reversa: Tenorshare 4uKey v2.15|
    +---------------------------------------+
    """
    print(banner)

def print_device_info(device):
    if not device["serial"] and not device["mode"]:
        print("  [!] Nenhum dispositivo detectado")
        return
    
    print(f"  Serial    : {device['serial'] or 'N/A'}")
    print(f"  Modo      : {device['mode'] or 'N/A'}")
    
    if device["mode"] == "adb":
        print(f"  Fabricante: {device['manufacturer'] or 'N/A'}")
        print(f"  Modelo    : {device['model'] or 'N/A'}")
        if device["info"].get("miui_version"):
            print(f"  MIUI      : {device['info']['miui_version']}")
        if device["info"].get("android_version"):
            print(f"  Android   : {device['info']['android_version']}")
    
    elif device["mode"] == "fastboot":
        print(f"  Produto   : {device['product'] or 'N/A'}")
        unlocked = device["bootloader_unlocked"]
        print(f"  Bootloader: {'[OK] DESTRAVADO' if unlocked else '[BL] TRAVADO'}")
    
    elif device["mode"] == "edl":
        print(f"  Estado    : [OK] Modo EDL 9008 ativo")
        print(f"  Acao      : Pressione 3 (novo EDL real) ou 8 (EDL legado 4uKey)")
    
    elif device["mode"] == "mtk_brom":
        print(f"  Estado    : [OK] Modo MTK BROM ativo")
    print()

def print_menu():
    print("  +--- MENU -------------------------------+")
    print("  |  [1]  Detectar dispositivo             |")
    print("  |  [2]  ADB Bypass (todas estrategias)   |")
    print("  |  [3]  EDL REAL (Sahara+Firehose)       |")
    print("  |  [4]  MTK BROM (MediaTek)              |")
    print("  |  [5]  Fastboot (erase particoes)       |")
    print("  |  [6]  Ver logs                         |")
    print("  |  [7]  Sobre                            |")
    print("  |  [8]  EDL Legado (4uKey)               |")
    print("  |  [9]  Gerenciar loaders EDL            |")
    print("  |  [0]  Sair                             |")
    print("  +----------------------------------------+")

def main():
    print_banner()
    print("  Inicializando...\n")
    
    # Verifica dependencias
    adb_ok = check_tool(ADB_PATH, "ADB")
    fb_ok = check_tool(FASTBOOT_PATH, "Fastboot")
    edl_ok = check_tool(EDL_EXE, "EDL tool")
    mtk_ok = check_tool(MTK_EXE, "MTK tool")
    
    print()
    print(f"  ADB       : {'[OK]' if adb_ok else '[--]'} {ADB_PATH}")
    print(f"  Fastboot  : {'[OK]' if fb_ok else '[--]'} {FASTBOOT_PATH}")
    print(f"  EDL tool  : {'[OK]' if edl_ok else '[--]'} {EDL_EXE}")
    print(f"  MTK tool  : {'[OK]' if mtk_ok else '[--]'} {MTK_EXE}")
    print()
    
    if not adb_ok or not fb_ok:
        log("ADB ou Fastboot nao encontrados. O 4uKey esta instalado?", "WARN")
    
    input("  Pressione Enter para continuar...")
    
    device = {}
    
    while True:
        print_banner()
        print_device_info(device)
        print_menu()
        
        choice = input("\n  Opcao: ").strip()
        
        if choice == "1":
            print_banner()
            print("  Detectando dispositivo...\n")
            device = detect_device()
            if device["serial"] or device["mode"]:
                log(f"Dispositivo detectado: modo={device['mode']}")
            else:
                log("Nenhum dispositivo encontrado", "WARN")
            input("\n  Pressione Enter...")
        
        elif choice == "2":
            if device.get("mode") != "adb":
                print("\n  [!] Dispositivo nao esta em modo ADB")
                print("  [!] Conecte o celular e certifique-se que USB debugging esta ativo")
                input("\n  Pressione Enter...")
                continue
            
            print_banner()
            print(f"  Dispositivo: {device['serial']}")
            print("  Executando ADB Bypass...\n")
            
            bypass = ADBBypass(device["serial"])
            
            # Primeiro verifica estado
            bypass.check_locked_state()
            bypass.get_miui_version()
            bypass.get_miui_region()
            
            print()
            
            # Executa todas as estrategias
            results = bypass.remove_frp_all_steps()
            
            print("\n  -- Resultados --")
            for name, cmd, ok in results:
                status = "[OK]" if ok else "[--]"
                print(f"  {status} [{name}] {cmd}")
            
            print("\n  [OK] Bypass concluido! Se funcionou, reinicie o celular.")
            print("  [DICA] Se nao funcionou, tente opcao 3 (EDL REAL) ou 5 (Fastboot)")
            input("\n  Pressione Enter...")
        
        elif choice == "3":
            print_banner()
            print("  EDL REAL - Sahara + Firehose (FRP)\n")
            print("  Usa pyusb + libusb para comunicar diretamente com o")
            print("  dispositivo via protocolo Qualcomm Sahara/Firehose.\n")

            if check_edl_mode():
                print("  [OK] Dispositivo em modo EDL 9008!\n")

                soc_hint = input("  SoC do dispositivo (ex: sdm660, sm7125, sm8250) [auto]: ").strip()
                if not soc_hint:
                    soc_hint = None

                loader_path = None
                if soc_hint:
                    loader_path = get_loader_for_soc(soc_hint)
                    if not loader_path:
                        print(f"\n  [!] Loader para {soc_hint} nao encontrado.")
                        print("  Tente opcao 9 para gerenciar loaders.\n")
                        if input("  Continuar mesmo assim? (s/N): ").strip().lower() != "s":
                            input("\n  Pressione Enter...")
                            continue

                print()
                if input("  Remover FRP via EDL REAL? (s/N): ").strip().lower() == "s":
                    print()
                    success = remove_frp_edl(loader_path=loader_path, soc_hint=soc_hint)
                    print(f"\n  Resultado: {'SUCESSO' if success else 'FALHA'}")
                    if success:
                        print("  Desconecte e reinicie o celular.")
                else:
                    print("  Cancelado.")
            else:
                print("  [--] Nenhum dispositivo em modo EDL 9008\n")
                print("  Para entrar em modo EDL:")
                print("  1. Desligue o celular completamente")
                print("  2. Conecte USB + segure Vol+ e Vol- (ou use test point)")
                print("  3. Deve aparecer como 'Qualcomm HS-USB QDLoader 9008'\n")

                if device.get("mode") == "fastboot":
                    if input("  Tentar reboot-edl via fastboot? (s/N): ").strip().lower() == "s":
                        run_cmd([str(FASTBOOT_PATH), "-s", device["serial"], "oem", "reboot-edl"], timeout=10)
                        print("  Comando enviado!")
            
            input("\n  Pressione Enter...")
        
        elif choice == "4":
            print_banner()
            print("  Modo MTK BROM (MediaTek)\n")
            
            if mtk_enter_brom():
                print("  ✅ Dispositivo em modo MTK BROM!")
                mtk_remove_frp()
            else:
                print("  ❌ Dispositivo NAO esta em modo MTK BROM")
                print()
                print("  Para MTK (MediaTek):")
                print("  1. Desligue o celular")
                print("  2. Remova a bateria (se possivel)")
                print("  3. Segure Volume+ e conecte USB")
                print("  4. Instale o driver VCOM se necessario")
            
            input("\n  Pressione Enter...")
        
        elif choice == "5":
            if device.get("mode") != "fastboot":
                print("\n  [!] Dispositivo nao esta em modo Fastboot")
                print("  [!] Para entrar: desligue e segure Volume- + Power")
                input("\n  Pressione Enter...")
                continue
            
            print_banner()
            print(f"  Dispositivo: {device['serial']} ({device.get('product', 'N/A')})")
            
            unlocked = device.get("bootloader_unlocked", False)
            if unlocked:
                print("  ✅ Bootloader DESTRAVADO")
                print()
                print("  ⚠️  ATENCAO: Isso vai apagar TODOS os dados do celular!")
                confirm = input("\n  Tem certeza? Digite 'ERASE' para confirmar: ").strip()
                if confirm == "ERASE":
                    print()
                    fastboot_erase_all(device["serial"])
                    print("\n  ✅ Particoes apagadas!")
                    print("  Reiniciando...")
                    fastboot_reboot(device["serial"])
                else:
                    print("  Cancelado.")
            else:
                print("  ❌ Bootloader TRAVADO - Fastboot erase nao funciona")
                print()
                print("  Para destravar o bootloader:")
                print("  1. Habilite 'OEM Unlock' nas opcoes desenvolvedor")
                print("  2. Use: fastboot oem unlock")
                print("  (Isso vai apagar todos os dados!)")
            
            input("\n  Pressione Enter...")
        
        elif choice == "6":
            print_banner()
            print("  -- Ultimas linhas do log --\n")
            try:
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines[-30:]:
                        print(f"  {line.strip()}")
            except:
                print("  (log vazio)")
            input("\n  Pressione Enter...")
        
        elif choice == "7":
            print_banner()
            print("  XiaomiFRPTool v1.0")
            print("  Baseado na engenharia reversa do Tenorshare 4uKey for Android 2.15.2")
            print()
            print("  Metodos implementados:")
            print("  +--- FRPPlanO      - Desativar Google Services Framework")
            print("  +--- FRPPlanT      - Abrir menu de contas")
            print("  +--- FRPPlanTH     - Abrir Settings")
            print("  +--- FRPNewPlan    - Remover arquivos de conta do /data/system/")
            print("  +--- ADBAndroidBypass - Bypass completo (setup wizard)")
            print("  +--- RemoveXMFRP   - Metodo especifico Xiaomi")
            print("  +--- USARemoveFRP  - Metodo alternativo USA")
            print("  +--- EDL REAL      - Sahara+Firehose nativo (pyusb)")
            print("  +--- EDL Firehose  - Remocao via modo 9008 (usa tools 4uKey)")
            print("  +--- MTK BROM DA   - Remocao via Download Agent (usa tools 4uKey)")
            print("  +--- Fastboot      - Apagar particoes (bootloader unlocked)")
            print()
            print("  Creditos: Eng. reversa do 4uKey for Android")
            print("  Proposito educacional / backup pessoal")
            input("\n  Pressione Enter...")
        
        elif choice == "8":
            print_banner()
            print("  EDL Legado (via 4uKey tools)\n")

            if edl_check_9008():
                print("  [OK] Dispositivo em modo EDL 9008!\n")
                if input("  Remover FRP via EDL (4uKey)? (s/N): ").strip().lower() == "s":
                    edl_remove_frp()
            else:
                print("  [--] Dispositivo NAO esta em modo EDL 9008")
                print()
                print("  Para entrar em modo EDL:")
                print("  1. Desligue o celular completamente")
                print("  2. Use um cabo EDL ou faca test point nos pinos")
                print("  3. Conecte o USB ao computador")
                print("  4. Deve aparecer como 'Qualcomm HS-USB QDLoader 9008'")

                if device.get("mode") == "fastboot":
                    if input("\n  Tentar reboot-edl via fastboot? (s/N): ").strip().lower() == "s":
                        run_cmd([str(FASTBOOT_PATH), "-s", device["serial"], "oem", "reboot-edl"], timeout=10)
                        print("  Comando enviado!")

            input("\n  Pressione Enter...")

        elif choice == "9":
            print_banner()
            print("  Gerenciar Loaders EDL\n")

            loaders = list_available_loaders()
            if loaders:
                print(f"  Loaders disponiveis: {len(loaders)}\n")
                for i, (src, path) in enumerate(loaders, 1):
                    size_kb = path.stat().st_size / 1024
                    print(f"  [{i}] [{src}] {path.name} ({size_kb:.0f} KB)")
            else:
                print("  Nenhum loader encontrado no sistema.\n")

            print()
            print("  SoCs Xiaomi suportados para download:")
            for soc in sorted(XIAOMI_LOADERS.keys()):
                print(f"    - {soc} -> {XIAOMI_LOADERS[soc]}")

            print()
            soc_dl = input("  Digite um SoC para baixar loader (Enter para voltar): ").strip()
            if soc_dl:
                print()
                loader_path = get_loader_for_soc(soc_dl)
                if loader_path:
                    print(f"  Loader {XIAOMI_LOADERS.get(soc_dl, '')} pronto em:")
                    print(f"  {loader_path}")
                else:
                    print(f"  Nao foi possivel obter loader para {soc_dl}")
                    print("  Tente baixar manualmente de:")
                    print("  https://github.com/bkerler/Loaders")
                    print("  https://github.com/AndroidDumps/Firehose-Loaders")

            input("\n  Pressione Enter...")

        elif choice == "0":
            print("\n  Saindo...")
            break
        
        else:
            print("\n  Opcao invalida!")
            input("  Pressione Enter...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Interrompido pelo usuario.")
    except Exception as e:
        log(f"Erro fatal: {e}", "ERROR")
        import traceback
        traceback.print_exc()
    finally:
        print(f"\n  Log salvo em: {LOG_FILE}")
