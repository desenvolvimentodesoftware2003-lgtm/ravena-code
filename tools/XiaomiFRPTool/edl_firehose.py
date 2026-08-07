"""
edl_firehose.py - Implementacao real do protocolo EDL (Sahara + Firehose)
Remove FRP diretamente via USB sem depender do 4uKey.

Protocolos implementados:
  - Sahara: handshake + envio do loader (programmer ELF)
  - Firehose: comando XML para apagar particao FRP
"""

import os
import re
import io
import sys
import time
import json
import struct
import zipfile
import hashlib
import tarfile
import tempfile
import platform
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from urllib.request import urlopen, Request

# --- Config ----------------------------------------------------------------

LOG_FILE = Path(__file__).parent / "frp_tool.log"

# VID/PID Qualcomm EDL 9008
QCOM_VID = 0x05C6
QDLOADER_PIDS = {0x9008, 0x9003, 0x900E, 0x9006, 0x9010, 0x9015, 0x901B}
XIAOMI_EDL_PIDS = {0x9008, 0x9003, 0x9010}

# Sahara protocol commands
SAHARA_HELLO          = 0x1
SAHARA_HELLO_RESP     = 0x2
SAHARA_READ_DATA      = 0x3
SAHARA_READ_DATA_RESP = 0x4
SAHARA_DONE           = 0x5
SAHARA_DONE_RESP      = 0x6

# Firehose USB endpoints
FH_EP_IN  = 0x81
FH_EP_OUT = 0x01

# Loader cache
LOADER_CACHE_DIR = Path(tempfile.gettempdir()) / "xiaomi_frp_loaders"

# Repositorio de loaders Xiaomi (mapeamento SoC -> loader filename)
# Extraidos de firmware oficial MIUI / telegram groups / xda
XIAOMI_LOADERS = {
    "msm8916":  "prog_emmc_firehose_8916.mbn",
    "msm8937":  "prog_emmc_firehose_8937.mbn",
    "msm8940":  "prog_emmc_firehose_8937.mbn",
    "msm8953":  "prog_emmc_firehose_8953.mbn",
    "msm8956":  "prog_emmc_firehose_8956.mbn",
    "sdm450":   "prog_emmc_firehose_sdm450.mbn",
    "sdm625":   "prog_emmc_firehose_8953.mbn",
    "sdm630":   "prog_emmc_firehose_sdm630.mbn",
    "sdm636":   "prog_emmc_firehose_sdm630.mbn",
    "sdm660":   "prog_emmc_firehose_sdm660.mbn",
    "sdm670":   "prog_emmc_firehose_sdm670.mbn",
    "sdm710":   "prog_emmc_firehose_sdm710.mbn",
    "sdm845":   "prog_emmc_firehose_sdm845.mbn",
    "sdm855":   "prog_emmc_firehose_sdm855.elf",
    "sm6150":   "prog_emmc_firehose_sm6150.elf",
    "sm6250":   "prog_firehose_lite_sm6250.elf",
    "sm6350":   "prog_firehose_lite_sm6350.elf",
    "sm7125":   "prog_firehose_lite_sm7125.elf",
    "sm7150":   "prog_firehose_lite_sm7150.elf",
    "sm7225":   "prog_firehose_lite_sm7225.elf",
    "sm7250":   "prog_firehose_lite_sm7250.elf",
    "sm7325":   "prog_firehose_lite_sm7325.elf",
    "sm7350":   "prog_firehose_lite_sm7350.elf",
    "sm8150":   "prog_firehose_lite_sm8150.elf",
    "sm8250":   "prog_firehose_lite_sm8250.elf",
    "sm8350":   "prog_firehose_lite_sm8350.elf",
    "sm8450":   "prog_firehose_lite_sm8450.elf",
    "sm8550":   "prog_firehose_lite_sm8550.elf",
}

