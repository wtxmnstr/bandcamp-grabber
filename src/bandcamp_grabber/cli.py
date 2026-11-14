import argparse
import sys
from pathlib import Path

from . import __version__
from .banner import print_banner
from .covers import embed_cover_in_folder
from .downloader import download_album
from .utils import find_cover


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)

    parser = argparse.ArgumentParser(
        prog="bandcamp-grabber",
        description="Скачивает альбом Bandcamp и встраивает обложку в теги.",
    )
    parser.add_argument("url", help="URL альбома Bandcamp")
    parser.add_argument("-o", "--output", default="downloads", type=Path,
                        help="Базовая папка для сохранения (по умолчанию: downloads)")
    parser.add_argument("--no-cover", action="store_true",
                        help="Не скачивать обложку")
    parser.add_argument("--no-embed", action="store_true",
                        help="Не встраивать обложку в аудиофайлы")
    parser.add_argument("--delay", type=float, default=1.5,
                        help="Пауза между загрузками треков, сек (по умолчанию: 1.5)")
    parser.add_argument("--no-banner", action="store_true",
                        help="Не печатать ASCII-баннер")                    
    parser.add_argument("--version", action="version",
                        version=f"bandcamp-grabber {__version__}")

    meta_flags = ("-h", "--help", "--version")
    wants_meta = any(flag in meta_flags for flag in raw_argv)
    wants_no_banner = "--no-banner" in raw_argv

    if not wants_meta and not wants_no_banner:
        print_banner(__version__)

    args = parser.parse_args(argv)

    try:
        album_dir = download_album(args.url, args.output, delay=args.delay)
    except Exception as e:
        print(f"Ошибка при скачивании: {e}", file=sys.stderr)
        return 1

    if args.no_cover or args.no_embed:
        return 0

    cover = find_cover(album_dir)
    if cover is None:
        print("Обложка не найдена.")
        return 0

    print(f"\nВстраиваю обложку {cover.name} в треки:")
    embed_cover_in_folder(album_dir, cover)
    return 0