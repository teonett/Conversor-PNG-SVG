# Validação da entrega

Verificação executada em 18/10/2026, em Linux x64, com Python 3.11.17, Streamlit 1.50.0, openai-whisper 20250625 e PyTorch 2.14.1+cpu. O ambiente de verificação foi instalado com `uv`; a instalação documentada para Windows utiliza `venv` e `pip`.

## Resultados

- **24 testes automatizados passaram** (`python -m pytest -q`).
- Compilação dos módulos Python concluída sem erros.
- Verificação de compatibilidade das dependências concluída sem conflitos.
- Servidor Streamlit iniciado em `127.0.0.1:8501`; página inicial e endpoint de saúde responderam HTTP 200.
- Interface verificada com Streamlit AppTest: carregamento, opções, botão desabilitado sem entrada, erro de caminho inexistente, exibição de resultado, quatro downloads e limpeza de sessão.
- FFmpeg real: MP4 com áudio decodificado em 16 kHz; vídeos sem áudio e arquivos corrompidos geraram mensagens de erro tratadas, antes de carregar um modelo.
- Exportação: UTF-8, JSON válido, formatos SRT/VTT, avanço correto dos milissegundos para minuto/hora e trechos vazios.
- Temporários: cópia de upload com nome controlado e exclusão mesmo após falha.
- Integração simulada: seleção de CPU, idioma `pt`, tarefa `transcribe`, CUDA indisponível, memória insuficiente e bloqueio de transcrições simultâneas.

## Transcrição com o modelo real

Foi criada uma amostra de fala sintética em português brasileiro com eSpeak NG, convertida para vídeo MP4 com áudio AAC. Duração decodificada: aproximadamente **7,66 segundos**. O sintetizador foi utilizado somente na verificação e não é dependência da aplicação.

A CLI real foi executada com os modelos oficiais **tiny** e **small**, ambos em **CPU**, gerando TXT, SRT, VTT e JSON. No teste com `small`, foi habilitada a marcação por palavra; o JSON continha os tempos por palavra.

Frase utilizada e reconhecida pelo modelo `small`:

> Olá, bom dia. Este é um teste de transcrição de vídeo em português. A tecnologia ajuda as pessoas a trabalhar melhor.

Essa amostra confirma o funcionamento do fluxo completo; não constitui um estudo de precisão ou de desempenho. O modelo `tiny` apresentou erros na mesma amostra, reforçando a necessidade de escolher o modelo e revisar o resultado.

## Limites da verificação

Não houve execução em Windows, GPU NVIDIA/CUDA ou macOS. Os scripts `.bat` foram revisados, mas precisam ser executados na máquina Windows do usuário para validação final. O caminho de GPU foi testado com simulações de disponibilidade e erro de memória, sem uma GPU física.

A instalação direta do GitHub é oferecida como alternativa e não foi executada; foi validada a distribuição oficial `openai-whisper` com versão fixa. Vídeos longos, uploads próximos do limite de 1.024 MB, outros codecs e a precisão em gravações reais precisam ser avaliados com os arquivos do usuário.

Os testes automatizados podem ser repetidos sem baixar pesos. Os modelos, ambientes virtuais e arquivos de verificação não fazem parte do ZIP.
