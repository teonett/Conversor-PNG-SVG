"""Interface web local. Inicie com: python -m streamlit run app.py."""

from contextlib import nullcontext
from pathlib import Path
import shutil
import traceback

import streamlit as st

from transcritor.engine import MODELS, Options, transcribe
from transcritor.errors import TranscriptionError
from transcritor.exporters import exports, timestamp
from transcritor.media import EXTENSIONS, uploaded_media

st.set_page_config(page_title="Transcritor local · Whisper", page_icon="🎙️", layout="wide")
st.title("🎙️ Transcritor local")
st.write("Transforme a fala do seu vídeo em texto e legendas em português.")
st.caption("Whisper oficial • processamento no seu computador • sem chave de API")

with st.sidebar:
    st.header("Configuração")
    model = st.selectbox("Modelo", MODELS, index=2)
    st.caption("small é um bom ponto de partida. base/tiny consomem menos recursos; modelos maiores podem melhorar a precisão.")
    device = st.selectbox("Processamento", ["auto", "cpu", "cuda"], format_func={
        "auto": "Automático (CUDA quando disponível)", "cpu": "Processador (CPU)",
        "cuda": "GPU NVIDIA (CUDA)",
    }.get)
    words = st.checkbox("Marcação por palavra no JSON", value=False)
    prompt = st.text_area("Nomes e termos de apoio (opcional)", max_chars=400,
                          placeholder="Ex.: Caixa Vida e Previdência, Streamlit, Teotonio")
    st.caption("Use apenas vocabulário presente no vídeo. Esse campo pode influenciar o texto reconhecido.")
    st.divider()
    if shutil.which("ffmpeg"):
        st.success("FFmpeg encontrado")
    else:
        st.error("Instale o FFmpeg e reabra o terminal. Veja o README.")
    st.caption("O primeiro uso de cada modelo exige internet. Depois do download, a transcrição funciona offline.")

mode = st.radio("Como deseja abrir o arquivo?", ["Enviar arquivo", "Caminho no computador"], horizontal=True)
upload = None
local_path = ""
if mode == "Enviar arquivo":
    upload = st.file_uploader("Vídeo ou áudio", type=sorted(e.lstrip(".") for e in EXTENSIONS))
    st.caption("Até 1.024 MB por upload. Para arquivos maiores ou menor consumo de RAM, use o caminho no computador.")
else:
    local_path = st.text_input("Caminho completo", placeholder=r"C:\Videos\reuniao.mp4")
    st.caption("O arquivo deve estar na máquina onde esta aplicação está executando.")

ready = upload is not None or bool(local_path.strip())
if st.button("Transcrever em português", type="primary", disabled=not ready):
    st.session_state.pop("result", None)
    st.session_state.pop("source_name", None)
    try:
        with st.status("Preparando transcrição…", expanded=True) as status:
            def notify(message):
                status.update(label=message)
                st.write(message)

            options = Options(model, device, prompt, words)
            source = uploaded_media(upload) if upload is not None else nullcontext(local_path)
            with source as path:
                result = transcribe(path, options, notify)
            name = upload.name if upload is not None else Path(local_path.strip().strip('"')).name
            result["metadata"]["source_name"] = name
            st.session_state["result"] = result
            st.session_state["source_name"] = name
            status.update(label="Transcrição concluída", state="complete", expanded=False)
    except Exception as exc:
        st.error(str(exc) if isinstance(exc, TranscriptionError) else "Falha inesperada. Consulte os detalhes abaixo.")
        with st.expander("Detalhes técnicos"):
            st.code("".join(traceback.format_exception(exc)), language="text")

if "result" in st.session_state:
    result = st.session_state["result"]
    meta = result["metadata"]
    st.subheader("Última transcrição concluída")
    st.write(f"Arquivo: **{meta['source_name']}** · Modelo: **{meta['model']}** · Dispositivo: **{meta['device']}**")
    left, right = st.columns(2)
    left.metric("Duração do áudio", timestamp(meta["duration_seconds"], ".").split(".")[0])
    right.metric("Tempo de processamento", f"{meta['elapsed_seconds']:.1f} s")
    if not result["text"]:
        st.warning("Nenhuma fala foi reconhecida. Confira o áudio e tente outro modelo.")
    st.text_area("Texto reconhecido", result["text"], height=300, disabled=True, key="transcript_" + str(meta["elapsed_seconds"]))
    columns = st.columns(4)
    for column, (extension, (data, mime)) in zip(columns, exports(result).items()):
        column.download_button(f"Baixar {extension.upper()}", data=data, mime=mime,
                               file_name=f"{Path(meta['source_name']).stem}.{extension}")
    with st.expander("Trechos com marcação de tempo"):
        st.dataframe([{"Início": timestamp(s["start"], "."), "Fim": timestamp(s["end"], "."),
                       "Texto": s["text"].strip()} for s in result.get("segments", [])],
                     hide_index=True, use_container_width=True)
    if st.button("Limpar resultado"):
        st.session_state.pop("result", None)
        st.session_state.pop("source_name", None)
        st.rerun()

st.divider()
st.caption("Revise nomes próprios, números e trechos com ruído. O Whisper reconhece fala; não extrai textos exibidos na imagem nem identifica automaticamente os participantes.")
