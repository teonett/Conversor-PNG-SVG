"""Validação estrutural e publicação segura do SVG gerado."""
import os
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def validate_svg(path: Path) -> int:
    root = ET.parse(path).getroot()
    if root.tag != f"{{{SVG_NS}}}svg":
        raise ValueError("A saída não tem uma raiz SVG válida.")
    box = [float(value) for value in root.get("viewBox", "").split()]
    if len(box) != 4 or box[2] <= 0 or box[3] <= 0:
        raise ValueError("A saída não tem dimensões válidas.")
    paths = []
    for element in root.iter():
        local_name = element.tag.rsplit("}", 1)[-1]
        if local_name not in {"svg", "title", "g", "path"}:
            raise ValueError(f"Elemento não permitido na saída: {local_name}")
        if any(key.rsplit("}", 1)[-1] == "href" for key in element.attrib):
            raise ValueError("A saída contém uma referência externa.")
        if local_name == "path" and element.get("d", "").strip():
            paths.append(element)
    if not paths:
        raise ValueError("A saída não contém formas vetoriais.")
    return len(paths)


def save_svg(root: ET.Element, output: Path, overwrite: bool) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".png-svg-", suffix=".svg", dir=output.parent)
    os.close(fd)
    temp = Path(temporary)
    try:
        ET.ElementTree(root).write(temp, encoding="utf-8", xml_declaration=True)
        count = validate_svg(temp)
        if overwrite:
            os.replace(temp, output)
        else:
            # Criação exclusiva e atômica; nunca substitui um destino existente.
            # NTFS e os sistemas de arquivos Linux usuais suportam hard links.
            os.link(temp, output)
        return count
    except FileExistsError:
        raise ValueError(f"O destino já existe: {output}. Ative sobrescrita para substituí-lo.") from None
    finally:
        temp.unlink(missing_ok=True)
