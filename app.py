"""Ponto de entrada do Streamlit.

Execute com:
    streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from provao.app import main  # noqa: E402

main()
