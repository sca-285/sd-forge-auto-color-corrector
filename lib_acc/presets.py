"""Correction presets: which fixes Auto may make, and how far. Each preset is
the full set of controls (the stock defaults, then its changes), so one never
inherits leftovers from another. The reference image and its strength are your
own pick and stay put.

A ticked fix is permission, not an order: Auto still measures first and skips
a fix when there is nothing to fix. The presets differ in which fixes they
allow, since a picture that needs no fix looks the same under all of them."""

from .controls import DEFAULTS

CUSTOM = "Custom"
NOT_IN_PRESETS = {"ref_strength"}

_ALL_OFF = dict(en_wb=False, en_levels=False, en_exposure=False, en_contrast=False,
                en_saturation=False, en_jpeg=False, en_denoise=False, en_horizon=False)

_P = {
    # Every fix allowed, each only as far as it measures a fault.
    "Standard": dict(),
    # Faults only: repairs, colour cast and exposure. Levels, contrast and
    # colour strength, the taste-shaped fixes, stay as generated.
    "Natural": dict(
        en_levels=False, en_contrast=False, en_saturation=False),
    "Gentle": dict(
        strength=0.5, levels=0.6, exposure=0.6, contrast=0.4, saturation=0.4, denoise=0.6),
    "Full Fix": dict(
        strength=1.0, wb=1.0, levels=1.0, exposure=1.0, contrast=1.0, saturation=1.0,
        jpeg=1.0, denoise=1.0, en_horizon=True),
    # A deliberately warm, cool or dark picture: the cast mostly kept, no
    # levels, contrast or colour changes, exposure only half.
    "Keep the Mood": dict(
        keep_mood=0.8, en_levels=False, en_contrast=False, en_saturation=False, exposure=0.5),
    "Repair Only": dict(
        _ALL_OFF, strength=1.0, en_jpeg=True, jpeg=1.0, en_denoise=True, denoise=1.0),
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
    "Standard": "Everyday", "Natural": "Everyday", "Gentle": "Everyday", "Full Fix": "Everyday",
    "Keep the Mood": "Everyday", "Repair Only": "Focused", "Tone Only": "Focused",
    "Old Photo Scan": "Restore",
}

DESCRIPTIONS = {
    "Standard": "Every fix allowed, each only as far as it measures a fault. Horizon off.",
    "Natural": "Faults only: blocking, noise, colour cast, exposure. Contrast and colour left as generated.",
    "Gentle": "Everything at half strength: a light touch.",
    "Full Fix": "Everything at full strength, horizon levelling included.",
    "Keep the Mood": "For a deliberately warm, cool or dark picture: keeps its cast, contrast and colour.",
    "Repair Only": "JPEG blocking and noise, nothing else: colour and tone stay as they are.",
    "Tone Only": "Black & white points, exposure and contrast only; colour untouched.",
    "Old Photo Scan": "For faded scans and old phone pictures: every fix at full, no low-key / high-key protection.",
}
