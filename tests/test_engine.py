from io import BytesIO
from pathlib import Path
from unittest.mock import Mock

import pytest

from transcritor import engine
from transcritor.engine import Options, transcribe
from transcritor.errors import TranscriptionError
from transcritor.media import uploaded_media, validate_path


@pytest.fixture
def media(tmp_path):
    path = tmp_path / "Vídeo com espaços.mp4"
    path.write_bytes(b"fixture")
    return path


def test_upload_cleanup_on_error():
    upload = BytesIO(b"video")
    upload.name = "../../reunião.mp4"
    copied = None
    with pytest.raises(RuntimeError):
        with uploaded_media(upload) as path:
            copied = path
            assert path.name == "entrada.mp4"
            assert path.read_bytes() == b"video"
            raise RuntimeError("failure")
    assert copied is not None and not copied.exists()


@pytest.mark.parametrize("name", ["missing.mp4", "bad.exe", "empty.mp4"])
def test_bad_paths(tmp_path, name):
    path = tmp_path / name
    if name != "missing.mp4":
        path.write_bytes(b"x" if name == "bad.exe" else b"")
    with pytest.raises(TranscriptionError):
        validate_path(path)


@pytest.mark.parametrize("kwargs", [{"model": "small.en"}, {"device": "bad"}, {"prompt": "x" * 401}])
def test_reject_bad_options(kwargs):
    with pytest.raises(TranscriptionError):
        Options(**kwargs)


def test_ffmpeg_missing(media, monkeypatch):
    monkeypatch.setattr("transcritor.media.shutil.which", lambda _: None)
    with pytest.raises(TranscriptionError, match="FFmpeg"):
        transcribe(media, Options())


def test_cpu_options_and_metadata(media, monkeypatch):
    import whisper
    import torch
    model = Mock()
    model.transcribe.return_value = {"text": " Olá! ", "language": "pt", "segments": []}
    monkeypatch.setattr(whisper, "load_audio", lambda _: [0.1] * 16000)
    loader = Mock(return_value=model)
    monkeypatch.setattr(whisper, "load_model", loader)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    result = transcribe(media, Options(model="base", prompt="Teotonio"))
    assert result["metadata"]["duration_seconds"] == 1
    assert result["metadata"]["device"] == "cpu"
    assert result["text"] == "Olá!"
    kwargs = model.transcribe.call_args.kwargs
    assert kwargs["language"] == "pt" and kwargs["task"] == "transcribe"
    assert kwargs["fp16"] is False and kwargs["initial_prompt"] == "Teotonio"
    assert kwargs["condition_on_previous_text"] is False


def test_cuda_unavailable(media, monkeypatch):
    import torch
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    with pytest.raises(TranscriptionError, match="CUDA indisponível"):
        transcribe(media, Options(device="cuda"))


def test_inference_lock(media):
    engine._INFERENCE_LOCK.acquire()
    try:
        with pytest.raises(TranscriptionError, match="andamento"):
            transcribe(media, Options())
    finally:
        engine._INFERENCE_LOCK.release()


def test_gpu_oom_and_lock_release(media, monkeypatch):
    import torch
    import whisper
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    cleanup = Mock()
    monkeypatch.setattr(torch.cuda, "empty_cache", cleanup)
    monkeypatch.setattr(whisper, "load_audio", lambda _: [0.1])
    monkeypatch.setattr(whisper, "load_model", Mock(side_effect=torch.cuda.OutOfMemoryError("OOM")))
    with pytest.raises(TranscriptionError, match="Memória da GPU"):
        transcribe(media, Options())
    cleanup.assert_called_once()
    assert not engine._INFERENCE_LOCK.locked()
