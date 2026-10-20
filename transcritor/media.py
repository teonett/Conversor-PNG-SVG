"""Validação de arquivos locais e cópia de uploads."""

from contextlib import contextmanager
from pathlib import Path
import shutil
import tempfile

from .errors import TranscriptionError

EXTENSIONS = {".mp4", ".m4v", ".mov", ".mkv", ".webm", ".mp3", ".wav", ".m4a", ".flac", ".ogg"}


def validate_path(value: str | Path) -> Path:
    path = Path(str(value).strip().strip('"')).expanduser().resolve()
    if not path.is_file():
        raise TranscriptionError("Arquivo não encontrado. Informe o caminho completo do vídeo.")
    if path.suffix.lower() not in EXTENSIONS:
        raise TranscriptionError("Formato não aceito. Use MP4 ou outro formato listado na interface.")
    if path.stat().st_size == 0:
        raise TranscriptionError("O arquivo está vazio.")
    return path


def require_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        raise TranscriptionError(
            "FFmpeg não encontrado no PATH. Instale-o conforme o README e reabra o terminal."
        )


@contextmanager
def uploaded_media(upload):
    """Não usa o nome do upload como caminho; apaga a cópia mesmo após falha."""
    suffix = Path(upload.name).suffix.lower()
    if suffix not in EXTENSIONS:
        raise TranscriptionError("Formato de arquivo não aceito.")
    with tempfile.TemporaryDirectory(prefix="transcritor-") as folder:
        path = Path(folder) / f"entrada{suffix}"
        upload.seek(0)
        with path.open("wb") as destination:
            shutil.copyfileobj(upload, destination, length=1024 * 1024)
        yield validate_path(path)
