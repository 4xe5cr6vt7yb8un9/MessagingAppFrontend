from pathlib import Path
import sys
import customtkinter
from PIL import Image

# Ensure src is in sys.path for standalone pytest invocations
_SRC_PATH = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_PATH not in sys.path:
    sys.path.insert(0, _SRC_PATH)

from messaging_app.ui.icons import get_icon
from messaging_app.ui.theme import Theme


def test_theme_tokens():
    assert isinstance(Theme.PRIMARY, tuple)
    assert len(Theme.PRIMARY) == 2  # (light, dark)
    assert Theme.RADIUS_CARD == 12
    assert Theme.RADIUS_BUTTON == 8
    assert Theme.RADIUS_INPUT == 8
    assert Theme.HIT_AREA_HEIGHT >= 40
    assert Theme.FONT_FAMILY == "Segoe UI"
    assert isinstance(Theme.BG_ROOT, tuple)
    assert isinstance(Theme.STATUS_ONLINE, tuple)


def test_icon_retrieval():
    icon = get_icon("send", size=(20, 20))
    assert isinstance(icon, customtkinter.CTkImage)
    assert icon._size == (20, 20)
    assert isinstance(icon._light_image, Image.Image)
    assert isinstance(icon._dark_image, Image.Image)


def test_icon_caching():
    icon1 = get_icon("search", size=(24, 24))
    icon2 = get_icon("search", size=(24, 24))
    assert icon1 is icon2


def test_icon_multiple_names():
    for name in ["send", "user-plus", "search", "sun", "moon", "message-square", "check-check", "unknown-fallback"]:
        icon = get_icon(name, size=(16, 16))
        assert isinstance(icon, customtkinter.CTkImage)
        assert icon._size == (16, 16)