# URLs de fallback para download de loaders
LOADER_FALLBACK_URLS = [
    "https://raw.githubusercontent.com/bkerler/Loaders/main/{filename}",
    "https://raw.githubusercontent.com/AndroidDumps/Firehose-Loaders/master/{filename}",
]

# --- Logging ----------------------------------------------------------------

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:12]
    line = f"{ts} [EDL] [{level}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass

# --- USB backend -----------------------------------------------------------

USB_BACKEND = None

def _get_usb_backend():
    global USB_BACKEND
    if USB_BACKEND is not None:
        return USB_BACKEND
    try:
        import libusb_package
        USB_BACKEND = libusb_package.get_libusb1_backend()
        log(f"Backend libusb carregado via libusb-package", "DEBUG")
        return USB_BACKEND
    except:
        pass
    try:
        import usb.backend.libusb1 as lb1
        USB_BACKEND = lb1.get_backend()
        log(f"Backend libusb1 carregado", "DEBUG")
        return USB_BACKEND
    except:
        pass
    log("Nenhum backend USB encontrado (instale libusb-package)", "ERROR")
    return None

def _find_edl_devices():
    """Encontra dispositivos Qualcomm em modo EDL 9008."""
    be = _get_usb_backend()
    if not be:
        return []
    try:
        import usb.core as usbc
        devices = []
        for pid in QDLOADER_PIDS:
            devs = usbc.find(idVendor=QCOM_VID, idProduct=pid, find_all=True, backend=be)
            if devs:
                for d in devs:
                    devices.append(d)
        return devices
    except Exception as e:
        log(f"Erro ao buscar dispositivos EDL: {e}", "ERROR")
        return []

def _find_edl_wmi():
    """Fallback: detecta EDL via WMI (PowerShell)."""
    try:
        import subprocess
        cmd = 'powershell "Get-PnpDevice | Where-Object { $_.FriendlyName -match \'9008|QDLoader|EDL|Qualcomm.*HS.*USB\' } | Select-Object FriendlyName, InstanceId, Status | ConvertTo-Json"'
        r = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=5)
        if r.stdout.strip():
            log(f"EDL detectado via WMI", "DEBUG")
            return True
    except:
        pass
    return False

# --- Sahara Protocol -------------------------------------------------------

class SaharaError(Exception):
    pass

