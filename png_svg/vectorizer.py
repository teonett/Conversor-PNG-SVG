"""Separação de cores e vetorização de máscaras com VTracer."""
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image
import vtracer

from .images import color_layers, load_png
from .svg_files import SVG_NS, save_svg

SCALES = {"rapida": 1, "equilibrada": 2, "alta": 4}


def convert(input_path: str, output_path: str, quality="alta", colors=8, overwrite=False) -> dict:
    source = Path(input_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()
    if quality not in SCALES or not 1 <= colors <= 32:
        raise ValueError("Qualidade ou quantidade de cores inválida.")
    if output.suffix.lower() != ".svg" or output == source:
        raise ValueError("Informe um destino .svg diferente da entrada.")
    if output.exists() and not overwrite:
        raise ValueError(f"O destino já existe: {output}")
    scale = SCALES[quality]
    rgba = load_png(source, scale)
    height, width = rgba.shape[:2]
    layers = color_layers(rgba, colors)
    root = ET.Element(f"{{{SVG_NS}}}svg", width=str(width), height=str(height),
                      viewBox=f"0 0 {width} {height}", preserveAspectRatio="xMidYMid meet")
    ET.SubElement(root, f"{{{SVG_NS}}}title").text = source.stem
    group = ET.SubElement(root, f"{{{SVG_NS}}}g", transform=f"scale({1 / scale})")
    with TemporaryDirectory(prefix="png-svg-") as folder:
        bitmap = Path(folder) / "mask.png"
        traced = Path(folder) / "mask.svg"
        for color, alpha in layers:
            # A ampliação facilita o ajuste dos contornos; não recupera detalhes perdidos.
            mask = Image.fromarray(alpha)
            if scale > 1:
                mask = mask.resize((width * scale, height * scale), Image.Resampling.LANCZOS)
            binary = np.where(np.asarray(mask) >= 128, 0, 255).astype("uint8")
            Image.fromarray(binary).save(bitmap)
            vtracer.convert_image_to_svg_py(
                str(bitmap), str(traced), colormode="binary", mode="spline",
                filter_speckle=0, corner_threshold=10, length_threshold=1,
                max_iterations=10, splice_threshold=20, path_precision=3,
            )
            for node in ET.parse(traced).getroot().iter():
                if node.tag.rsplit("}", 1)[-1] == "path" and node.get("d"):
                    # Copia somente geometria, sem imagens ou referências.
                    attributes = {k: node.get(k) for k in ("d", "transform", "fill-rule") if node.get(k)}
                    attributes["fill"] = "#" + "".join(f"{component:02X}" for component in color)
                    ET.SubElement(group, f"{{{SVG_NS}}}path", attributes)
    count = save_svg(root, output, overwrite)
    return {"output": str(output), "width": width, "height": height,
            "paths": count, "colors": len(layers), "bytes": output.stat().st_size}
