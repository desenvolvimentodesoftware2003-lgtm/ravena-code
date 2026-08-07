"""
FINETUNE RAVENA
===============
Full fine-tuning do Qwen 2.5-1.5B-Instruct via HF Transformers.
Pipeline:
  1. Baixa modelo base da HF (se nao existir localmente)
  2. Carrega dataset formatado (JSONL com chat format)
  3. Fine-tune com Trainer + checkpoints automaticos
  4. Salva checkpoint em data/treino/checkpoint/
  5. Converte para GGUF (substitui modelo atual)
"""

import os
import sys
import json
import logging
import subprocess
import urllib.request
import argparse

_PROJETO_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJETO_RAIZ)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("finetune")

CAMINHO_MODELO_HF = os.path.join(_PROJETO_RAIZ, "data", "models", "qwen2.5-1.5b-instruct")
CAMINHO_DATASET = os.path.join(_PROJETO_RAIZ, "data", "treino", "treino_formatado.jsonl")
CAMINHO_CHECKPOINT = os.path.join(_PROJETO_RAIZ, "data", "treino", "checkpoint")
CAMINHO_CHECKPOINT_DIR = os.path.join(_PROJETO_RAIZ, "checkpoints")
CAMINHO_GGUF_ATUAL = os.path.join(_PROJETO_RAIZ, "data", "models", "qwen2.5-1.5b-instruct-q4_k_m.gguf")
CAMINHO_CONVERT_SCRIPT = os.path.join(_PROJETO_RAIZ, "data", "treino", "convert_hf_to_gguf.py")
CAMINHO_HISTORICO = os.path.join(_PROJETO_RAIZ, "data", "treino", "historico_finetune.json")


def baixar_modelo_hf():
    if os.path.exists(CAMINHO_MODELO_HF) and len(os.listdir(CAMINHO_MODELO_HF)) > 5:
        logger.info(f"Modelo HF ja existe em {CAMINHO_MODELO_HF}")
        return True

    logger.info(f"Baixando Qwen 2.5-1.5B-Instruct da HuggingFace...")
    from huggingface_hub import snapshot_download
    snapshot_download(
        repo_id="Qwen/Qwen2.5-1.5B-Instruct",
        local_dir=CAMINHO_MODELO_HF,
        local_dir_use_symlinks=False,
    )
    logger.info(f"Modelo baixado em {CAMINHO_MODELO_HF}")
    return True


