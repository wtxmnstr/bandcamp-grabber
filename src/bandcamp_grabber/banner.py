"""ASCII-баннер и цветной вывод для CLI."""
import os
import sys

_RESET   = "\033[0m"
_DIM     = "\033[2m"
_CYAN    = "\033[36m"
_MAGENTA = "\033[35m"

_BANNER = r"""
   ___               __                  
  / _ )___ ____  ___/ /______ ___ _  ___ 
 / _  / _ `/ _ \/ _  / __/ _ `/  ' \/ _ \
/____/\_,_/_//_/\_,_/\__/\_,_/_/_/_/ .__/
      ________  ___   ___  ___  __/_/__  
     / ___/ _ \/ _ | / _ )/ _ )/ __/ _ \ 
    / (_ / , _/ __ |/ _  / _  / _// , _/ 
    \___/_/|_/_/ |_/____/____/___/_/|_|  
                                         
"""


def _use_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def print_banner(version: str) -> None:
    tail = f"{'by wtxmnstr':>46}\n"
    note = f"  v{version} · скачивает альбомы Bandcamp и встраивает обложку\n\n"

    if _use_color():
        sys.stdout.write(f"{_CYAN}{_BANNER}{_MAGENTA}{tail}{_RESET}")
        sys.stdout.write(f"{_DIM}{note}{_RESET}")
    else:
        sys.stdout.write(_BANNER)
        sys.stdout.write(tail)
        sys.stdout.write(note)