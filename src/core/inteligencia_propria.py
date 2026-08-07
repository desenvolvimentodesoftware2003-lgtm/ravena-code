import os
import json
import logging
import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

logger = logging.getLogger("ravena.inteligencia")

_PROJETO_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DIM_ENCODER = 768
VOCAB_SIZE = 10000
LR = 0.0001
BATCH_SIZE = 32

class EncoderRavena(nn.Module):
    def __init__(self, vocab_size: int = VOCAB_SIZE, dim_embed: int = DIM_ENCODER):
        super().__init__()
        self.dim_embed = dim_embed
        self.embedding = nn.EmbeddingBag(vocab_size, dim_embed, mode="mean", sparse=False)
        self.norm = nn.LayerNorm(dim_embed)
        self.proj = nn.Linear(dim_embed, dim_embed)
        self.dropout = nn.Dropout(0.1)

    def forward(self, tokens: torch.Tensor, offsets: torch.Tensor) -> torch.Tensor:
        x = self.embedding(tokens, offsets)
        x = self.norm(x)
        x = self.dropout(x)
        x = self.proj(x)
        x = F.normalize(x, p=2, dim=-1)
        return x

    def codificar_texto(self, texto: str, vocab: Dict[str, int]) -> np.ndarray:
        tokens = self._tokenizar_id(texto, vocab)
        if not tokens:
            return np.zeros(self.dim_embed, dtype=np.float32)
        with torch.no_grad():
            tensor = torch.tensor(tokens, dtype=torch.long)
            offsets = torch.tensor([0], dtype=torch.long)
            emb = self.forward(tensor, offsets)
            return emb.squeeze(0).numpy()

    def _tokenizar_id(self, texto: str, vocab: Dict[str, int]) -> List[int]:
        texto = texto.lower().strip()
        palavras = texto.split()[:256]
        ids = []
        for p in palavras:
            if p in vocab:
                ids.append(vocab[p])
            else:
                ids.append(vocab.get("<unk>", 1))
        return ids


@dataclass
class ExperienciaTreino:
    pergunta: str = ""
    raciocinio: str = ""
    resposta: str = ""
    confianca: float = 0.0
    fonte: str = ""
    authority_score: float = 0.0

    @classmethod
    def de_jsonl(cls, caminho: str) -> List["ExperienciaTreino"]:
        experiencias = []
        if not os.path.exists(caminho):
            return experiencias
        with open(caminho, "r", encoding="utf-8") as f:
            for linha in f:
                try:
                    d = json.loads(linha)
                    if d.get("pergunta") and d.get("resposta"):
                        experiencias.append(cls(
                            pergunta=d["pergunta"],
                            raciocinio=d.get("raciocinio", ""),
                            resposta=d["resposta"],
                            confianca=d.get("confianca", 0.0),
                            fonte=d.get("fonte", ""),
                            authority_score=d.get("authority_score", 0.0)
                        ))
                except json.JSONDecodeError:
                    continue
        return experiencias


