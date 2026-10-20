"""Testes de mídia com FFmpeg real, sem download de modelos."""

import shutil
import subprocess

import pytest

from transcritor.engine import Options, transcribe
from transcritor.errors import TranscriptionError

pytestmark = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="FFmpeg não instalado")


def make_video(path, audio):
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
               "color=c=black:s=64x64:r=10:d=0.5"]
    if audio:
        command += ["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000:duration=0.5",
                    "-c:a", "aac", "-shortest"]
    command += ["-c:v", "mpeg4", str(path)]
    subprocess.run(command, check=True, capture_output=True)


def test_mp4_decodes_to_16khz(tmp_path):
    import whisper
    path = tmp_path / "vídeo com espaço.mp4"
    make_video(path, audio=True)
    audio = whisper.load_audio(str(path))
    assert 0.45 < len(audio) / 16000 < 0.7
    assert str(audio.dtype) == "float32"


def test_video_without_audio(tmp_path):
    path = tmp_path / "sem_audio.mp4"
    make_video(path, audio=False)
    with pytest.raises(TranscriptionError, match="ler o áudio"):
        transcribe(path, Options())


def test_corrupt_mp4(tmp_path):
    path = tmp_path / "corrompido.mp4"
    path.write_bytes(b"not an mp4 file")
    with pytest.raises(TranscriptionError, match="ler o áudio"):
        transcribe(path, Options())