class SaharaProtocol:
    """Implementa o protocolo Sahara para comunicacao com bootrom Qualcomm."""

    def __init__(self, dev):
        self.dev = dev
        self.ep_in = None
        self.ep_out = None
        self.max_cmd_len = 4096

    def _find_endpoints(self, intf):
        """Configura endpoints bulk para o Sahara."""
        self.ep_in = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN and
                                    usb.util.endpoint_type(e.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK
        )
        self.ep_out = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT and
                                    usb.util.endpoint_type(e.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK
        )
        if not self.ep_in or not self.ep_out:
            raise SaharaError("Nao foi possivel encontrar endpoints bulk Sahara")

    def connect(self):
        """Estabelece conexao Sahara com o dispositivo."""
        cfg = self.dev.get_active_configuration()
        intf = cfg[(0, 0)]

        # Tenta dar detach no driver do kernel primeiro
        try:
            if self.dev.is_kernel_driver_active(intf.bInterfaceNumber):
                self.dev.detach_kernel_driver(intf.bInterfaceNumber)
        except:
            pass

        try:
            self.dev.set_configuration()
        except:
            pass

        usb.util.claim_interface(self.dev, intf)
        self._find_endpoints(intf)

    def _recv_packet(self, timeout=5000):
        """Recebe um pacote Sahara (header de 8 bytes + dados)."""
        raw = self.ep_in.read(0x1000, timeout=timeout)
        if len(raw) < 8:
            raise SaharaError(f"Pacote Sahara muito curto: {len(raw)} bytes")

        cmd_id = struct.unpack_from("<I", raw, 0)[0]
        length = struct.unpack_from("<I", raw, 4)[0]

        data = raw[8:8+length] if length > 0 else b""

        if cmd_id not in (SAHARA_HELLO, SAHARA_HELLO_RESP, SAHARA_READ_DATA,
                          SAHARA_READ_DATA_RESP, SAHARA_DONE, SAHARA_DONE_RESP):
            log(f"Pacote Sahara desconhecido: cmd=0x{cmd_id:02X}", "WARN")

        return cmd_id, length, data, raw[:8+length]

    def _send_packet(self, cmd_id, data=b""):
        """Envia um pacote Sahara."""
        header = struct.pack("<II", cmd_id, len(data))
        self.ep_out.write(header + data)

    def handshake(self):
        """
        Executa o handshake Sahara completo.
        Retorna as informacoes do dispositivo.
        """
        # Aguarda HELLO do target
        cmd, length, data, raw = self._recv_packet()
        if cmd != SAHARA_HELLO:
            raise SaharaError(f"Esperava HELLO(0x1), recebeu 0x{cmd:02X}")

        if len(data) >= 16:
            version      = struct.unpack_from("<I", data, 0)[0]
            version_min  = struct.unpack_from("<I", data, 4)[0]
            max_cmd_len  = struct.unpack_from("<I", data, 8)[0]
            mode         = struct.unpack_from("<I", data, 12)[0]
            self.max_cmd_len = max_cmd_len if max_cmd_len > 0 else 4096
        else:
            raise SaharaError("HELLO packet muito curto")

        log(f"Sahara HELLO: version={version}, mode={mode}, max_cmd_len={self.max_cmd_len}")

        # Envia HELLO_RESP (modo 1 = command mode)
        resp = struct.pack("<IIIIIIIII",
            1,     # version
            1,     # version_min
            mode,  # mode
            0, 0, 0, 0, 0, 0  # padding
        )
        self._send_packet(SAHARA_HELLO_RESP, resp)

        log(f"Sahara HELLO_RESP enviado (mode={mode})")

        return {
            "version": version,
            "version_min": version_min,
            "max_cmd_len": max_cmd_len,
            "mode": mode,
        }

    def read_data_and_send_loader(self, loader_data, image_id=0):
        """
        Processa requisicoes READ_DATA do Sahara e envia o loader.
        Sahara pede chunks via READ_DATA -> nos enviamos os dados.
        """
        loader_offset = 0
        loader_size = len(loader_data)

        while True:
            cmd, length, data, raw = self._recv_packet()

            if cmd == SAHARA_DONE:
                log(f"Sahara DONE recebido (loader enviado com sucesso)")
                return True

            elif cmd == SAHARA_READ_DATA:
                img_id  = struct.unpack_from("<I", data, 0)[0]
                offset  = struct.unpack_from("<Q", data, 4)[0]
                length  = struct.unpack_from("<Q", data, 12)[0]

                chunk = loader_data[offset:offset+length]
                self._send_packet(SAHARA_READ_DATA_RESP, chunk)
            else:
                log(f"Sahara: cmd inesperado 0x{cmd:02X} durante envio do loader", "WARN")
                break

        return False

    def send_done(self, image_id=0):
        """Envia comando DONE para finalizar Sahara e entrar em modo Firehose."""
        data = struct.pack("<II", image_id, 0)
        self._send_packet(SAHARA_DONE, data)

        # Aguarda DONE_RESP
        try:
            cmd, length, data, raw = self._recv_packet(timeout=10000)
            if cmd == SAHARA_DONE_RESP:
                log(f"Sahara DONE_RESP recebido")
                return True
        except:
            pass

        return True  # Em alguns firmwares o DONE_RESP nao chega

    def close(self):
        """Libera a interface USB."""
        try:
            cfg = self.dev.get_active_configuration()
            intf = cfg[(0, 0)]
            usb.util.release_interface(self.dev, intf)
        except:
            pass

# --- Firehose Protocol -----------------------------------------------------

class FirehoseError(Exception):
    pass

