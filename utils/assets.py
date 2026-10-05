"""Gemeinsame lokale Hilfsfunktionen für Bilddateien der Streamlit-Oberfläche."""

import base64
from pathlib import Path

import streamlit as st


@st.cache_data(show_spinner=False)
def portrait_data_uri(filename: str) -> str:
    """Lädt ein eingebundenes Philosophenporträt als Daten-URI für den Browser."""
    portrait_dir = Path(__file__).resolve().parent.parent / "assets" / "portraits"
    image_path = (portrait_dir / filename).resolve()
    if not image_path.is_relative_to(portrait_dir.resolve()):
        raise ValueError("Der Porträtpfad liegt außerhalb des Asset-Verzeichnisses.")
    if not image_path.is_file():
        raise FileNotFoundError(f"Das Porträt fehlt: {image_path}")

    mime_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
    mime_type = mime_types.get(image_path.suffix.lower())
    if mime_type is None:
        raise ValueError(f"Nicht unterstütztes Porträtformat: {image_path.suffix}")
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


@st.cache_data(show_spinner=False)
def sun_logo_data_uri() -> str:
    """Lädt das lokale Sonnenlogo als Daten-URI mit JPG-Fallback."""
    asset_dir = Path(__file__).resolve().parent.parent / "assets"
    logo_path = next(
        (
            candidate
            for candidate in (asset_dir / "sun_logo.png", asset_dir / "sun_logo.jpg")
            if candidate.is_file()
        ),
        None,
    )
    if logo_path is None:
        raise FileNotFoundError(
            "Das Sonnenlogo fehlt: erwartet assets/sun_logo.png oder assets/sun_logo.jpg."
        )

    mime_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
    mime_type = mime_types.get(logo_path.suffix.lower())
    if mime_type is None:
        raise ValueError(f"Nicht unterstütztes Sonnenlogoformat: {logo_path.suffix}")
    encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"
