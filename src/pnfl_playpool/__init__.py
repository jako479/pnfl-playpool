from pathlib import Path

from .pool import Play, PlayPool


ROOT_DIR = Path(__file__).resolve().parent.parent.parent

__all__ = [
    "Play",
    "PlayPool",
    "ROOT_DIR",
]
