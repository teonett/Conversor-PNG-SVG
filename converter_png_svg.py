#!/usr/bin/env python3
"""Abra sem argumentos para usar a interface ou informe arquivos pela CLI."""
import argparse
from pathlib import Path
import sys

from png_svg.service import ConversionError, run_conversion


def main():
    parser = argparse.ArgumentParser(description="Converte PNG em formas vetoriais SVG, localmente.")
    parser.add_argument("arquivos", nargs="*", help="Um ou mais arquivos PNG")
    parser.add_argument("--saida", type=Path, help="Pasta de destino; padrão: pasta da entrada")
    parser.add_argument("--qualidade", choices=["rapida", "equilibrada", "alta"], default="alta")
    parser.add_argument("--cores", type=int, default=8, help="Limite da paleta: 1 a 32 (padrão: 8)")
    parser.add_argument("--sobrescrever", action="store_true", help="Substitui SVG existente após validação")
    parser.add_argument("--timeout", type=int, default=240, help="Tempo máximo por arquivo em segundos")
    args = parser.parse_args()
    if not 1 <= args.cores <= 32 or args.timeout < 1:
        parser.error("Informe de 1 a 32 cores e um timeout positivo.")
    if not args.arquivos:
        from png_svg.gui import launch
        launch()
        return 0
    failures = 0
    for name in args.arquivos:
        source = Path(name).expanduser().resolve()
        output = (args.saida.expanduser().resolve() if args.saida else source.parent) / (source.stem + ".svg")
        try:
            result = run_conversion(source, output, args.qualidade, args.cores,
                                    args.sobrescrever, args.timeout)
            print(f"OK: {result['output']} | {result['paths']} formas | {result['colors']} cores")
        except ConversionError as error:
            failures += 1
            print(f"ERRO: {source.name}: {error}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