class InteligenciaPropria:
    def __init__(self, dim_embed: int = DIM_ENCODER, device: str = "cpu"):
        self.device = device
        self.dim_embed = dim_embed
        self.vocab: Dict[str, int] = {"<pad>": 0, "<unk>": 1}
        self.vocab_rev: List[str] = ["<pad>", "<unk>"]
        self._proximo_id = 2

        self.encoder = EncoderRavena(VOCAB_SIZE, dim_embed)
        self.otimizador = torch.optim.AdamW(self.encoder.parameters(), lr=LR)
        self.treinado = False
        self._experiencias: List[ExperienciaTreino] = []

        logger.info(f"InteligenciaPropria inicializada (dim={dim_embed}, device={device})")

    def _adicionar_ao_vocab(self, texto: str):
        for palavra in texto.lower().split():
            if palavra not in self.vocab and len(self.vocab) < VOCAB_SIZE:
                self.vocab[palavra] = self._proximo_id
                self.vocab_rev.append(palavra)
                self._proximo_id += 1

    def carregar_dados(self, caminho_jsonl: str) -> int:
        caminho = caminho_jsonl if os.path.isabs(caminho_jsonl) else os.path.join(_PROJETO_RAIZ, caminho_jsonl)
        self._experiencias = ExperienciaTreino.de_jsonl(caminho)
        for exp in self._experiencias:
            self._adicionar_ao_vocab(exp.pergunta)
            self._adicionar_ao_vocab(exp.resposta)
            if exp.raciocinio:
                self._adicionar_ao_vocab(exp.raciocinio)
        logger.info(f"Carregados {len(self._experiencias)} dados, vocab: {len(self.vocab)}")
        return len(self._experiencias)

    def codificar(self, texto: str) -> np.ndarray:
        return self.encoder.codificar_texto(texto, self.vocab)

    def similaridade(self, texto_a: str, texto_b: str) -> float:
        emb_a = self.codificar(texto_a)
        emb_b = self.codificar(texto_b)
        cos_sim = np.dot(emb_a, emb_b) / (np.linalg.norm(emb_a) * np.linalg.norm(emb_b) + 1e-8)
        return float(cos_sim)

    def treinar(self, epochs: int = 10, lr: float = LR) -> Dict[str, Any]:
        if len(self._experiencias) < 2:
            logger.warning("Dados insuficientes para treino (min 2)")
            return {"status": "dados_insuficientes", "total": len(self._experiencias)}

        logger.info(f"Iniciando treino com {len(self._experiencias)} experiencias, {epochs} epochs")
        self.encoder.train()
        losses = []
        for epoch in range(epochs):
            loss_total = 0.0
            n_batches = 0
            for i in range(0, len(self._experiencias), BATCH_SIZE):
                batch = self._experiencias[i:i + BATCH_SIZE]
                perguntas_ids = []
                offsets = []
                offset_atual = 0
                for exp in batch:
                    tokens = self.encoder._tokenizar_id(exp.pergunta, self.vocab)
                    if not tokens:
                        tokens = [0]
                    perguntas_ids.extend(tokens)
                    offsets.append(offset_atual)
                    offset_atual += len(tokens)

                if not perguntas_ids:
                    continue

                input_tensor = torch.tensor(perguntas_ids, dtype=torch.long)
                offset_tensor = torch.tensor(offsets, dtype=torch.long)
                embeddings = self.encoder(input_tensor, offset_tensor)
                loss = embeddings.pow(2).mean()
                self.otimizador.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.encoder.parameters(), 1.0)
                self.otimizador.step()
                loss_total += loss.item()
                n_batches += 1

            loss_media = loss_total / max(n_batches, 1)
            losses.append(loss_media)
            if (epoch + 1) % 5 == 0 or epoch == 0:
                logger.info(f"  Epoch {epoch+1}/{epochs} — loss: {loss_media:.6f}")

        self.treinado = True
        logger.info(f"Treino concluido. Loss final: {losses[-1]:.6f}")
        return {"status": "ok", "epochs": epochs, "loss_final": losses[-1], "total": len(self._experiencias)}

    def buscar_com_encoder(self, pergunta: str, itens: List[Dict[str, Any]],
                           top_k: int = 5, similaridade_min: float = 0.3) -> List[Dict[str, Any]]:
        if not self.treinado or len(self.vocab) < 10:
            return []

        emb_pergunta = self.codificar(pergunta)
        resultados = []
        for item in itens:
            if item.get("estado_crenca") in ("contestado", "substituido", "stale"):
                continue
            texto_item = f"{item.get('pergunta', '')} {item.get('conteudo', '')}"
            emb_item = self.codificar(texto_item)
            sim = float(np.dot(emb_pergunta, emb_item) / (np.linalg.norm(emb_pergunta) * np.linalg.norm(emb_item) + 1e-8))
            if sim >= similaridade_min:
                resultados.append({
                    **item,
                    "similaridade_encoder": round(sim, 4),
                    "fonte_encoder": "inteligencia_propria"
                })
        resultados.sort(key=lambda x: x["similaridade_encoder"], reverse=True)
        return resultados[:top_k]

    def obter_estado(self) -> Dict[str, Any]:
        return {
            "treinado": self.treinado,
            "vocab_size": len(self.vocab),
            "dim_embed": self.dim_embed,
            "experiencias_carregadas": len(self._experiencias),
            "parametros_encoder": sum(p.numel() for p in self.encoder.parameters() if p.requires_grad)
        }


