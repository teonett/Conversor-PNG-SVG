"""Processo isolado: recebe um pedido JSON e devolve um resultado JSON."""
import json
import sys


def main():
    try:
        from .vectorizer import convert
        request = json.load(sys.stdin)
        result = {"ok": True, **convert(**request)}
    except Exception as error:
        result = {"ok": False, "error": str(error) or type(error).__name__}
    sys.stdout.write(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
