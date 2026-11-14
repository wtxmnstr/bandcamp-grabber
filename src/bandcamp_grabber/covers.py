from pathlib import Path

from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, ID3, error as ID3Error
from mutagen.mp4 import MP4, MP4Cover


def _process_mp3(path: Path, data: bytes, mime: str) -> None:
    try:
        tags = ID3(str(path))
    except ID3Error:
        tags = ID3()
    tags.delall("APIC")
    tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=data))
    tags.save(str(path))


def _process_flac(path: Path, data: bytes, mime: str) -> None:
    audio = FLAC(str(path))
    audio.clear_pictures()
    pic = Picture()
    pic.type = 3
    pic.mime = mime
    pic.desc = "Cover"
    pic.data = data
    audio.add_picture(pic)
    audio.save()


def _process_m4a(path: Path, data: bytes, mime: str) -> None:
    audio = MP4(str(path))
    fmt = MP4Cover.FORMAT_PNG if mime == "image/png" else MP4Cover.FORMAT_JPEG
    audio["covr"] = [MP4Cover(data, imageformat=fmt)]
    audio.save()


_HANDLERS = {".mp3": _process_mp3, ".flac": _process_flac, ".m4a": _process_m4a}


def embed_cover_in_folder(folder: Path, cover_path: Path) -> int:
    """Встраивает обложку во все аудио находящиеся в папке.
    Возвращает число обновлённых файлов."""
    mime = "image/png" if cover_path.suffix.lower() == ".png" else "image/jpeg"
    data = cover_path.read_bytes()

    files = [f for f in sorted(folder.iterdir())
             if f.suffix.lower() in _HANDLERS]
    if not files:
        print("Аудиофайлы в папке не найдены.")
        return 0

    ok = 0
    for f in files:
        try:
            _HANDLERS[f.suffix.lower()](f, data, mime)
            print(f"  ✓ {f.name}")
            ok += 1
        except Exception as e:
            print(f"  ✗ {f.name}: {e}")
    print(f"\nОбложка встроена: {ok}/{len(files)} файлов.")
    return ok