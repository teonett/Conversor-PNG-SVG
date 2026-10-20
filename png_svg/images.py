"""Leitura de PNG e identificação da paleta visível."""
from pathlib import Path
import warnings

import numpy as np
from PIL import Image

MAX_PIXELS = 20_000_000
MAX_SCALED_PIXELS = 32_000_000


def load_png(path: Path, scale: int) -> np.ndarray:
    if not path.is_file():
        raise ValueError(f"Arquivo não encontrado: {path}")
    if path.suffix.lower() != ".png":
        raise ValueError("A entrada deve ter extensão .png.")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(path) as image:
            if image.format != "PNG":
                raise ValueError("O conteúdo do arquivo não é um PNG.")
            if getattr(image, "n_frames", 1) != 1:
                raise ValueError("PNG animado não é suportado; exporte um único quadro.")
            w, h = image.size
            if w * h > MAX_PIXELS or w * h * scale * scale > MAX_SCALED_PIXELS:
                raise ValueError("Imagem acima do limite de pixels. Reduza a qualidade ou a resolução.")
            image.verify()
        with Image.open(path) as image:
            image.load()
            return np.array(image.convert("RGBA"))


def color_layers(rgba: np.ndarray, max_colors: int) -> list:
    """Quantiza cores e mantém a cor original mais frequente em cada grupo."""
    visible = rgba[:, :, 3] >= 128
    if not visible.any():
        raise ValueError("A imagem não contém pixels com opacidade igual ou superior a 50%.")
    rgb = rgba[:, :, :3]
    # Pixels opacos evitam transformar franjas de antialias em cores extras.
    # Uma arte inteiramente semitransparente usa a região visível como alternativa.
    opaque = rgba[:, :, 3] == 255
    sample = rgb[opaque] if opaque.any() else rgb[visible]
    # Amostragem determinística limita memória durante a descoberta das cores.
    sample = sample[::max(1, (len(sample) + 199_999) // 200_000)]
    quantized = Image.fromarray(sample.reshape(1, -1, 3)).quantize(
        colors=max_colors, method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )
    labels = np.array(quantized).reshape(-1)
    candidates = []
    for count, index in quantized.getcolors():
        members = sample[labels == index]
        colors, counts = np.unique(members, axis=0, return_counts=True)
        modal = colors[counts.argmax()]
        candidates.append((count, tuple(int(x) for x in modal)))
    palette = []
    minimum_count = max(1, len(sample) // 1000)
    for count, color in sorted(candidates, key=lambda x: x[0], reverse=True):
        if palette and count < minimum_count:
            continue
        if all(sum((a - b) ** 2 for a, b in zip(color, other)) > 144 for other in palette):
            palette.append(color)
    pixels = rgb.reshape(-1, 3)
    assignments = np.empty(len(pixels), dtype=np.uint8)
    for start in range(0, len(pixels), 131_072):
        block = pixels[start:start + 131_072].astype(np.int32)
        distances = np.stack([np.sum((block - c) ** 2, axis=1) for c in palette], axis=1)
        assignments[start:start + len(block)] = distances.argmin(axis=1)
    assignments = assignments.reshape(visible.shape)
    layers = []
    for index, color in enumerate(palette):
        selected = assignments == index
        if (selected & visible).any():
            layers.append((color, np.where(selected, rgba[:, :, 3], 0).astype("uint8")))
    return layers