class FirehoseProtocol:
    """Implementa o protocolo Firehose (streaming XML) para Qualcomm EDL."""

    def __init__(self, dev):
        self.dev = dev
        self.ep_in = None
        self.ep_out = None

    def _find_endpoints(self, intf):
        """Configura endpoints para Firehose (streaming channel)."""
        self.ep_in = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN and
                                    usb.util.endpoint_type(e.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK
        )
        self.ep_out = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT and
                                    usb.util.endpoint_type(e.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK
        )
        if not self.ep_in or not self.ep_out:
            raise FirehoseError("Nao foi possivel encontrar endpoints Firehose")

    def connect(self, intf_num=0):
        """Conecta ao streaming channel Firehose."""
        cfg = self.dev.get_active_configuration()
        intf = cfg[(0, intf_num)]

        try:
            if self.dev.is_kernel_driver_active(intf.bInterfaceNumber):
                self.dev.detach_kernel_driver(intf.bInterfaceNumber)
        except:
            pass

        usb.util.claim_interface(self.dev, intf)
        self._find_endpoints(intf)

    def send_xml(self, xml_str, timeout=10000):
        """Envia comando XML e recebe resposta."""
        payload = xml_str.encode("utf-8")
        self.ep_out.write(payload, timeout=timeout)
        time.sleep(0.3)

        resposta = b""
        try:
            while True:
                chunk = self.ep_in.read(0x10000, timeout=timeout)
                if not chunk:
                    break
                resposta += bytes(chunk)
                # O streaming channel pode enviar varios pacotes
                # Tenta parsear XML para ver se ja temos resposta completa
                try:
                    ET.fromstring(resposta.decode("utf-8", errors="replace"))
                    break
                except:
                    continue
        except:
            pass

        return resposta.decode("utf-8", errors="replace")

    def parse_response(self, xml_str):
        """Interpreta resposta XML do Firehose."""
        result = {"status": "unknown", "raw": xml_str}
        if not xml_str.strip():
            return result

        try:
            root = ET.fromstring(xml_str)
            result["raw"] = xml_str
            result["tag"] = root.tag

            if root.tag == "data":
                result["status"] = root.get("response", "unknown")
            elif root.tag == "log":
                result["status"] = root.get("value", "unknown")
                result["message"] = root.text
            elif root.tag == "configure":
                result["status"] = "configured"
            elif root.tag == "erase":
                result["status"] = root.get("response", "unknown")

        except ET.ParseError as e:
            result["status"] = "parse_error"
            result["error"] = str(e)

        return result

    def configure(self, skip_storage_init="0", zlib="False"):
        """Envia comando <configure> para o Firehose."""
        xml = f'<configure MemoryName="emmc" SkipStorageInit="{skip_storage_init}" ZippedHashes="{zlib}" Verbose="0" MaxPayloadSizeToTargetInBytes="1048576" MaxPayloadSizeToTargetInBytesSupported="false" AlwaysValidate="false"/>'
        log(f"Firehose: enviando configure...")
        resp = self.send_xml(xml)
        parsed = self.parse_response(resp)
        log(f"Firehose configure response: {parsed['status']}")
        return parsed

    def read_pinfo(self, part_name="frp"):
        """Le informacoes da particao (opcional, para debug)."""
        xml = f'<read Ptt="True" PartitionName="{part_name}"/>'
        log(f"Firehose: lendo info da particao {part_name}...")
        resp = self.send_xml(xml)
        parsed = self.parse_response(resp)
        log(f"Firehose read_pinfo: {parsed['status']}")
        return parsed

    def erase(self, part_name="frp"):
        """Apaga uma particao via Firehose."""
        xml = f'<erase PartitionName="{part_name}"/>'
        log(f"Firehose: apagando particao {part_name}...")
        resp = self.send_xml(xml)
        parsed = self.parse_response(resp)
        log(f"Firehose erase response: {parsed['status']}")
        return parsed

    def power_off(self):
        """Envia comando <power> para desligar o dispositivo."""
        xml = '<power value="off"/>'
        log(f"Firehose: enviando power off...")
        resp = self.send_xml(xml)
        parsed = self.parse_response(resp)
        log(f"Firehose power response: {parsed['status']}")
        return parsed

    def close(self):
        """Libera interface."""
        try:
            cfg = self.dev.get_active_configuration()
            intf = cfg[(0, 1)]  # Firehose geralmente na interface 1
            usb.util.release_interface(self.dev, intf)
        except:
            pass

