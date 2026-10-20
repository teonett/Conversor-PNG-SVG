"""CLI: python -m transcritor video.mp4 --model small --device cpu."""

import argparse
from pathlib import Path
import sys

from .engine import MODELS, Options, transcribe
from .errors import TranscriptionError
from .exporters import exports


def main() -> int:
    parser = argparse.ArgumentParser(description="Transcreve vídeos localmente em português.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--model", choices=MODELS, default="small")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--output-dir", type=Path, default=Path("saida"))
    parser.add_argument("--prompt", default="", help="Nomes e termos de apoio (até 400 caracteres).")
    parser.add_argument("--word-timestamps", action="store_true")
    args = parser.parse_args()
    try:
        options = Options(args.model, args.device, args.prompt, args.word_timestamps)
        result = transcribe(args.input, options, print)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for extension, (data, _) in exports(result).items():
            target = args.output_dir / f"{args.input.stem}.{extension}"
            target.write_bytes(data)
            print(target.resolve())
    except (TranscriptionError, OSError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
