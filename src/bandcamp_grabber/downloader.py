import json
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .utils import sanitize_filename

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_page(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def parse_tralbum(soup: BeautifulSoup) -> dict:
    for script in soup.find_all("script"):
        if script.has_attr("data-tralbum"):
            return json.loads(script["data-tralbum"])
    raise RuntimeError("data-tralbum не найден - возможно, страница изменилась "
                       "или это не страница альбома.")


def extract_cover_url(soup: BeautifulSoup, tralbum: dict) -> str | None:
    """Обложка: сначала og:image, иначе - по art_id из data-tralbum."""
    og = soup.find("meta", attrs={"property": "og:image"})
    if og and og.get("content"):
        return og["content"]
    art_id = (tralbum.get("current") or {}).get("art_id")
    if art_id:
        return f"https://f4.bcbits.com/img/a{art_id}_10.jpg"
    return None


def download_cover(url: str, dest: Path) -> Path:
    r = requests.get(url, headers=HEADERS, stream=True, timeout=30)
    r.raise_for_status()
    with dest.open("wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    return dest


def download_album(album_url: str, base_dir: Path, delay: float = 1.5) -> Path:
    soup = fetch_page(album_url)
    tralbum = parse_tralbum(soup)

    current = tralbum.get("current") or {}
    artist = tralbum.get("artist") or current.get("artist") or "Unknown Artist"
    album_title = current.get("title") or "Unknown Album"
    trackinfo = tralbum.get("trackinfo") or []

    if not trackinfo:
        raise RuntimeError("В JSON нет trackinfo - нечего скачивать.")

    album_dir = base_dir / sanitize_filename(artist) / sanitize_filename(album_title)
    album_dir.mkdir(parents=True, exist_ok=True)

    print(f"Исполнитель: {artist}")
    print(f"Альбом:      {album_title}")
    print(f"Треков:      {len(trackinfo)}")
    print(f"Папка:       {album_dir}\n")

    # Обложка
    cover_url = extract_cover_url(soup, tralbum)
    if cover_url:
        ext = ".png" if cover_url.lower().endswith(".png") else ".jpg"
        cover_path = album_dir / f"cover{ext}"
        if not cover_path.exists():
            print(f"[↓] Обложка: {cover_url}")
            try:
                download_cover(cover_url, cover_path)
            except Exception as e:
                print(f"    [!] Не удалось скачать обложку: {e}")
        else:
            print(f"[=] Обложка уже есть: {cover_path.name}")

    # Треки
    for idx, track in enumerate(trackinfo, start=1):
        title = track.get("title", f"Track {idx}")
        track_num = track.get("track_num", idx)
        mp3_url = (track.get("file") or {}).get("mp3-128")
        if not mp3_url:
            print(f"[!] Пропуск «{title}»: нет прямой ссылки.")
            continue

        filename = f"{track_num:02d} - {sanitize_filename(title)}.mp3"
        filepath = album_dir / filename
        if filepath.exists():
            print(f"[=] Уже есть: {filename}")
            continue

        print(f"[↓] {filename}")
        try:
            with requests.get(mp3_url, headers=HEADERS,
                              stream=True, timeout=30) as r:
                r.raise_for_status()
                with filepath.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        except Exception as e:
            print(f"    [!] Ошибка: {e}")
        time.sleep(delay)

    print("\nСкачивание завершено.")
    return album_dir