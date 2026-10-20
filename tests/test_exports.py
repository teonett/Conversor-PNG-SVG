import json

import pytest

from transcritor.exporters import exports, subtitles, timestamp


@pytest.mark.parametrize("seconds,expected", [
    (0, "00:00:00,000"), (59.9996, "00:01:00,000"),
    (3599.9996, "01:00:00,000"), (360000, "100:00:00,000"),
    (-1, "00:00:00,000"),
])
def test_timestamp_carries(seconds, expected):
    assert timestamp(seconds) == expected


def test_utf8_and_subtitle_formats():
    result = {"text": "Olá, prevenção!", "segments": [
        {"start": 59.9996, "end": 61.25, "text": " Olá,\n prevenção! "},
        {"start": 62, "end": 62, "text": "A < B & C"},
        {"start": 63, "end": 64, "text": "  "},
    ]}
    files = exports(result)
    assert files["txt"][0].decode() == "Olá, prevenção!\n"
    assert json.loads(files["json"][0]) == result
    assert "00:01:00,000 --> 00:01:01,250" in files["srt"][0].decode()
    assert "00:01:02,000 --> 00:01:02,001" in files["srt"][0].decode()
    assert "A &lt; B &amp; C" in files["srt"][0].decode()
    assert files["vtt"][0].decode().startswith("WEBVTT\n\n1\n00:01:00.000")
    assert "\n3\n" not in files["srt"][0].decode()


def test_empty_result():
    assert subtitles({"segments": []}) == ""
    assert subtitles({"segments": []}, vtt=True) == "WEBVTT\n\n"
