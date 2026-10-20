import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw

from png_svg.service import ConversionError, run_conversion
from png_svg.svg_files import SVG_NS, validate_svg
from png_svg.vectorizer import convert


class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.png = self.folder / "ação branca.png"
        self.svg = self.folder / "ação branca.svg"
        im = Image.new("RGBA", (96, 48), (0, 0, 0, 0))
        draw = ImageDraw.Draw(im)
        draw.rectangle((5, 5, 35, 40), fill="white")
        draw.rectangle((50, 5, 88, 40), fill=(243, 146, 0, 255))
        im.save(self.png)

    def test_white_and_orange_remain_vector_colors(self):
        result = convert(str(self.png), str(self.svg))
        root = ET.parse(self.svg).getroot()
        paths = root.findall(f".//{{{SVG_NS}}}path")
        self.assertEqual({p.get("fill") for p in paths}, {"#FFFFFF", "#F39200"})
        self.assertEqual(root.get("viewBox"), "0 0 96 48")
        self.assertEqual(result["colors"], 2)
        self.assertFalse(root.findall(f".//{{{SVG_NS}}}image"))

    def test_translucent_edge_tint_does_not_add_a_color(self):
        im = Image.open(self.png).convert("RGBA")
        im.putpixel((4, 5), (217, 222, 243, 200))
        im.save(self.png)
        result = convert(str(self.png), str(self.svg))
        self.assertEqual(result["colors"], 2)

    def test_existing_output_is_preserved_by_default(self):
        self.svg.write_bytes(b"original")
        with self.assertRaises(ValueError):
            convert(str(self.png), str(self.svg))
        self.assertEqual(self.svg.read_bytes(), b"original")

    def test_failed_overwrite_preserves_previous_output(self):
        self.svg.write_bytes(b"original")
        self.png.write_bytes(b"corrupt PNG")
        with self.assertRaises(Exception):
            convert(str(self.png), str(self.svg), overwrite=True)
        self.assertEqual(self.svg.read_bytes(), b"original")
        self.assertFalse(list(self.folder.glob(".png-svg-*")))

    def test_valid_overwrite_replaces_output(self):
        self.svg.write_bytes(b"original")
        convert(str(self.png), str(self.svg), overwrite=True)
        self.assertGreater(validate_svg(self.svg), 0)

    def test_invalid_xml_cannot_replace_output(self):
        self.svg.write_bytes(b"original")
        with patch("png_svg.svg_files.validate_svg", side_effect=ValueError("inválido")):
            with self.assertRaises(ValueError):
                convert(str(self.png), str(self.svg), overwrite=True)
        self.assertEqual(self.svg.read_bytes(), b"original")
        self.assertFalse(list(self.folder.glob(".png-svg-*")))

    def test_directory_named_png_is_rejected(self):
        folder = self.folder / "pasta.png"
        folder.mkdir()
        with self.assertRaises(ValueError):
            convert(str(folder), str(self.svg))

    def test_renamed_non_png_is_rejected(self):
        Image.new("RGB", (10, 10), "white").save(self.png, format="JPEG")
        with self.assertRaises(ValueError):
            convert(str(self.png), str(self.svg))

    def test_fully_transparent_png_is_rejected(self):
        Image.new("RGBA", (10, 10), (0, 0, 0, 0)).save(self.png)
        with self.assertRaises(ValueError):
            convert(str(self.png), str(self.svg))

    def test_apng_is_rejected(self):
        frame = Image.new("RGBA", (10, 10), "white")
        frame.save(self.png, save_all=True, append_images=[Image.new("RGBA", (10, 10), "red")], duration=100)
        with self.assertRaises(ValueError):
            convert(str(self.png), str(self.svg))

    def test_scaled_pixel_limit_is_enforced(self):
        with patch("png_svg.images.MAX_SCALED_PIXELS", 100):
            with self.assertRaises(ValueError):
                convert(str(self.png), str(self.svg))

    def test_embedded_image_svg_is_rejected(self):
        self.svg.write_text(f'<svg xmlns="{SVG_NS}" viewBox="0 0 10 10"><image href="x.png"/></svg>')
        with self.assertRaises(ValueError):
            validate_svg(self.svg)

    def test_unicode_paths_work_through_real_worker(self):
        result = run_conversion(self.png, self.svg, quality="equilibrada")
        self.assertTrue(result["ok"])
        self.assertGreater(validate_svg(self.svg), 0)

    def test_timeout_is_reported(self):
        with patch("png_svg.service.subprocess.run", side_effect=subprocess.TimeoutExpired("worker", 1)):
            with self.assertRaisesRegex(ConversionError, "Tempo limite"):
                run_conversion(self.png, self.svg, timeout=1)

    def test_cli_returns_failure_for_invalid_input(self):
        self.png.write_bytes(b"invalid")
        root = Path(__file__).resolve().parent.parent
        result = subprocess.run([sys.executable, str(root / "converter_png_svg.py"), str(self.png)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.svg.exists())


if __name__ == "__main__":
    unittest.main()
