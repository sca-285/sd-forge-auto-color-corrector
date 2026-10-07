"""Correction presets: how much Auto does and which fixes it may make. Each
preset is the full set of controls (the stock defaults, then its changes), so
one never inherits leftovers from another. The reference image and its
strength are your own pick and stay put."""

from .controls import DEFAULTS

CUSTOM = "Custom"
NOT_IN_PRESETS = {"ref_strength"}

_ALL_OFF = dict(en_wb=False, en_levels=False, en_exposure=False, en_contrast=False,
                en_saturation=False, en_jpeg=False, en_denoise=False, en_horizon=False)

_P = {
    "Standard": dict(),
    "Gentle": dict(
        strength=0.55, levels=0.6, exposure=0.5, contrast=0.4, saturation=0.5, denoise=0.6),
    "Full Fix": dict(
        strength=1.0, wb=1.0, levels=1.0, exposure=1.0, contrast=0.9, saturation=1.0,
        jpeg=1.0, denoise=1.0, en_horizon=True),
    "Keep the Mood": dict(
        strength=0.7, keep_mood=0.7, levels=0.6, exposure=0.4, contrast=0.4, saturation=0.4),
    "Repair Only": dict(
        _ALL_OFF, strength=1.0, en_jpeg=True, jpeg=1.0, en_denoise=True, denoise=1.0),
    "Colour Only": dict(
        _ALL_OFF, en_wb=True, wb=1.0, en_saturation=True, saturation=0.8),
    "Tone Only": dict(
        _ALL_OFF, en_levels=True, levels=0.9, en_exposure=True, exposure=0.8,
        en_contrast=True, contrast=0.7),
    "Old Photo Scan": dict(
        strength=1.0, wb=1.0, levels=1.0, exposure=0.8, contrast=0.8, saturation=1.0,
        jpeg=1.0, denoise=1.0, en_horizon=True, protect_intent=False),
}

PRESETS = {name: {**DEFAULTS, **p} for name, p in _P.items()}
CHOICES = [CUSTOM, *PRESETS]

CATEGORIES = {
    "Standard": "Everyday", "Gentle": "Everyday", "Full Fix": "Everyday", "Keep the Mood": "Everyday",
    "Repair Only": "Focused", "Colour Only": "Focused", "Tone Only": "Focused",
    "Old Photo Scan": "Restore",
}

DESCRIPTIONS = {
    "Standard": "The stock settings: every fix on, measured, at 80%. Horizon off.",
    "Gentle": "Half-strength nudges: fixes what is clearly wrong, barely touches the rest.",
    "Full Fix": "Everything at full strength, horizon levelling included.",
    "Keep the Mood": "Keeps most of a colour cast and the contrast you chose; only the faults go.",
    "Repair Only": "JPEG blocking and noise, nothing else: colour and tone stay as they are.",
    "Colour Only": "Colour cast and colour strength only; brightness and contrast untouched.",
    "Tone Only": "Black & white points, exposure and contrast only; colour untouched.",
    "Old Photo Scan": "For faded scans and old phone pictures: every fix at full, no low-key / high-key protection.",
}
