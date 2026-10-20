"""Executa a conversão com limite de tempo e erros centralizados."""
import json
import os
from pathlib import Path
import subprocess
import sys


class ConversionError(Exception):
    """Erro de entrada, dependência, processo ou saída."""


def run_conversion(source, output, quality="alta", colors=8, overwrite=False, timeout=240):
    request = {"input_path": str(Path(source).expanduser().resolve()),
               "output_path": str(Path(output).expanduser().resolve()),
               "quality": quality, "colors": colors, "overwrite": overwrite}
    # pythonw é usado na interface Windows; o worker precisa de stdin/stdout.
    executable = Path(sys.executable)
    if executable.name.lower() == "pythonw.exe":
        executable = executable.with_name("python.exe")
    try:
        result = subprocess.run(
            [str(executable), "-m", "png_svg.worker"], input=json.dumps(request),
            text=True, encoding="utf-8", capture_output=True, timeout=timeout,
            cwd=Path(__file__).resolve().parent.parent,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except subprocess.TimeoutExpired:
        raise ConversionError(f"Tempo limite de {timeout} segundos excedido.") from None
    except OSError as error:
        raise ConversionError(f"Não foi possível iniciar a conversão: {error}") from error
    if result.returncode != 0:
        raise ConversionError(result.stderr.strip() or f"O motor encerrou com código {result.returncode}.")
    try:
        payload = json.loads(result.stdout)
        if not isinstance(payload, dict) or not isinstance(payload.get("ok"), bool):
            raise ValueError("Resposta inválida")
    except (ValueError, TypeError):
        raise ConversionError("O motor retornou uma resposta inválida.") from None
    if not payload["ok"]:
        raise ConversionError(payload.get("error", "Falha na conversão."))
    return payload
