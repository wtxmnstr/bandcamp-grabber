import re
from pathlib import Path


def sanitize_filename(name: str) -> str:
    """Убирает символы, недопустимые в именах файлов."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def find_cover(folder: Path) -> Path | None:
    """Ищет файл обложки в папке по типичным именам."""
    candidates = ("cover.jpg", "cover.jpeg", "cover.png",
                  "folder.jpg", "folder.jpeg", "folder.png",
                  "front.jpg", "front.png")
    for name in candidates:
        p = folder / name
        if p.is_file():
            return p
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        found = sorted(folder.glob(ext))
        if len(found) == 1:
            return found[0]
    return None