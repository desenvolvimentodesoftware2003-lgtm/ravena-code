import os
import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger("ravena.alimentacao.manifest")

class ManifestIngestao:
    def __init__(self, caminho_manifesto: str):
        self._caminho = caminho_manifesto
        self._dados: Dict[str, Any] = self._carregar()

    def _carregar(self) -> Dict[str, Any]:
        if os.path.exists(self._caminho):
            try:
                with open(self._caminho, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erro ao carregar manifesto: {e}")
        return {"versao": "1.0", "arquivos": {}}

    def _salvar(self):
        try:
            os.makedirs(os.path.dirname(self._caminho), exist_ok=True)
            with open(self._caminho, "w", encoding="utf-8") as f:
                json.dump(self._dados, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Erro ao salvar manifesto: {e}")

    def hash_arquivo(self, caminho: str) -> str:
        h = hashlib.sha256()
        with open(caminho, "rb") as f:
            for bloco in iter(lambda: f.read(65536), b""):
                h.update(bloco)
        return h.hexdigest()

    def hash_texto(self, texto: str) -> str:
        return hashlib.sha256(texto.encode("utf-8")).hexdigest()

    def verificar(self, caminho: str) -> Optional[Dict[str, Any]]:
        hash_atual = self.hash_arquivo(caminho)
        registros = self._dados.get("arquivos", {})
        caminho_norm = os.path.normpath(caminho)
        for caminho_reg, info in registros.items():
            if os.path.normpath(caminho_reg) == caminho_norm:
                if info.get("hash") == hash_atual:
                    return info
                break
        return None

    def registrar(self, caminho: str, tema: str, status: str,
                  itens_gerados: int = 0, motivo_pulo: Optional[str] = None,
                  metadados: Optional[Dict[str, Any]] = None):
        if os.path.isfile(caminho):
            hash_val = self.hash_arquivo(caminho)
        else:
            hash_val = self.hash_texto(caminho + tema + status + str(itens_gerados))
        self._dados.setdefault("arquivos", {})[caminho] = {
            "hash": hash_val,
            "tema": tema,
            "status": status,
            "motivo_pulo": motivo_pulo,
            "itens_gerados": itens_gerados,
            "timestamp": datetime.now().isoformat(),
            "metadados": metadados or {}
        }
        self._salvar()

    def registrar_itens(self, caminho: str, itens_gerados: int):
        registro = self._dados.get("arquivos", {}).get(caminho)
        if registro:
            registro["itens_gerados"] = itens_gerados
            registro["timestamp"] = datetime.now().isoformat()
            self._salvar()

    def estatisticas(self) -> Dict[str, Any]:
        arquivos = self._dados.get("arquivos", {})
        total = len(arquivos)
        por_status: Dict[str, int] = {}
        por_tema: Dict[str, int] = {}
        total_itens = 0
        for info in arquivos.values():
            s = info.get("status", "desconhecido")
            por_status[s] = por_status.get(s, 0) + 1
            t = info.get("tema", "desconhecido")
            por_tema[t] = por_tema.get(t, 0) + 1
            total_itens += info.get("itens_gerados", 0)
        return {
            "total_arquivos": total,
            "por_status": por_status,
            "por_tema": por_tema,
            "total_itens_gerados": total_itens,
            "versao_manifesto": self._dados.get("versao", "1.0")
        }

    def listar_pendentes(self) -> List[str]:
        return [
            caminho for caminho, info in self._dados.get("arquivos", {}).items()
            if info.get("status") == "pendente"
        ]

    def listar_ingeridos(self) -> List[str]:
        return [
            caminho for caminho, info in self._dados.get("arquivos", {}).items()
            if info.get("status") == "ingerido"
        ]
