"""
RAVENA_MODEL — Núcleo de Inteligência v4.1.0
============================================
Suporta tres modos:
- gguf:    llama.cpp (CPU, rapido, quantizado)
- local:   HuggingFace Transformers (CPU, float32)
- oci:     Oracle Cloud Infrastructure (Qwen 3.5 / Kimi K2.5)
"""

import os
import logging
import time

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(): pass

logger = logging.getLogger("ravena.model")

# ── Dependencias opcionais ──
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    _HF_DISPONIVEL = True
except ImportError:
    _HF_DISPONIVEL = False

try:
    import oci
except ImportError:
    oci = None

try:
    import llama_cpp
    _LLAMA_DISPONIVEL = True
except ImportError:
    _LLAMA_DISPONIVEL = False

_PROJETO_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_CAMINHO_GGUF_PADRAO = os.path.join(
    _PROJETO_RAIZ, "data", "models", "qwen2.5-1.5b-instruct-q4_k_m.gguf"
)
_SYSTEM_PROMPT = (
    "Voce e a Ravena, uma assistente objetiva e tecnica. "
    "Seja direta. Responda apenas com a informacao solicitada, sem rodeios.\n\n"
    "FATOS IMPORTANTES:\n"
    "- O Brasil fica na America do Sul.\n"
    "- Quem descobriu o Brasil foi Pedro Alvares Cabral em 1500, nao Cristovao Colombo.\n"
    "- Agua ferve a 100 graus Celsius ao nivel do mar (Sim).\n"
    "- O orgao que bombeia o sangue no corpo humano e o coracao."
)


