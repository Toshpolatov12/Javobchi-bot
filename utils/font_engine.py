"""
utils/font_engine.py — Adapted from Userbot font_core/builtin_fonts.py
Translates plain text into 12 stylish Unicode font variations.
"""

from typing import Dict, Optional

UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWER = "abcdefghijklmnopqrstuvwxyz"
DIGITS = "0123456789"


def _seq_map(chars: str, start_codepoint: int, exceptions: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    exceptions = exceptions or {}
    result: Dict[str, str] = {}
    cp = start_codepoint
    for ch in chars:
        result[ch] = exceptions.get(ch, chr(cp))
        cp += 1
    return result


def _identity_map(chars: str) -> Dict[str, str]:
    return {ch: ch for ch in chars}


def _build(upper_map: Dict[str, str], lower_map: Dict[str, str],
           digit_map: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    merged: Dict[str, str] = {}
    merged.update(upper_map)
    merged.update(lower_map)
    merged.update(digit_map if digit_map is not None else _identity_map(DIGITS))
    return merged


# 1. Bold (𝐀𝐁𝐂 / 𝐚𝐛𝐜 / 𝟏𝟐𝟑)
_BOLD_UPPER = _seq_map(UPPER, 0x1D400)
_BOLD_LOWER = _seq_map(LOWER, 0x1D41A)
_BOLD_DIGITS = _seq_map(DIGITS, 0x1D7CE)

# 2. Script (𝒜𝐵𝒞 / 𝒶𝒷𝒸)
_SCRIPT_UPPER_EXC = {
    "B": "\u212C", "E": "\u2130", "F": "\u2131", "H": "\u210B",
    "I": "\u2110", "L": "\u2112", "M": "\u2133", "R": "\u211B",
}
_SCRIPT_UPPER = _seq_map(UPPER, 0x1D49C, _SCRIPT_UPPER_EXC)
_SCRIPT_LOWER_EXC = {"e": "\u212F", "g": "\u210A", "o": "\u2134"}
_SCRIPT_LOWER = _seq_map(LOWER, 0x1D4B6, _SCRIPT_LOWER_EXC)

# 3. Sans (𝖠𝖡𝖢 / 𝖺𝖻𝖼 / 𝟣𝟤𝟥)
_SANS_UPPER = _seq_map(UPPER, 0x1D5A0)
_SANS_LOWER = _seq_map(LOWER, 0x1D5BA)
_SANS_DIGITS = _seq_map(DIGITS, 0x1D7E2)

# 4. Gothic (𝕬𝕭𝕮 / 𝖆𝖇𝖈)
_GOTHIC_UPPER = _seq_map(UPPER, 0x1D56C)
_GOTHIC_LOWER = _seq_map(LOWER, 0x1D586)

# 5. Bubble (Ⓐ Ⓑ Ⓒ / ⓐ ⓑ ⓒ / ⓪①②)
_BUBBLE_UPPER = _seq_map(UPPER, 0x24B6)
_BUBBLE_LOWER = _seq_map(LOWER, 0x24D0)
_BUBBLE_DIGITS = {"0": "\u24EA", **{d: chr(0x2460 + i) for i, d in enumerate("123456789")}}

# 6. Double (𝔸𝔹ℂ / 𝕒𝕓𝕔 / 𝟘𝟙𝟚)
_DOUBLE_UPPER_EXC = {
    "C": "\u2102", "H": "\u210D", "N": "\u2115", "P": "\u2119",
    "Q": "\u211A", "R": "\u211D", "Z": "\u2124",
}
_DOUBLE_UPPER = _seq_map(UPPER, 0x1D538, _DOUBLE_UPPER_EXC)
_DOUBLE_LOWER = _seq_map(LOWER, 0x1D552)
_DOUBLE_DIGITS = _seq_map(DIGITS, 0x1D7D8)

# 7. Monospace (𝙰𝙱𝙲 / 𝚊𝚋𝚌 / 𝟶𝟷𝟸)
_MONO_UPPER = _seq_map(UPPER, 0x1D670)
_MONO_LOWER = _seq_map(LOWER, 0x1D68A)
_MONO_DIGITS = _seq_map(DIGITS, 0x1D7F6)

# 8. Small Caps (ᴀʙᴄ)
_SMALLCAPS_UPPER = {
    "A": "\u1D00", "B": "\u0299", "C": "\u1D04", "D": "\u1D05", "E": "\u1D07",
    "F": "\uA730", "G": "\u0262", "H": "\u029C", "I": "\u026A", "J": "\u1D0A",
    "K": "\u1D0B", "L": "\u029F", "M": "\u1D0D", "N": "\u0274", "O": "\u1D0F",
    "P": "\u1D18", "Q": "Q",      "R": "\u0280", "S": "S",      "T": "\u1D1B",
    "U": "\u1D1C", "V": "\u1D20", "W": "\u1D21", "X": "X",      "Y": "\u028F",
    "Z": "\u1D22",
}
_SMALLCAPS_LOWER = {ch.lower(): rep for ch, rep in _SMALLCAPS_UPPER.items()}

# 9. Fraktur (𝔄𝔅ℭ / 𝔞𝔟𝔠)
_FRAKTUR_UPPER_EXC = {
    "C": "\u212D", "H": "\u210C", "I": "\u2111", "R": "\u211C", "Z": "\u2128",
}
_FRAKTUR_UPPER = _seq_map(UPPER, 0x1D504, _FRAKTUR_UPPER_EXC)
_FRAKTUR_LOWER = _seq_map(LOWER, 0x1D51E)

# 10. Outline (Ａ Ｂ Ｃ / ａ ｂ ｃ / １２３)
_OUTLINE_UPPER = _seq_map(UPPER, 0xFF21)
_OUTLINE_LOWER = _seq_map(LOWER, 0xFF41)
_OUTLINE_DIGITS = _seq_map(DIGITS, 0xFF10)

# 11. Squared (🄰🄱🄲)
_SQUARED_UPPER = _seq_map(UPPER, 0x1F130)
_SQUARED_LOWER = {ch: _SQUARED_UPPER[ch.upper()] for ch in LOWER}

# 12. Circled (🅐 🅑 🅒)
_CIRCLED_UPPER = _seq_map(UPPER, 0x1F150)
_CIRCLED_LOWER = {ch: _CIRCLED_UPPER[ch.upper()] for ch in LOWER}
_CIRCLED_DIGITS = {"0": "0", **{d: chr(0x2775 + i) for i, d in enumerate("123456789")}}


BUILTIN_FONTS: Dict[str, Dict[str, str]] = {
    "Bold": _build(_BOLD_UPPER, _BOLD_LOWER, _BOLD_DIGITS),
    "Script": _build(_SCRIPT_UPPER, _SCRIPT_LOWER),
    "Sans": _build(_SANS_UPPER, _SANS_LOWER, _SANS_DIGITS),
    "Gothic": _build(_GOTHIC_UPPER, _GOTHIC_LOWER),
    "Bubble": _build(_BUBBLE_UPPER, _BUBBLE_LOWER, _BUBBLE_DIGITS),
    "Double": _build(_DOUBLE_UPPER, _DOUBLE_LOWER, _DOUBLE_DIGITS),
    "Monospace": _build(_MONO_UPPER, _MONO_LOWER, _MONO_DIGITS),
    "Small Caps": _build(_SMALLCAPS_UPPER, _SMALLCAPS_LOWER),
    "Fraktur": _build(_FRAKTUR_UPPER, _FRAKTUR_LOWER),
    "Outline": _build(_OUTLINE_UPPER, _OUTLINE_LOWER, _OUTLINE_DIGITS),
    "Squared": _build(_SQUARED_UPPER, _SQUARED_LOWER),
    "Circled": _build(_CIRCLED_UPPER, _CIRCLED_LOWER, _CIRCLED_DIGITS),
}


def apply_font(style: str, text: str) -> str:
    mapping = BUILTIN_FONTS.get(style)
    if not mapping:
        return text

    return "".join(mapping.get(ch, ch) for ch in text)