# --- Loader Management -----------------------------------------------------

def get_loader_for_soc(soc_name):
    """
    Tenta encontrar o loader (programmer ELF/MBN) para o SoC especificado.
    Procura em: cache local, diretorios do sistema, download.
    """
    loader_name = XIAOMI_LOADERS.get(soc_name.lower(), None)
    if not loader_name:
        log(f"Nenhum loader conhecido para SoC: {soc_name}", "WARN")
        return None

    # 1. Procura no cache local
    LOADER_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached = LOADER_CACHE_DIR / loader_name
    if cached.exists() and cached.stat().st_size > 0:
        log(f"Loader encontrado no cache: {cached}")
        return cached

    # 2. Procura em diretorios comuns do sistema
    search_dirs = [
        Path("C:/Program Files (x86)/4uKey for Android/edl_exe/Loaders"),
        Path("C:/Program Files (x86)/4uKey for Android/edl_exe/Prog"),
        Path("C:/Program Files (x86)/MiFlash/Prog"),
        Path("C:/Program Files (x86)/Qualcomm/QPST/bin"),
    ]
    for d in search_dirs:
        if d.exists():
            for f in d.iterdir():
                if f.name.lower() == loader_name.lower() and f.stat().st_size > 0:
                    log(f"Loader encontrado em: {f}")
                    return f

    # 3. Tenta fazer download
    log(f"Loader {loader_name} nao encontrado localmente. Tentando download...")
    for base_url in LOADER_FALLBACK_URLS:
        url = base_url.format(filename=loader_name)
        try:
            log(f"Downloading: {url}")
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=120) as resp:
                data = resp.read()
                if len(data) > 1024:
                    with open(cached, "wb") as f:
                        f.write(data)
                    log(f"Loader salvo em: {cached} ({len(data)} bytes)")
                    return cached
        except Exception as e:
            log(f"Falha ao baixar {url}: {e}", "WARN")
            continue

    log(f"Nao foi possivel obter loader: {loader_name}", "ERROR")
    return None

def find_any_loader():
    """
    Procura por qualquer loader firehose disponivel.
    Usado quando nao sabemos o SoC exato.
    """
    # Cache
    LOADER_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached_loaders = list(LOADER_CACHE_DIR.glob("prog_*"))
    if cached_loaders:
        log(f"Loaders em cache: {len(cached_loaders)}")
        return cached_loaders[0]

    # Diretorios do sistema
    search_dirs = [
        Path("C:/Program Files (x86)/4uKey for Android/edl_exe/Loaders"),
        Path("C:/Program Files (x86)/4uKey for Android/edl_exe/Prog"),
        Path("C:/Program Files (x86)/MiFlash/Prog"),
    ]
    for d in search_dirs:
        if d.exists():
            loaders = []
            for f in d.iterdir():
                if f.name.lower().startswith("prog_") and f.suffix in (".elf", ".mbn", ".bin"):
                    loaders.append(f)
            if loaders:
                log(f"Loaders encontrados em {d}: {len(loaders)}")
                return loaders[0]

    log("Nenhum loader firehose encontrado no sistema", "WARN")
    return None

