"""Shared icon policy: an application's own icon wins; otherwise use SwirUI."""
from pathlib import Path

ASSET_ROOT = Path(__file__).resolve().parent / "assets" / "icons"


def resolve_icon(asset_root=None):
    root = Path(asset_root) if asset_root is not None else ASSET_ROOT
    application = root / "app.ico"
    fallback = root / "swirui.ico"
    if application.is_file():
        return application
    if fallback.is_file():
        return fallback
    raise FileNotFoundError("Missing application icon and SwirUI fallback icon")
