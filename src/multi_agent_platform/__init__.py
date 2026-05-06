from pathlib import Path

WEB_DIRECTORY = Path(__file__).resolve().parent / "web"

__all__ = ["WEB_DIRECTORY", "__version__"]

__version__ = "0.0.0"