def guess_soc_from_device(info):
    """
    Tenta identificar o SoC com base nas informacoes do dispositivo.
    info pode ser um dicionario com dados do ADB ou fastboot.
    """
    soc_hints = [
        info.get("product"),
        info.get("model"),
        info.get("device"),
        info.get("ro.board.platform"),
        info.get("ro.chipname"),
        info.get("ro.hardware"),
    ]

    # Mapa de nomes de produto Xiaomi para SoC
    product_soc = {
        "sdm660": "sdm660",  "sdm845": "sdm845", "sdm855": "sdm855",
        "sm6150": "sm6150",  "sm6250": "sm6250", "sm6350": "sm6350",
        "sm7125": "sm7125",  "sm7150": "sm7150", "sm7225": "sm7225",
        "sm7250": "sm7250",  "sm7325": "sm7325", "sm7350": "sm7350",
        "sm8150": "sm8150",  "sm8250": "sm8250", "sm8350": "sm8350",
        "sm8450": "sm8450",  "sm8550": "sm8550",
        "msm8916": "msm8916", "msm8937": "msm8937", "msm8940": "msm8937",
        "msm8953": "msm8953", "msm8956": "msm8956",
        "sdm450": "sdm450", "sdm625": "sdm625",
        "sdm630": "sdm630", "sdm636": "sdm630",
        "sdm670": "sdm670", "sdm710": "sdm710",
    }

    for hint in soc_hints:
        if not hint:
            continue
        hint_lower = hint.lower()
        for key, soc in product_soc.items():
            if key in hint_lower:
                log(f"SoC identificado via hint '{hint}': {soc}")
                return soc

    return None

# --- EDL Device Manager ----------------------------------------------------

class EDLDevice:
    """Gerenciador completo de dispositivo em modo EDL."""

    def __init__(self, usb_dev=None):
        self.usb_dev = usb_dev
        self.sahara = None
        self.firehose = None
        self.info = {}
        self.loader_path = None

    @staticmethod
    def detect(timeout=3):
        """Detecta se ha algum dispositivo em modo EDL 9008."""
        import usb.core as usbc

        be = _get_usb_backend()
        if not be:
            return None

        log("Procurando dispositivos EDL 9008...")
        for pid in QDLOADER_PIDS:
            devs = usbc.find(idVendor=QCOM_VID, idProduct=pid, find_all=True, backend=be)
            if devs:
                for d in devs:
                    edl = EDLDevice(d)
                    log(f"Dispositivo EDL encontrado: VID=0x{QCOM_VID:04X} PID=0x{pid:04X}")
                    return edl

        return None

    def get_usb_info(self):
        """Retorna informacoes USB do dispositivo."""
        if not self.usb_dev:
            return {}
        info = {
            "vid": self.usb_dev.idVendor,
            "pid": self.usb_dev.idProduct,
            "manufacturer": self.usb_dev.manufacturer or "",
            "product": self.usb_dev.product or "",
            "serial": self.usb_dev.serial_number or "",
        }
        # Tenta ler descritores USB qualcomm
        try:
            desc = usb.util.get_string(self.usb_dev, 256)
            if desc:
                info["descriptor"] = desc
        except:
            pass
        return info

    def enter_sahara(self):
        """Entra em modo Sahara e faz handshake."""
        if not self.usb_dev:
            raise SaharaError("Sem dispositivo USB")

        self.sahara = SaharaProtocol(self.usb_dev)
        self.sahara.connect()
        info = self.sahara.handshake()
        self.info["sahara"] = info
        return info

    def send_loader(self, loader_path=None):
        """
        Envia o firehose loader para o dispositivo via Sahara.
        Retorna True se o loader foi aceito.
        """
        if not self.sahara:
            raise SaharaError("Sahara nao conectado")

        if loader_path:
            self.loader_path = Path(loader_path)
        elif self.loader_path:
            pass
        else:
            lp = find_any_loader()
            if not lp:
                raise SaharaError("Nenhum loader firehose disponivel")
            self.loader_path = Path(lp)

        if not self.loader_path.exists():
            raise SaharaError(f"Loader nao existe: {self.loader_path}")

        loader_size = os.path.getsize(self.loader_path)
        log(f"Loader: {self.loader_path.name} ({loader_size} bytes)")

        with open(self.loader_path, "rb") as f:
            loader_data = f.read()
            ok = self.sahara.read_data_and_send_loader(loader_data)

        if ok:
            self.info["loader"] = self.loader_path.name
            self.info["loader_size"] = loader_size

        return ok

    def enter_firehose(self):
        """Finaliza Sahara e entra no modo Firehose (streaming commands)."""
        if not self.sahara:
            raise SaharaError("Sahara nao conectado")

        log("Finalizando Sahara e entrando em modo Firehose...")
        self.sahara.send_done()
        time.sleep(0.5)

        # Cria Firehose protocol
        self.firehose = FirehoseProtocol(self.usb_dev)
        try:
            # O streaming channel normalmente esta na interface 1
            self.firehose.connect(intf_num=1)
        except:
            try:
                # Fallback para interface 0
                self.firehose.connect(intf_num=0)
            except Exception as e:
                raise FirehoseError(f"Nao foi possivel conectar Firehose: {e}")

        return True

    def remove_frp(self):
        """
        Executa a remocao FRP via Firehose.
        1. Configure
        2. Erase 'frp'
        3. Verifica resultado
        """
        if not self.firehose:
            raise FirehoseError("Firehose nao conectado")

        # 1. Configure
        cfg_resp = self.firehose.configure()
        if cfg_resp["status"] in ("configured", "ok", "done"):
            log("Firehose configurado com sucesso")
        else:
            log(f"Firehose configure retornou: {cfg_resp['status']}", "WARN")

        # 2. Le info da particao FRP (opcional, tentativa)
        try:
            self.firehose.read_pinfo("frp")
        except:
            pass

        # 3. Apaga FRP
        result = self.firehose.erase("frp")

        if result["status"] in ("ok", "done", "success"):
            log("Particao FRP apagada com sucesso!")
            return True
        elif result["status"] == "error":
            err_msg = result.get("raw", "erro desconhecido")
            log(f"Falha ao apagar FRP: {err_msg}", "ERROR")
            return False
        else:
            log(f"Resultado inesperado ao apagar FRP: {result}", "WARN")
            return False

    def close(self):
        """Fecha todas as conexoes."""
        try:
            if self.firehose:
                self.firehose.close()
        except:
            pass
        try:
            if self.sahara:
                self.sahara.close()
        except:
            pass

    def reboot(self):
        """Tenta reiniciar o dispositivo."""
        try:
            if self.firehose:
                self.firehose.power_off()
        except:
            pass
        log("Comando de reboot enviado")

