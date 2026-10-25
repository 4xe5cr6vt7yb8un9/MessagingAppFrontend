"""Theme color tokens, typography, radii, and spacing constants.

Follows CustomTkinter (light, dark) appearance mode conventions and
design engineering principles from make-interfaces-feel-better.
"""

from typing import Final


class Theme:
    """UI Color tokens (Light, Dark), radii and spacing."""

    # Background surfaces
    BG_ROOT: Final[tuple[str, str]] = ("#F8FAFC", "#111318")
    BG_SIDEBAR: Final[tuple[str, str]] = ("#EDF2F7", "#181B22")
    BG_SURFACE: Final[tuple[str, str]] = ("#FFFFFF", "#222631")
    BG_HOVER: Final[tuple[str, str]] = ("#E2E8F0", "#2B303E")
    BG_SELECTED: Final[tuple[str, str]] = ("#E0E7FF", "#2E3447")

    # Primary accents
    PRIMARY: Final[tuple[str, str]] = ("#4F46E5", "#6366F1")
    PRIMARY_HOVER: Final[tuple[str, str]] = ("#4338CA", "#4F46E5")

    # Message bubbles
    BUBBLE_OUT: Final[tuple[str, str]] = ("#4F46E5", "#4F46E5")
    BUBBLE_IN: Final[tuple[str, str]] = ("#FFFFFF", "#222631")

    # Typography colors
    TEXT_PRIMARY: Final[tuple[str, str]] = ("#0F172A", "#F1F5F9")
    TEXT_SECONDARY: Final[tuple[str, str]] = ("#64748B", "#94A3B8")
    TEXT_ON_PRIMARY: Final[tuple[str, str]] = ("#FFFFFF", "#FFFFFF")

    # Borders & Status indicators
    BORDER: Final[tuple[str, str]] = ("#CBD5E1", "#2E3442")
    STATUS_ONLINE: Final[tuple[str, str]] = ("#10B981", "#10B981")
    STATUS_OFFLINE: Final[tuple[str, str]] = ("#94A3B8", "#64748B")

    # Polish metrics (make-interfaces-feel-better: concentric radii & tactile hit areas)
    RADIUS_CARD: Final[int] = 12
    RADIUS_BUTTON: Final[int] = 8
    RADIUS_INPUT: Final[int] = 8
    HIT_AREA_HEIGHT: Final[int] = 42

    FONT_FAMILY: Final[str] = "Segoe UI"
