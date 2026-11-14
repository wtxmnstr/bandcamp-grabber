"""Встраивание текстовых тегов + обложки в аудиофайлы."""
from pathlib import Path

from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, ID3, TALB, TDRC, TIT2, TPE1, error as ID3Error
from mutagen.mp4 import MP4, MP4Cover


def _process_mp3(path: Path, track: dict, album: dict) -> None:
    try:
        tags = ID3(str(path))
    except ID3Error:
        tags = ID3()

    for frame in ("TIT2", "TPE1", "TALB", "TDRC", "APIC"):
        tags.delall(frame)

    tags.add(TIT2(encoding=3, text=track["title"]))
    tags.add(TPE1(encoding=3, text=album["artist"]))
    tags.add(TALB(encoding=3, text=album["album"]))
    if album.get("year"):
        tags.add(TDRC(encoding=3, text=str(album["year"])))
    if album.get("cover_data"):
        tags.add(APIC(encoding=3, mime=album["cover_mime"],
                      type=3, desc="Cover", data=album["cover_data"]))
    tags.save(str(path))


def _process_flac(path: Path, track: dict, album: dict) -> None:
    audio = FLAC(str(path))
    audio.delete()
    audio["title"] = track["title"]
    audio["artist"] = album["artist"]
    audio["album"] = album["album"]
    if album.get("year"):
        audio["date"] = str(album["year"])
    if album.get("cover_data"):
        pic = Picture()
        pic.type = 3
        pic.mime = album["cover_mime"]
        pic.desc = "Cover"
        pic.data = album["cover_data"]
        audio.add_picture(pic)
    audio.save()


def _process_m4a(path: Path, track: dict, album: dict) -> None:
    audio = MP4(str(path))
    audio["\xa9nam"] = [track["title"]]
    audio["\xa9ART"] = [album["artist"]]
    audio["\xa9alb"] = [album["album"]]
    if album.get("year"):
        audio["\xa9day"] = [str(album["year"])]
    if album.get("cover_data"):
        fmt = (MP4Cover.FORMAT_PNG if album["cover_mime"] == "image/png"
               else MP4Cover.FORMAT_JPEG)
        audio["covr"] = [MP4Cover(album["cover_data"], imageformat=fmt)]
    audio.save()


_HANDLERS = {".mp3": _process_mp3, ".flac": _process_flac, ".m4a": _process_m4a}


def embed_metadata_in_folder(folder: Path, tracks: list[dict], album: dict) -> int:
    """tracks: [{'track_num': int, 'title': str}]. album: общие поля."""
    # Подгружаем обложку один раз
    if not album.get("cover_data") and album.get("cover_path"):
        cp = Path(album["cover_path"])
        if cp.is_file():
            album["cover_data"] = cp.read_bytes()
            album["cover_mime"] = ("image/png" if cp.suffix.lower() == ".png"
                                   else "image/jpeg")

    by_num = {t["track_num"]: t for t in tracks}
    files = [f for f in sorted(folder.iterdir()) if f.suffix.lower() in _HANDLERS]
    ok = 0
    for f in files:
        # Имя файла: "01 - Title.mp3" - 1
        try:
            num = int(f.name.split(" - ", 1)[0])
        except (ValueError, IndexError):
            print(f"  ? {f.name}: не смог определить номер, пропуск")
            continue
        track = by_num.get(num)
        if not track:
            print(f"  ? {f.name}: нет трека #{num} в метаданных")
            continue
        try:
            _HANDLERS[f.suffix.lower()](f, track, album)
            print(f"  ✓ {f.name}")
            ok += 1
        except Exception as e:
            print(f"  ✗ {f.name}: {e}")
    print(f"\nТеги записаны: {ok}/{len(files)} файлов.")
    return ok