# --- Funcao principal ------------------------------------------------------

def remove_frp_edl(loader_path=None, soc_hint=None):
    """
    Funcao principal para remocao de FRP via EDL.
    
    Args:
        loader_path: Caminho para o firehose loader (opcional, auto-detecta se None)
        soc_hint: Nome do SoC (ex: "sm7125") para baixar loader correto
    
    Returns:
        bool: True se FRP foi removido com sucesso
    """
    log("=" * 60)
    log("Iniciando remocao FRP via EDL (Sahara + Firehose)")
    log("=" * 60)

    # 1. Detecta dispositivo EDL
    edl = EDLDevice.detect()
    if not edl:
        log("Nenhum dispositivo em modo EDL 9008 encontrado!", "ERROR")
        log("Instrucoes para entrar em modo EDL:")
        log("  1. Desligue o celular")
        log("  2. Conecte o USB e segure as teclas (ou use test point)")
        log("  3. Para Xiaomi: Desligue -> Conecte USB -> Segure Vol+ e Vol-")
        log("  4. Deve aparecer como 'Qualcomm HS-USB QDLoader 9008'")
        return False

    usb_info = edl.get_usb_info()
    log(f"Dispositivo EDL detectado:")
    log(f"  VID: 0x{usb_info.get('vid', 0):04X}")
    log(f"  PID: 0x{usb_info.get('pid', 0):04X}")
    log(f"  Fabricante: {usb_info.get('manufacturer', 'N/A')}")
    log(f"  Produto: {usb_info.get('product', 'N/A')}")

    # 2. Determina loader
    if not loader_path and soc_hint:
        loader_path = get_loader_for_soc(soc_hint)

    if not loader_path:
        loader_path = find_any_loader()

    if not loader_path:
        log("Nenhum loader firehose encontrado. Tente especificar o SoC.", "ERROR")
        log("SoCs Xiaomi suportados: " + ", ".join(sorted(XIAOMI_LOADERS.keys())))
        edl.close()
        return False

    loader_path = Path(loader_path)
    if not loader_path.exists():
        log(f"Loader nao encontrado: {loader_path}", "ERROR")
        edl.close()
        return False

    log(f"Usando loader: {loader_path} ({loader_path.stat().st_size} bytes)")

    # 3. Handshake Sahara
    try:
        edl.enter_sahara()
    except Exception as e:
        log(f"Falha no handshake Sahara: {e}", "ERROR")
        edl.close()
        return False

    # 4. Envia loader via Sahara
    try:
        log("Enviando loader para o dispositivo...")
        ok = edl.send_loader(loader_path)
        if not ok:
            log("Falha ao enviar loader!", "ERROR")
            edl.close()
            return False
        log("Loader enviado com sucesso!")
    except Exception as e:
        log(f"Erro ao enviar loader: {e}", "ERROR")
        edl.close()
        return False

    time.sleep(1)

    # 5. Transita para Firehose
    try:
        edl.enter_firehose()
        log("Modo Firehose ativado!")
    except Exception as e:
        log(f"Falha ao entrar em modo Firehose: {e}", "ERROR")
        edl.close()
        return False

    # 6. Apaga FRP
    try:
        log("Apagando particao FRP...")
        success = edl.remove_frp()
        if success:
            log("FRP removido com sucesso!")
        else:
            log("Falha na remocao do FRP", "WARN")
    except Exception as e:
        log(f"Erro ao apagar FRP: {e}", "ERROR")
        edl.close()
        return False

    # 7. Finaliza
    try:
        edl.reboot()
    except:
        pass

    edl.close()
    log("Processo EDL concluido")

    if success:
        log("Reinicie o celular. O FRP deve ter sido removido.")
    return success

