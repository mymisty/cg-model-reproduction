from __future__ import annotations

import os
import shutil
import sys
import tempfile
import traceback
import webbrowser
from pathlib import Path
from tkinter import Tk, messagebox


APP_NAME = "HydroCalculator"
TEMP_APP_DIR = "HydroCalculator_reproduction_ui"
UI_DIR = Path("Hydrocalculator_reproduction_ui")

RESOURCE_FILES = (
    UI_DIR / "index.html",
    UI_DIR / "styles.css",
    UI_DIR / "app.js",
    UI_DIR / "hydrocalc-core.js",
    UI_DIR / "README.md",
    Path("Hydrocalculator_full-offline_version1-04")
    / "HydroCalculator_104_unpacked"
    / "resources"
    / "images"
    / "icona_hcalc.jpg",
)


def bundle_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]


def materialize_assets() -> Path:
    source_root = bundle_root()
    target_root = Path(tempfile.gettempdir()) / TEMP_APP_DIR

    for relative_path in RESOURCE_FILES:
        source = source_root / relative_path
        if not source.exists():
            raise FileNotFoundError(f"Missing application asset: {relative_path}")

        target = target_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    return target_root / UI_DIR / "index.html"


def show_error(details: str) -> None:
    message = f"{APP_NAME} could not be opened.\n\n{details}"
    try:
        root = Tk()
        root.withdraw()
        messagebox.showerror(APP_NAME, message)
        root.destroy()
    except Exception:
        print(message, file=sys.stderr)


def open_index(index_file: Path) -> None:
    if os.name == "nt":
        os.startfile(str(index_file))  # type: ignore[attr-defined]
        return

    webbrowser.open(index_file.as_uri(), new=2)


def main() -> int:
    try:
        open_index(materialize_assets())
        return 0
    except Exception:
        show_error(traceback.format_exc(limit=8))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
