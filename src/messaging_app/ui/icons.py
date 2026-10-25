"""Icon provider and caching system with high-DPI raster fallback rendering."""

from pathlib import Path
from PIL import Image, ImageDraw
import customtkinter

ASSETS_DIR = Path(__file__).parent / "assets" / "icons"
_ICON_CACHE: dict[tuple[str, tuple[int, int]], customtkinter.CTkImage] = {}


def _render_fallback_icon(name: str, size: tuple[int, int], color: str) -> Image.Image:
    """Generate high-DPI raster fallback icon when SVG parser is unavailable."""
    w, h = size[0] * 2, size[1] * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    m = 4
    if name == "send":
        draw.polygon([(m, m), (w - m, h // 2), (m, h - m), (m + 6, h // 2)], fill=color)
    elif name == "user-plus":
        draw.ellipse([(m, m), (w - m - 8, h - m - 8)], outline=color, width=3)
        draw.line([(w - 8, m + 4), (w - 8, m + 14)], fill=color, width=3)
        draw.line([(w - 13, m + 9), (w - 3, m + 9)], fill=color, width=3)
    elif name == "search":
        draw.ellipse([(m, m), (w - 12, h - 12)], outline=color, width=3)
        draw.line([(w - 14, h - 14), (w - m, h - m)], fill=color, width=3)
    elif name == "sun":
        draw.ellipse([(w // 4, h // 4), (3 * w // 4, 3 * h // 4)], fill=color)
    elif name == "moon":
        draw.ellipse([(m, m), (w - m, h - m)], fill=color)
        draw.ellipse([(m + 6, m - 2), (w - m + 6, h - m - 2)], fill=(0, 0, 0, 0))
    elif name == "message-square":
        draw.rounded_rectangle([(m, m), (w - m, h - m - 4)], radius=4, outline=color, width=3)
        draw.polygon([(m + 4, h - m - 4), (m + 10, h - m - 4), (m + 4, h - m + 4)], fill=color)
    elif name == "check-check":
        draw.line([(m, h // 2), (w // 3, h - m - 2), (2 * w // 3, m + 4)], fill=color, width=3)
        draw.line([(w // 3 + 4, h // 2 + 2), (w // 2 + 4, h - m - 2), (w - m, m + 4)], fill=color, width=3)
    else:
        draw.ellipse([(m, m), (w - m, h - m)], outline=color, width=2)
    return img


def get_icon(name: str, size: tuple[int, int] = (20, 20)) -> customtkinter.CTkImage:
    """Return a cached high-DPI CTkImage with automatic light/dark tinting."""
    key = (name, size)
    if key in _ICON_CACHE:
        return _ICON_CACHE[key]

    light_img = _render_fallback_icon(name, size, "#1E293B")
    dark_img = _render_fallback_icon(name, size, "#F8FAFC")
    ctk_image = customtkinter.CTkImage(light_image=light_img, dark_image=dark_img, size=size)
    _ICON_CACHE[key] = ctk_image
    return ctk_image
