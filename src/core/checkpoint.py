"""
RAVENA AIM — src/core/checkpoint.py
====================================
Sistema de checkpoints para fine-tuning.
Salva progresso durante treinamento e permite restauração.
"""

import os
import json
import csv
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Set

import logging

logger = logging.getLogger("ravena.checkpoint")

_PROJETO_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEFAULT_CHECKPOINT_DIR = os.path.join(_PROJETO_RAIZ, "checkpoints")


class CheckpointHandler:
    """Gerencia checkpoints durante o treinamento de ML."""

    def __init__(self, checkpoint_dir: str = None):
        self.checkpoint_dir = Path(checkpoint_dir or _DEFAULT_CHECKPOINT_DIR)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.processed_files_file = self.checkpoint_dir / "processed_files.txt"
        self.metrics_file = self.checkpoint_dir / "metrics_history.csv"
        self.state_file = self.checkpoint_dir / "training_state.json"

        self.epoch = 0
        self.batch = 0
        self.global_step = 0
        self.total_samples = 0
        self.last_loss = 0.0
        self.best_loss = float('inf')
        self.processed_files: Set[str] = set()

        if hasattr(signal, 'SIGUSR1'):
            signal.signal(signal.SIGUSR1, self._handle_save_signal)

        self._load_processed_files()

    def _handle_save_signal(self, signum, frame):
        logger.info("SIGUSR1 recebido - salvando checkpoint manual")
        self.save_checkpoint("manual_signal")

    def _load_processed_files(self):
        if self.processed_files_file.exists():
            with open(self.processed_files_file, 'r') as f:
                self.processed_files = set(line.strip() for line in f if line.strip())
            logger.info(f"{len(self.processed_files)} arquivos processados carregados")

    def save_processed_files(self):
        with open(self.processed_files_file, 'w') as f:
            for filepath in sorted(self.processed_files):
                f.write(f"{filepath}\n")

    def mark_file_processed(self, filepath: str):
        self.processed_files.add(str(filepath))
        self.save_processed_files()

    def save_metrics(self, metrics: Dict[str, Any]):
        """Salva métricas em CSV sem duplicatas."""
        existing_metrics = []
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r') as f:
                reader = csv.DictReader(f)
                existing_metrics = list(reader)

        current_step = str(self.global_step)
        already_exists = any(m.get('step') == current_step for m in existing_metrics)

        if not already_exists:
            file_exists = len(existing_metrics) > 0
            with open(self.metrics_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['epoch', 'batch', 'step', 'loss', 'accuracy', 'timestamp'])
                if not file_exists:
                    writer.writeheader()
                writer.writerow({
                    'epoch': self.epoch,
                    'batch': self.batch,
                    'step': self.global_step,
                    'loss': metrics.get('loss', 0),
                    'accuracy': metrics.get('accuracy', 0),
                    'timestamp': datetime.now().isoformat()
                })

    def save_checkpoint(self, reason: str = "auto") -> str:
        """Salva checkpoint completo do treinamento."""
        checkpoint_id = f"ckpt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        ckpt_path = self.checkpoint_dir / checkpoint_id
        ckpt_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"SALVANDO CHECKPOINT: {checkpoint_id} (motivo: {reason})")

        state = {
            "checkpoint_id": checkpoint_id,
            "timestamp": datetime.now().isoformat(),
            "epoch": self.epoch,
            "batch": self.batch,
            "global_step": self.global_step,
            "total_samples_processed": self.total_samples,
            "last_loss": self.last_loss,
            "best_loss": self.best_loss if self.best_loss != float('inf') else 0,
            "reason": reason,
            "pid": os.getpid(),
            "hostname": os.uname().nodename if hasattr(os, 'uname') else "windows"
        }

        with open(ckpt_path / "training_state.json", 'w') as f:
            json.dump(state, f, indent=2)

        if self.processed_files_file.exists():
            import shutil
            shutil.copy2(self.processed_files_file, ckpt_path / "processed_files.txt")

        if self.metrics_file.exists():
            import shutil
            shutil.copy2(self.metrics_file, ckpt_path / "metrics_history.csv")

        latest_file = self.checkpoint_dir / "latest.txt"
        with open(latest_file, 'w') as f:
            f.write(str(ckpt_path))

        logger.info(f"CHECKPOINT SALVO: {ckpt_path}")
        self._cleanup_old_checkpoints()
        return str(ckpt_path)

    def save_model_checkpoint(self, model=None, optimizer=None, tokenizer=None):
        """Salva estado do modelo (chamado pelo callback do Trainer)."""
        if model is not None:
            import torch
            model_path = self.checkpoint_dir / "model_checkpoint.pth"
            torch.save(model.state_dict(), model_path)
            logger.info(f"Modelo salvo: {model_path}")

        if optimizer is not None:
            import torch
            opt_path = self.checkpoint_dir / "optimizer_state.pth"
            torch.save(optimizer.state_dict(), opt_path)
            logger.info(f"Otimizador salvo: {opt_path}")

    def restore_from(self, checkpoint_path: str = None) -> bool:
        """Restaura estado de um checkpoint."""
        if checkpoint_path is None:
            checkpoint_path = self._find_latest_checkpoint()

        if checkpoint_path is None:
            logger.info("Nenhum checkpoint encontrado - iniciando do zero")
            return False

        ckpt_path = Path(checkpoint_path)
        if not ckpt_path.exists():
            logger.warning(f"Checkpoint não encontrado: {ckpt_path}")
            return False

        state_file = ckpt_path / "training_state.json"
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)

            self.epoch = state.get('epoch', 0)
            self.batch = state.get('batch', 0)
            self.global_step = state.get('global_step', 0)
            self.total_samples = state.get('total_samples_processed', 0)
            self.last_loss = state.get('last_loss', 0)
            self.best_loss = state.get('best_loss', float('inf'))

            logger.info(f"Estado restaurado: Epoch={self.epoch} Step={self.global_step} Loss={self.last_loss}")

        processed_file = ckpt_path / "processed_files.txt"
        if processed_file.exists():
            with open(processed_file) as f:
                self.processed_files = set(line.strip() for line in f if line.strip())
            logger.info(f"{len(self.processed_files)} arquivos restaurados")

        return True

    def _find_latest_checkpoint(self) -> Optional[str]:
        """Encontra o último checkpoint disponível."""
        latest_file = self.checkpoint_dir / "latest.txt"
        if latest_file.exists():
            with open(latest_file) as f:
                path = f.read().strip()
                if Path(path).exists():
                    return path

        ckpt_dirs = sorted(self.checkpoint_dir.glob("ckpt_*"))
        if ckpt_dirs:
            return str(ckpt_dirs[-1])

        return None

    def _cleanup_old_checkpoints(self, max_keep: int = 3):
        """Remove checkpoints antigos, mantendo apenas os N mais recentes."""
        ckpt_dirs = sorted(self.checkpoint_dir.glob("ckpt_*"))
        if len(ckpt_dirs) > max_keep:
            to_remove = ckpt_dirs[:len(ckpt_dirs) - max_keep]
            for d in to_remove:
                logger.info(f"Removendo checkpoint antigo: {d}")
                import shutil
                shutil.rmtree(d)

    def get_resume_info(self) -> Dict[str, Any]:
        """Retorna informações para retomar treinamento."""
        return {
            'start_epoch': self.epoch,
            'start_batch': self.batch,
            'start_step': self.global_step,
            'processed_files': self.processed_files
        }

    def get_checkpoint_dir(self) -> str:
        """Retorna o diretório de checkpoints."""
        return str(self.checkpoint_dir)
