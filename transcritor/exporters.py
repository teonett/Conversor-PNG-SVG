"""Exportação UTF-8 e timestamps com arredondamento em milissegundos."""

import html
import json


def timestamp(seconds: float, separator: str = ",") -> str:
    milliseconds = max(0, round(float(seconds) * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{milliseconds:03d}"


def subtitles(result: dict, vtt: bool = False) -> str:
    blocks = []
    for segment in result.get("segments", []):
        text = " ".join(str(segment["text"]).split())
        if not text:
            continue
        start = max(0, round(float(segment["start"]) * 1000)) / 1000
        end = max(start + 0.001, round(float(segment["end"]) * 1000) / 1000)
        separator = "." if vtt else ","
        times = f"{timestamp(start, separator)} --> {timestamp(end, separator)}"
        blocks.append(f"{len(blocks) + 1}\n{times}\n{html.escape(text, quote=False)}")
    return ("WEBVTT\n\n" if vtt else "") + "\n\n".join(blocks) + ("\n" if blocks else "")


def exports(result: dict) -> dict[str, tuple[bytes, str]]:
    contents = {
        "txt": (result.get("text", "").strip() + "\n", "text/plain"),
        "srt": (subtitles(result), "application/x-subrip"),
        "vtt": (subtitles(result, vtt=True), "text/vtt"),
        "json": (json.dumps(result, ensure_ascii=False, indent=2), "application/json"),
    }
    return {extension: (text.encode("utf-8"), mime) for extension, (text, mime) in contents.items()}
