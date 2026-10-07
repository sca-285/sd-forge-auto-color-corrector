"""Every control, declared once. The UI and the PNG-info round trip read this
table. The reference image is not in it: a picture does not go into PNG info."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Control:
    name: str
    label: str
    default: object
    minimum: float = 0.0
    maximum: float = 1.0
    step: float = 0.05
    kind: str = "slider"    # slider | checkbox
    info: str = ""


C = Control
CONTROLS = [
    C("strength", "Overall strength", 0.8,
      info="How much of the correction is applied: 0 = original, 1 = all of it."),
    C("en_wb", "Fix colour cast", True, kind="checkbox"),
    C("wb", "White balance", 1.0, info="Measured on what ought to be grey; both warm/cool and green/magenta."),
    C("keep_mood", "Keep mood", 0.0,
      info="Share of a colour cast to keep: 0 = neutral, 1 = untouched."),
    C("en_levels", "Fix black & white points", True, kind="checkbox"),
    C("levels", "Levels", 0.8, info="Makes milky blacks black and dull whites white, without clipping."),
    C("en_exposure", "Fix exposure", True, kind="checkbox"),
    C("exposure", "Exposure", 0.7, info="Brings a too dark or too bright picture back, in linear light."),
    C("en_contrast", "Fix contrast", True, kind="checkbox"),
    C("contrast", "Contrast", 0.6, info="Lifts a flat picture, calms a harsh one."),
    C("en_saturation", "Fix colour strength", True, kind="checkbox"),
    C("saturation", "Colour strength", 0.8, info="Vibrance on dull pictures; skin and strong colours are spared."),
    C("en_jpeg", "Fix JPEG blocking", True, kind="checkbox"),
    C("jpeg", "JPEG repair", 1.0, info="Smooths JPEG blocks and ringing, as strong as measured."),
    C("en_denoise", "Fix noise", True, kind="checkbox"),
    C("denoise", "Noise reduction", 0.8, info="Colour noise smoothed hard, grain gently; edges kept."),
    C("en_horizon", "Level the horizon", False, kind="checkbox",
      info="Levels a tilted picture from its straight lines (crops a little)."),
    C("protect_intent", "Respect low-key / high-key pictures", True, kind="checkbox",
      info="A night scene with lights stays dark, a bright snow scene stays bright."),
    C("ref_strength", "Reference strength", 0.5,
      info="Only with a reference image: how far colour and spread move towards it."),
]

BY_NAME = {c.name: c for c in CONTROLS}
NAMES = [c.name for c in CONTROLS]
DEFAULTS = {c.name: c.default for c in CONTROLS}

INFOTEXT_KEY = "Auto Color Corrector"
REPORT_KEY = "Auto Color Corrector found"


def coerce(name, value):
    c = BY_NAME[name]
    if c.kind == "checkbox":
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on")
        return bool(value)
    return min(max(float(value), c.minimum), c.maximum)


def settings(values=None, **overrides):
    s = dict(DEFAULTS)
    for src in (values or {}), overrides:
        for k, v in src.items():
            if k in BY_NAME:
                s[k] = coerce(k, v)
    return s


def to_infotext(s) -> str:
    """Only what differs from the defaults: 'on' for a stock run."""
    parts = []
    for c in CONTROLS:
        v = s[c.name]
        if v == c.default or (isinstance(v, float) and abs(v - c.default) < 1e-9):
            continue
        parts.append(f"{c.name}={v:g}" if isinstance(v, float) else f"{c.name}={v}")
    return "; ".join(parts) or "on"


def from_infotext(text):
    if not text:
        return None
    values = {}
    for part in text.strip().strip('"').split(";"):
        if "=" in part:
            k, v = (t.strip() for t in part.split("=", 1))
            if k in BY_NAME:
                try:
                    values[k] = coerce(k, v)
                except ValueError:
                    pass
    return settings(values)