if __name__ == "__main__":
    import json, tempfile, uuid

    ip = InteligenciaPropria()

    dados_teste = [
        {"pergunta": "qual e a capital do brasil", "raciocinio": "Brasilia", "resposta": "Brasilia", "confianca": 0.95, "fonte": "usuario", "authority_score": 0.9},
        {"pergunta": "o que e python", "raciocinio": "linguagem interpretada", "resposta": "Python e linguagem", "confianca": 0.7, "fonte": "aprendizado", "authority_score": 0.7},
        {"pergunta": "capital da franca", "raciocinio": "Paris", "resposta": "Paris", "confianca": 0.9, "fonte": "usuario", "authority_score": 0.9},
        {"pergunta": "o que e fotossintese", "raciocinio": "energia luminosa", "resposta": "processo bioquimico", "confianca": 0.6, "fonte": "aprendizado", "authority_score": 0.65},
        {"pergunta": "qual a formula da agua", "raciocinio": "H2O", "resposta": "H2O", "confianca": 0.88, "fonte": "usuario", "authority_score": 0.88},
        {"pergunta": "quem descobriu o brasil", "raciocinio": "1500", "resposta": "Cabral", "confianca": 0.5, "fonte": "documento", "authority_score": 0.5},
    ]

    caminho_temp = os.path.join(tempfile.gettempdir(), f"treino_{uuid.uuid4().hex[:8]}.jsonl")
    with open(caminho_temp, "w", encoding="utf-8") as f:
        for d in dados_teste:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    print("=== CARREGAR DADOS ===")
    total = ip.carregar_dados(caminho_temp)
    print(f"  Experiencias: {total} | Vocab: {len(ip.vocab)}")

    print()
    print("=== TREINO ===")
    resultado = ip.treinar(epochs=20)
    print(f"  Status: {resultado['status']} | Loss final: {resultado.get('loss_final', 'N/A')}")

    print()
    print("=== TESTE DE SIMILARIDADE ===")
    pares = [
        ("qual e a capital do brasil", "capital do brasil"),
        ("o que e python", "python linguagem"),
        ("qual e a capital do brasil", "qual a formula da agua"),
        ("quem descobriu o brasil", "qual e a capital do brasil"),
    ]
    for a, b in pares:
        sim = ip.similaridade(a, b)
        print(f"  sim({a[:30]}..., {b[:30]}...) = {sim:.4f}")

    print()
    print("=== BUSCA COM ENCODER ===")
    itens_teste = [
        {"pergunta": "qual e a capital do brasil", "conteudo": "Brasilia", "estado_crenca": "ativo"},
        {"pergunta": "capital da franca", "conteudo": "Paris", "estado_crenca": "ativo"},
        {"pergunta": "o que e fotossintese", "conteudo": "processo bioquimico", "estado_crenca": "ativo"},
    ]
    resultados = ip.buscar_com_encoder("qual a capital do brasil", itens_teste)
    print(f"  Busca por 'qual a capital do brasil':")
    for r in resultados:
        print(f"    {r['pergunta'][:30]} -> {r['conteudo'][:30]} | sim: {r['similaridade_encoder']:.4f}")

    print()
    print("=== ESTADO ===")
    print(f"  {json.dumps(ip.obter_estado(), indent=2, ensure_ascii=False)}")

    os.remove(caminho_temp)