class RavenaModel:
    def __init__(self, modelo: str = "gguf", nome_modelo: str = None,
                 caminho_gguf: str = None):
        load_dotenv()
        self.modo = modelo
        self.nome_modelo = nome_modelo or _CAMINHO_GGUF_PADRAO
        self.caminho_gguf = caminho_gguf or (
            self.nome_modelo if self.nome_modelo.endswith(".gguf") else None
        )
        # fallback: se caminho_gguf foi passado, força modo gguf
        if self.caminho_gguf:
            self.modo = "gguf"

        self._tokenizer = None
        self._model = None
        self._llama = None
        self._oci_client = None
        self._oci_compartment = os.getenv("OCI_COMPARTMENT_ID")
        self._oci_qwen_endpoint = os.getenv("QWEN_ENDPOINT_ID")
        self._carregado = False
        logger.info(f"RavenaModel modo={self.modo} modelo={self.nome_modelo}")

    # ── Carregamento ──

    def carregar(self) -> bool:
        if self._carregado:
            return True
        if self.modo == "gguf":
            return self._carregar_gguf()
        elif self.modo == "local":
            return self._carregar_local()
        elif self.modo == "oci":
            return self._carregar_oci()
        logger.error(f"Modo desconhecido: {self.modo}")
        return False

    def _carregar_gguf(self) -> bool:
        if not _LLAMA_DISPONIVEL:
            logger.error("llama-cpp-python nao instalado")
            return False
        caminho = self.caminho_gguf
        if not caminho or not os.path.exists(caminho):
            logger.error(f"Arquivo GGUF nao encontrado: {caminho}")
            return False
        try:
            logger.info(f"Carregando GGUF: {caminho} ({os.path.getsize(caminho)/1e6:.0f} MB)")
            inicio = time.time()
            self._llama = llama_cpp.Llama(
                model_path=caminho,
                n_ctx=2048,
                n_threads=4,
                verbose=False,
            )
            logger.info(f"GGUF carregado em {time.time()-inicio:.1f}s")
            self._carregado = True
            return True
        except Exception as e:
            logger.error(f"Erro ao carregar GGUF: {e}")
            return False

    def _carregar_local(self) -> bool:
        if not _HF_DISPONIVEL:
            logger.error("transformers/torch nao instalados")
            return False
        try:
            logger.info(f"Carregando tokenizer: {self.nome_modelo}")
            self._tokenizer = AutoTokenizer.from_pretrained(self.nome_modelo)
            logger.info(f"Carregando modelo: {self.nome_modelo} (CPU, float32)")
            inicio = time.time()
            self._model = AutoModelForCausalLM.from_pretrained(
                self.nome_modelo, dtype=torch.float32
            )
            self._model.to("cpu")
            self._model.eval()
            logger.info(f"Modelo carregado em {time.time()-inicio:.1f}s")
            self._carregado = True
            return True
        except Exception as e:
            logger.error(f"Erro ao carregar modelo local: {e}")
            return False

    def _carregar_oci(self) -> bool:
        if oci is None:
            logger.error("SDK OCI nao instalado")
            return False
        try:
            config = oci.config.from_file()
            self._oci_client = oci.generative_ai_inference.GenerativeAiInferenceClient(config)
            self._carregado = True
            logger.info("Conexao OCI estabelecida")
            return True
        except Exception as e:
            logger.error(f"Erro conexao OCI: {e}")
            return False

    # ── Geração ──

    def gerar_resposta(self, prompt: str, max_tokens: int = 100, temperatura: float = 0.1) -> str:
        if self.modo == "gguf":
            return self._gerar_gguf(prompt, max_tokens, temperatura)
        elif self.modo == "local":
            return self._gerar_local(prompt, max_tokens, temperatura)
        elif self.modo == "oci":
            return self._gerar_oci(prompt, max_tokens, temperatura)
        return "Modo de modelo invalido."

    def _gerar_gguf(self, prompt: str, max_tokens: int, temperatura: float) -> str:
        if not self._carregado and not self.carregar():
            return "Erro: GGUF nao carregado."
        try:
            output = self._llama.create_chat_completion(
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperatura,
            )
            return output["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Erro geracao GGUF: {e}")
            return f"Erro ao gerar resposta: {e}"

    def _gerar_local(self, prompt: str, max_tokens: int, temperatura: float) -> str:
        if not self._carregado and not self.carregar():
            return "Erro: modelo nao carregado."
        try:
            messages = [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
            text = self._tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self._tokenizer(text, return_tensors="pt")
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    do_sample=temperatura > 0,
                    temperature=temperatura if temperatura > 0 else None,
                    pad_token_id=self._tokenizer.eos_token_id,
                )
            resposta = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
            if "assistant" in resposta:
                resposta = resposta.split("assistant")[-1].strip()
            return resposta if resposta else "[resposta vazia]"
        except Exception as e:
            logger.error(f"Erro geracao local: {e}")
            return f"Erro ao gerar resposta: {e}"

    def _gerar_oci(self, prompt: str, max_tokens: int, temperatura: float) -> str:
        if not self._carregado and not self.carregar():
            return "Erro: OCI nao conectado."
        try:
            system_prompt = _SYSTEM_PROMPT
            full_prompt = f"{system_prompt}\nUsuario: {prompt}\nRavena:"
            details = oci.generative_ai_inference.models.GenerateTextDetails(
                compartment_id=self._oci_compartment,
                endpoint_id=self._oci_qwen_endpoint,
                prompt=full_prompt,
                max_tokens=max_tokens,
                temperature=temperatura,
                top_p=0.9,
            )
            response = self._oci_client.generate_text(details)
            resposta = response.data.generated_text.strip()
            resposta = resposta.split("Usuario:")[0].split("Ravena:")[0].strip()
            return resposta if resposta else "Entendido. Como posso ajudar?"
        except Exception as e:
            logger.error(f"Erro geracao OCI: {e}")
            return "Erro de conexao com a nuvem."

    # ── Utilitários ──

    def esta_carregado(self) -> bool:
        return self._carregado

    def descarregar(self):
        self._tokenizer = None
        self._model = None
        self._llama = None
        self._carregado = False
        import gc
        gc.collect()
        logger.info("Modelo descarregado da memoria")


if __name__ == "__main__":
    import sys
    modo = sys.argv[1] if len(sys.argv) > 1 else "gguf"
    model = RavenaModel(modelo=modo)
    t0 = time.time()
    r = model.gerar_resposta("Qual a capital do Brasil?", max_tokens=30)
    print(f"Resposta: {r}")
    print(f"Tempo total: {time.time()-t0:.1f}s")