def check_edl_mode():
    """Verifica se o dispositivo esta em modo EDL 9008 (retorna bool)."""
    edl = EDLDevice.detect()
    if edl:
        edl.close()
        return True
    return _find_edl_wmi()

def list_available_loaders():
    """Lista todos os loaders disponiveis no cache e sistema."""
    loaders = []

    LOADER_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for f in LOADER_CACHE_DIR.iterdir():
        if f.suffix in (".elf", ".mbn", ".bin"):
            loaders.append(("cache", f))

    search_dirs = [
        Path("C:/Program Files (x86)/4uKey for Android/edl_exe/Loaders"),
        Path("C:/Program Files (x86)/4uKey for Android/edl_exe/Prog"),
        Path("C:/Program Files (x86)/MiFlash/Prog"),
    ]
    for d in search_dirs:
        if d.exists():
            for f in d.iterdir():
                if f.suffix in (".elf", ".mbn", ".bin"):
                    loaders.append(("system", f))

    return loaders


if __name__ == "__main__":
    # Teste rapido
    print("=== EDL Firehose FRP Remover ===\n")

    if check_edl_mode():
        print("[OK] Dispositivo em modo EDL detectado!")
        soc = input("SoC do dispositivo (ex: sm7125, sdm660, sm8250) [auto]: ").strip()
        if not soc:
            soc = None
        print("\nRemovendo FRP...")
        result = remove_frp_edl(soc_hint=soc)
        print(f"\nResultado: {'SUCESSO' if result else 'FALHA'}")
    else:
        print("[--] Nenhum dispositivo em modo EDL 9008")
        print("\nLoaders disponiveis:")
        for src, path in list_available_loaders():
            print(f"  [{src}] {path.name} ({path.stat().st_size} bytes)")
