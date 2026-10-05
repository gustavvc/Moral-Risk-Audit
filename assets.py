"""Local asset helpers shared by the Streamlit UI."""

import base64
from pathlib import Path

import streamlit as st


@st.cache_data(show_spinner=False)
def portrait_data_uri(filename: str) -> str:
    """Load a bundled philosopher portrait as a browser-ready data URI."""
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