def carregar_dataset():
    if not os.path.exists(CAMINHO_DATASET):
        logger.error(f"Dataset nao encontrado: {CAMINHO_DATASET}")
        logger.error("Execute scripts/preparar_treino.py primeiro")
        return None

    dados = []
    with open(CAMINHO_DATASET, "r", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            try:
                item = json.loads(linha)
                if "messages" in item:
                    dados.append(item)
            except json.JSONDecodeError:
                continue

    if not dados:
        logger.error("Dataset vazio ou invalido")
        return None

    logger.info(f"Dataset carregado: {len(dados)} exemplos")
    return dados


def formatar_chat(dados):
    """Converte usando o chat template do proprio tokenizer"""
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(CAMINHO_MODELO_HF)
    textos = []
    for item in dados:
        texto = tokenizer.apply_chat_template(
            item["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )
        textos.append(texto)
    return textos


def tokenizar(textos, tokenizer):
    entradas = tokenizer(
        textos,
        truncation=True,
        padding=False,
        max_length=256,
        return_tensors=None,
    )
    entradas["labels"] = [list(ids) for ids in entradas["input_ids"]]
    return entradas


def finetunar(dados, resume_from=None, checkpoint_dir=None):
    from transformers import (
        AutoTokenizer,
        AutoModelForCausalLM,
        Trainer,
        TrainingArguments,
        DataCollatorForLanguageModeling,
        TrainerCallback,
    )
    from datasets import Dataset
    from src.core.checkpoint import CheckpointHandler

    checkpoint_handler = CheckpointHandler(checkpoint_dir or CAMINHO_CHECKPOINT_DIR)

    if resume_from:
        logger.info(f"Restaurando checkpoint: {resume_from}")
        checkpoint_handler.restore_from(resume_from)

    tokenizer = AutoTokenizer.from_pretrained(CAMINHO_MODELO_HF)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    logger.info("Formatando dados com chat template...")
    textos = formatar_chat(dados)
    entradas = tokenizar(textos, tokenizer)
    dataset = Dataset.from_dict(entradas)

    total_batches = len(dados) // 1 + (1 if len(dados) % 1 else 0)

    historico = {
        "modelo": "Qwen/Qwen2.5-1.5B-Instruct",
        "status": "INICIANDO",
        "epocas": 1,
        "max_length": 256,
        "batch_size": 1,
        "gradient_accumulation": 4,
        "learning_rate": "2e-5",
        "warmup_steps": 10,
        "dtype": "auto",
        "dispositivo": "CPU",
        "dataset": CAMINHO_DATASET,
        "total_exemplos": len(dados),
        "total_batches": total_batches,
        "progresso_batches": [],
        "logs_loss": [],
        "erros_script": "NENHUM",
        "script": "finetune_ravena.py",
        "save_strategy": "steps",
        "checkpoint_interval": 10,
        "conversao_final": "GGUF q8_0",
        "processo_pid": os.getpid(),
    }
    _salvar_historico(historico)

    logger.info("Carregando modelo para fine-tuning...")
    model = AutoModelForCausalLM.from_pretrained(
        CAMINHO_MODELO_HF,
        dtype="auto",
    )

    class CheckpointCallback(TrainerCallback):
        def __init__(self, handler):
            self.handler = handler

        def on_save(self, args, state, control, **kwargs):
            self.handler.epoch = int(state.epoch) if state.epoch else 0
            self.handler.global_step = state.global_step
            self.handler.batch = state.global_step % total_batches if total_batches > 0 else 0
            ckpt_path = self.handler.save_checkpoint("auto_step")
            logger.info(f"Checkpoint salvo no step {state.global_step}: {ckpt_path}")

        def on_log(self, args, state, control, logs=None, **kwargs):
            if logs and "loss" in logs:
                historico["logs_loss"].append({
                    "loss": f"{logs['loss']:.4f}",
                    "grad_norm": f"{logs.get('grad_norm', 0):.2f}",
                    "learning_rate": f"{logs.get('learning_rate', 0):.2e}",
                    "epoch": f"{state.epoch:.4f}" if state.epoch else "0",
                })
                historico["progresso_batches"] = [f"{state.global_step}/{total_batches}"]
                _salvar_historico(historico)

    checkpoint_callback = CheckpointCallback(checkpoint_handler)

    args = TrainingArguments(
        output_dir=CAMINHO_CHECKPOINT,
        num_train_epochs=1,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        save_strategy="steps",
        save_steps=10,
        save_total_limit=3,
        logging_steps=5,
        learning_rate=2e-5,
        warmup_steps=10,
        fp16=False,
        bf16=False,
    )

    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=dataset,
        data_collator=data_collator,
        callbacks=[checkpoint_callback],
    )

    historico["status"] = "EM EXECUCAO"
    historico["processo_inicio"] = _agora()
    _salvar_historico(historico)

    logger.info("Iniciando fine-tuning (CPU, 1 epoca, checkpoint a cada 10 steps)...")
    if resume_from:
        trainer.train(resume_from_checkpoint=resume_from)
    else:
        trainer.train()

    historico["status"] = "CONCLUIDO"
    historico["processo_fim"] = _agora()
    _salvar_historico(historico)

    logger.info(f"Salvando modelo final em {CAMINHO_CHECKPOINT}")
    trainer.save_model(CAMINHO_CHECKPOINT)
    tokenizer.save_pretrained(CAMINHO_CHECKPOINT)

    checkpoint_handler.save_checkpoint("training_complete")

    return True


def _agora():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _salvar_historico(historico):
    os.makedirs(os.path.dirname(CAMINHO_HISTORICO), exist_ok=True)
    with open(CAMINHO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)


def baixar_convert_script():
    """Baixa o script de conversao HF->GGUF do llama.cpp"""
    if os.path.exists(CAMINHO_CONVERT_SCRIPT):
        return True

    url = "https://raw.githubusercontent.com/ggml-org/llama.cpp/master/convert_hf_to_gguf.py"
    logger.info(f"Baixando script de conversao de {url}")
    try:
        urllib.request.urlretrieve(url, CAMINHO_CONVERT_SCRIPT)
        logger.info(f"Script salvo em {CAMINHO_CONVERT_SCRIPT}")
        return True
    except Exception as e:
        logger.warning(f"Falha ao baixar script de conversao: {e}")
        return False


def converter_para_gguf():
    """Converte checkpoint HF para GGUF e substitui modelo atual"""
    if not os.path.exists(CAMINHO_CHECKPOINT):
        logger.warning(f"Checkpoint nao encontrado: {CAMINHO_CHECKPOINT}")
        return False

    if not baixar_convert_script():
        logger.warning(
            "Conversao GGUF indisponivel. "
            f"Checkpoint HF salvo em {CAMINHO_CHECKPOINT}. "
            "Para converter manualmente: "
            "python convert_hf_to_gguf.py --outfile modelo.gguf --outtype q8_0"
        )
        return False

    logger.info("Convertendo checkpoint HF para GGUF...")
    try:
        args = [
            sys.executable, CAMINHO_CONVERT_SCRIPT,
            CAMINHO_CHECKPOINT,
            "--outfile", CAMINHO_GGUF_ATUAL,
            "--outtype", "q8_0",
        ]
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"GGUF salvo em {CAMINHO_GGUF_ATUAL}")
            return True
        else:
            logger.error(f"Erro na conversao: {result.stderr[:200]}")
            return False
    except Exception as e:
        logger.error(f"Erro na conversao: {e}")
        return False


def validar_tamanho():
    """Verifica se o GGUF atualizado tem tamanho minimo"""
    if os.path.exists(CAMINHO_GGUF_ATUAL):
        tamanho = os.path.getsize(CAMINHO_GGUF_ATUAL)
        logger.info(f"Modelo GGUF atual: {tamanho / 1e6:.0f} MB")
        if tamanho > 10_000_000:
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Fine-tuning do Ravena LLM com checkpoints")
    parser.add_argument("--resume-from", help="Caminho do checkpoint para restaurar")
    parser.add_argument("--checkpoint-dir", default=CAMINHO_CHECKPOINT_DIR,
                        help="Diretorio de checkpoints (default: ./checkpoints)")
    parser.add_argument("--no-gguf", action="store_true",
                        help="Pular conversao GGUF no final")
    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info("FINETUNE RAVENA")
    logger.info(f"Checkpoint dir: {args.checkpoint_dir}")
    if args.resume_from:
        logger.info(f"Restaurando de: {args.resume_from}")
    logger.info("=" * 50)

    baixar_modelo_hf()

    dados = carregar_dataset()
    if not dados:
        return

    finetunar(dados, resume_from=args.resume_from, checkpoint_dir=args.checkpoint_dir)

    if not args.no_gguf:
        ok = converter_para_gguf()
        if ok:
            validar_tamanho()
            logger.info("Fine-tuning concluido e modelo GGUF atualizado!")
        else:
            logger.info("Fine-tuning concluido. Checkpoint salvo para conversao manual.")
    else:
        logger.info("Fine-tuning concluido. Conversao GGUF pulada.")

    logger.info("=" * 50)


if __name__ == "__main__":
    main()
