"""Integração com openai/whisper; nenhum serviço externo de transcrição."""

from dataclasses import dataclass
import gc
from pathlib import Path
import threading
import time
from typing import Callable

from .errors import TranscriptionError
from .media import require_ffmpeg, validate_path

MODELS = ("tiny", "base", "small", "medium", "large-v3", "turbo")
MODEL_DIR = Path(__file__).resolve().parents[1] / "modelos"
_INFERENCE_LOCK = threading.Lock()


@dataclass(frozen=True)
class Options:
    model: str = "small"
    device: str = "auto"
    prompt: str = ""
    word_timestamps: bool = False

    def __post_init__(self):
        if self.model not in MODELS:
            raise TranscriptionError("Selecione um modelo multilíngue válido.")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise TranscriptionError("Dispositivo inválido: use auto, cpu ou cuda.")
        if len(self.prompt) > 400:
            raise TranscriptionError("O vocabulário de apoio deve ter até 400 caracteres.")


def transcribe(path: str | Path, options: Options, notify: Callable[[str], None] | None = None) -> dict:
    path = validate_path(path)
    require_ffmpeg()
    notify = notify or (lambda _: None)
    if not _INFERENCE_LOCK.acquire(blocking=False):
        raise TranscriptionError("Já existe uma transcrição em andamento. Aguarde a conclusão.")
    try:
        return _run(path, options, notify)
    except TranscriptionError:
        raise
    except Exception as exc:
        raise TranscriptionError(
            "Não foi possível concluir. Verifique espaço em disco e memória; "
            "tente um modelo menor. Consulte os detalhes técnicos."
        ) from exc
    finally:
        _INFERENCE_LOCK.release()


def _run(path: Path, options: Options, notify: Callable[[str], None]) -> dict:
    try:
        import torch
        import whisper
    except ImportError as exc:
        raise TranscriptionError("Dependências ausentes. Execute instalar_windows.bat ou instale requirements.txt.") from exc

    device = "cuda" if options.device == "auto" and torch.cuda.is_available() else options.device
    if device == "auto":
        device = "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise TranscriptionError("CUDA indisponível neste PyTorch. Use CPU ou instale o PyTorch com CUDA.")
    model = audio = None
    started = time.perf_counter()
    try:
        notify("Extraindo e preparando o áudio do arquivo…")
        try:
            audio = whisper.load_audio(str(path))
        except (RuntimeError, OSError) as exc:
            raise TranscriptionError(
                "Não foi possível ler o áudio. O vídeo pode estar corrompido, sem faixa de áudio "
                "ou usar um codec indisponível no FFmpeg."
            ) from exc
        if len(audio) == 0:
            raise TranscriptionError("O arquivo não contém áudio decodificável.")
        duration = len(audio) / 16000
        notify(f"Carregando modelo {options.model} em {device}. No primeiro uso haverá download…")
        try:
            model = whisper.load_model(options.model, device=device, download_root=str(MODEL_DIR))
        except torch.cuda.OutOfMemoryError:
            raise
        except Exception as exc:
            raise TranscriptionError(
                "Falha ao carregar o modelo. No primeiro uso, verifique a internet e o espaço "
                "na pasta modelos. Se o download estiver incompleto, remova somente o .pt afetado e tente novamente."
            ) from exc
        notify(f"Transcrevendo {duration / 60:.1f} minuto(s) em português. Aguarde…")
        result = model.transcribe(
            audio, language="pt", task="transcribe", fp16=device == "cuda", verbose=None,
            initial_prompt=options.prompt.strip() or None,
            word_timestamps=options.word_timestamps,
            condition_on_previous_text=False,
        )
        result["text"] = result.get("text", "").strip()
        result["metadata"] = {
            "source_name": path.name, "model": options.model, "device": device,
            "language_requested": "pt", "locale": "pt-BR", "duration_seconds": duration,
            "elapsed_seconds": round(time.perf_counter() - started, 2),
            "engine": "openai-whisper", "word_timestamps": options.word_timestamps,
        }
        return result
    except torch.cuda.OutOfMemoryError as exc:
        raise TranscriptionError(
            "Memória da GPU insuficiente. Selecione small/base, feche outros programas "
            "que usam a GPU ou escolha CPU e tente novamente."
        ) from exc
    finally:
        del model, audio
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()
