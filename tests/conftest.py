"""Pytest configuration and root fixtures."""

from pathlib import Path
import os
import sys

# Ensure src directory is in sys.path for test discovery
_SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# Ensure TCL_LIBRARY and TK_LIBRARY are explicitly configured on Windows if unset
if sys.platform == "win32":
    tcl_dir = os.path.join(sys.prefix, "tcl", "tcl8.6")
    tk_dir = os.path.join(sys.prefix, "tcl", "tk8.6")
    if os.path.isdir(tcl_dir) and "TCL_LIBRARY" not in os.environ:
        os.environ["TCL_LIBRARY"] = tcl_dir
    if os.path.isdir(tk_dir) and "TK_LIBRARY" not in os.environ:
        os.environ["TK_LIBRARY"] = tk_dir
