from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_initial_ui_and_local_path_error():
    app = AppTest.from_file(str(APP)).run(timeout=30)
    assert not app.exception
    assert app.selectbox[0].value == "small"
    assert app.button[0].disabled
    app.radio[0].set_value("Caminho no computador").run()
    app.text_input[0].set_value("/arquivo/nao-existe.mp4").run()
    assert not app.button[0].disabled
    app.button[0].click().run()
    assert not app.exception
    assert any("não encontrado" in x.value for x in app.error)


def test_result_and_clear(monkeypatch):
    def fake_transcribe(path, options, notify):
        notify("Teste de interface")
        return {"text": "Olá, Brasil!", "segments": [{"start": 0, "end": 1, "text": "Olá, Brasil!"}],
                "metadata": {"source_name": "", "model": options.model, "device": "cpu",
                             "duration_seconds": 1, "elapsed_seconds": 0.5}}
    monkeypatch.setattr("transcritor.engine.transcribe", fake_transcribe)
    app = AppTest.from_file(str(APP)).run(timeout=30)
    app.radio[0].set_value("Caminho no computador").run()
    app.text_input[0].set_value("video.mp4").run()
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state["result"]["text"] == "Olá, Brasil!"
    assert len(app.get("download_button")) == 4
    app.button[-1].click().run()
    assert not app.exception
    assert "result" not in app.session_state
