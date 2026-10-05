"""Auto correction: measure the image, decide what is actually off, fix only
that, and say what was found.

Every step follows the same pattern: measure -> compare with a target ->
skip if inside a dead zone -> correct by the size of the error, capped. A
well-made image comes through untouched. The measuring runs on a copy of at
most 512 px; the corrections are applied to the full image.

Intent guards keep deliberate pictures as they are: a night scene with light
sources is low-key, not underexposed; a bright snow scene is high-key, not
overexposed; a black & white or toned picture has no cast to remove; a
picture with almost nothing grey in it (golden hour, neon) gives no honest
reading of a cast, so its colour is left alone.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import torch
import torch.nn.functional as F

from . import ops

ANALYSIS_SIZE = 512


@dataclass
class Plan:
    gains: tuple = (1.0, 1.0, 1.0)
    black: float = 0.0
    white: float = 1.0
    stops: float = 0.0
    contrast: float = 0.0
    pivot: float = 0.5
    vibrance: float = 0.0
    reference: tuple = None       # (ref_mean, ref_std) in Lab
    notes: list = field(default_factory=list)

    def changes(self):
        return (any(abs(g - 1.0) > 1e-6 for g in self.gains) or self.black > 0.0 or self.white < 1.0
                or bool(self.stops) or bool(self.contrast) or bool(self.vibrance) or self.reference is not None)

    def report(self):
        return " · ".join(self.notes) if self.notes else "nothing to correct"


def _small(x):
    h, w = x.shape[-2:]
    s = ANALYSIS_SIZE / max(h, w)
    if s >= 1.0:
        return x
    return F.interpolate(x, size=(max(1, round(h * s)), max(1, round(w * s))), mode="area")


def _q(t, q):
    return float(torch.quantile(t.flatten().float(), q))


def lab_stats(x):
    lab = ops.to_lab(_small(x))
    return lab.mean(dim=(2, 3), keepdim=True), lab.std(dim=(2, 3), keepdim=True)


# ------------------------------------------------------------------ detectors

def _sat(x):
    """HSV saturation: chroma relative to the brightest channel."""
    return ops.chroma(x) / x.amax(1, keepdim=True).clamp_min(1e-4)


def is_monochrome(x):
    """Black & white, or toned (sepia, cyanotype): no pixel is strongly
    coloured, and the faint colour there is all points one way."""
    y = ops.luma(x)
    mid = ((y > 0.08) & (y < 0.95)).expand_as(y)
    if mid.float().mean() < 0.05:
        return False
    sat = _sat(x)[mid]
    if _q(sat, 0.95) < 0.08:
        return True                       # plain black & white
    if _q(sat, 0.95) > 0.40:
        return False                      # something is properly coloured
    # Toned: the hue of the coloured pixels is concentrated (mean resultant
    # length of the hue angle close to 1).
    a, b = ops.opponent(x)
    a, b = a[mid], b[mid]
    r = torch.sqrt(a * a + b * b).clamp_min(1e-6)
    return float(torch.sqrt((a / r).mean() ** 2 + (b / r).mean() ** 2)) > 0.95


def tonal_key(x):
    """'low', 'high' or 'normal': whether darkness or brightness is the point.

    Low-key: dark overall but with real highlights (lamps, neon, a lit face),
    so the exposure is a choice and the image is not underexposed.
    High-key: bright overall but with real darks, so it is not overexposed.
    """
    y = ops.luma(x)
    median, p_lo, p_hi = _q(y, 0.5), _q(y, 0.005), _q(y, 0.995)
    bright_share = float((y > 0.75).float().mean())
    if median < 0.30 and p_hi > 0.75 and bright_share > 0.002:
        return "low"
    if median > 0.65 and p_lo < 0.25:
        return "high"
    return "normal"


def find_cast(x):
    """Linear-light gains that make the bright near-neutral pixels neutral,
    and the share of the frame they cover; (None, share) when there is too
    little of them to trust.

    Bright near-neutrals (a white shirt, a cup, clouds, a lit wall) carry the
    colour of the light most honestly; dim low-saturation pixels are as often
    brown wood or a blue night sky as they are grey. Two passes: a strong cast
    hides some neutrals until the first estimate has been taken out.
    """
    lin = ops.srgb_to_linear(x)
    gains = torch.ones(3, device=x.device, dtype=x.dtype)
    share = 0.0
    for limit in (0.30, 0.15):
        seen = ops.linear_to_srgb(lin * gains.view(1, 3, 1, 1))
        y = ops.luma(seen)
        sat = _sat(seen)
        cand = (sat < limit) & (y > 0.15) & (y < 0.97)
        if cand.float().mean() < 0.02:
            return None, float(cand.float().mean())
        bright = cand & (y >= _q(y[cand], 0.6))
        share = float(bright.float().mean())
        if share < 0.005:
            return None, share
        weight = (1.0 - sat / limit).clamp(0.0, 1.0) * bright.to(x.dtype)
        mean = (lin * weight).sum(dim=(0, 2, 3)) / weight.sum().clamp_min(1e-6)
        target = float((mean * mean.new_tensor(ops.LUMA)).sum())
        gains = (target / mean.clamp_min(1e-6)).clamp(0.6, 1.6)
    return gains, share


# How far the light may stray from neutral before it counts as a cast. Warm
# and cool light is everyday (tungsten, shade, golden hour), so it gets a wide
# allowance; green and magenta almost never look intended.
WARM_COOL_TOLERANCE = 0.12
GREEN_MAGENTA_TOLERANCE = 0.04


def _beyond_tolerance(gains):
    """The part of a cast (as log gains) that lies outside the tolerances."""
    lr, lg, lb = torch.log(gains)
    wc = (lb - lr) / 2                     # + = too warm
    gm = (lr + lb) / 2 - lg                # + = too green
    shrink = lambda v, t: torch.sign(v) * (v.abs() - t).clamp_min(0.0)  # noqa: E731
    wc, gm = shrink(wc, WARM_COOL_TOLERANCE / 2), shrink(gm, GREEN_MAGENTA_TOLERANCE)
    return torch.stack((-wc + gm / 3, -2 * gm / 3, wc + gm / 3))


def _describe_cast(gains):
    r, g, b = (math.log(float(v)) for v in gains)
    warm_cool = b - r                 # + : image was too warm (needs blue)
    green_mag = (r + b) / 2 - g       # + : image was too green (needs magenta)
    parts = []
    if abs(warm_cool) > 0.02:
        parts.append(("warm" if warm_cool > 0 else "cool") + f" {abs(warm_cool):.2f}")
    if abs(green_mag) > 0.02:
        parts.append(("green" if green_mag > 0 else "magenta") + f" {abs(green_mag):.2f}")
    return ", ".join(parts)


# ------------------------------------------------------------------ planning

def plan(x, s, reference=None):
    """Decide the corrections for x (1, 3, H, W) under settings s."""
    p = Plan()
    small = _small(x)
    mono = is_monochrome(small)
    key = tonal_key(small) if s["protect_intent"] else "normal"
    if mono:
        p.notes.append("monochrome: colour left alone")
    if key != "normal":
        p.notes.append(f"{key}-key: kept")
    # A plain backdrop or a near-solid frame has no tonal range to judge.
    y0 = ops.luma(small)
    flat = _q(y0, 0.99) - _q(y0, 0.01) < 0.15
    if flat:
        p.notes.append("almost one tone: tone left alone")

    # 1. White balance
    cur = small
    if s["en_wb"] and s["wb"] > 0 and not mono:
        gains, share = find_cast(small)
        if gains is None:
            p.notes.append(f"cast: not measurable ({share:.0%} grey), kept")
        else:
            amount = s["wb"] * (1.0 - s["keep_mood"])
            if key == "low":
                # Coloured light is part of most night pictures: half measures.
                amount *= 0.5
            fix = _beyond_tolerance(gains)
            if float(fix.abs().max()) < 1e-3 or amount <= 0:
                if _describe_cast(gains):
                    p.notes.append(f"cast: {_describe_cast(gains)}, kept"
                                   + (" (mood)" if amount <= 0 else " (natural light)"))
            else:
                applied = torch.exp(fix * amount)
                p.gains = tuple(float(v) for v in applied)
                cur = ops.white_balance(cur, applied)
                p.notes.append(f"cast: {_describe_cast(gains)} -> corrected" + (" by half" if amount < 0.99 and key == "low" else ""))

    # 2. Levels
    # A low-key picture's dark, lifted or not, is part of its look.
    if s["en_levels"] and s["levels"] > 0 and key != "low" and not flat:
        y = ops.luma(cur)
        lo, hi = _q(y, 0.005), _q(y, 0.995)
        black = min(lo, 0.12) if lo > 0.03 else 0.0
        white = max(hi, 0.60) if hi < 0.95 else 1.0
        if key == "high":
            black = 0.0
        black *= s["levels"]
        white = 1.0 - (1.0 - white) * s["levels"]
        if black > 0.0 or white < 1.0:
            p.black, p.white = black, white
            cur = ops.levels(cur, black, white)
            p.notes.append(f"levels: {black:.2f}..{white:.2f} -> 0..1")

    # 3. Exposure
    if s["en_exposure"] and s["exposure"] > 0 and not flat:
        median = _q(ops.luma(cur), 0.5)
        # Only a median outside the normal band is wrong, and it is brought
        # to the edge of the band, not to one 'correct' grey: pictures are
        # allowed to be darker or brighter than average.
        low, high = 0.28, 0.62
        if key == "low":
            low = 0.10                    # only rescue a truly black frame
        elif key == "high":
            high = 0.85
        if key != "high" and float((ops.luma(cur) > 0.98).float().mean()) > 0.05:
            high = 0.50                   # clipped whites: the frame is overexposed
        target = min(max(median, low), high)
        lin_m = float(ops.srgb_to_linear(torch.tensor(max(median, 1e-3))))
        lin_t = float(ops.srgb_to_linear(torch.tensor(target)))
        stops = max(-1.0, min(1.0, math.log2(lin_t / lin_m))) * s["exposure"]
        if abs(stops) >= 0.12:
            p.stops = stops
            cur = ops.exposure(cur, stops)
            p.notes.append(f"exposure: {stops:+.2f} stop")

    # 4. Contrast
    if s["en_contrast"] and s["contrast"] > 0 and not flat:
        y = ops.luma(cur)
        iqr = _q(y, 0.75) - _q(y, 0.25)
        median = _q(y, 0.5)
        amount = 0.0
        if iqr < 0.20 and key == "normal":
            amount = min(0.45, (0.26 - iqr) * 3.0)
        elif iqr > 0.62 and key == "normal":
            amount = -min(0.30, (iqr - 0.58) * 1.5)
        amount *= s["contrast"]
        if abs(amount) >= 0.04:
            p.contrast, p.pivot = amount, median
            cur = ops.contrast(cur, amount, median)
            p.notes.append(f"contrast: spread {iqr:.2f}, {amount:+.2f}")

    # 5. Saturation
    if s["en_saturation"] and s["saturation"] > 0 and not mono and key != "low" and not flat:
        y = ops.luma(cur)
        c = ops.chroma(cur)[(y > 0.08) & (y < 0.95)]
        level = float(c.mean()) if c.numel() else 0.0
        amount = 0.0
        if level < 0.20:
            amount = min(0.8, (0.24 - level) * 7.0)
        elif level > 0.55:
            amount = -min(0.3, (level - 0.50) * 2.0)
        amount *= s["saturation"]
        if abs(amount) >= 0.04:
            p.vibrance = amount
            p.notes.append(f"colour: level {level:.2f}, vibrance {amount:+.2f}")

    # 6. Reference
    if reference is not None and s["ref_strength"] > 0:
        p.reference = lab_stats(reference)
        p.notes.append(f"reference: matched {s['ref_strength']:.0%}")
    return p


def apply(x, p, ref_strength=0.0):
    """Carry out a plan on the full-size image."""
    if any(abs(g - 1.0) > 1e-6 for g in p.gains):
        x = ops.white_balance(x, x.new_tensor(p.gains))
    if p.black > 0.0 or p.white < 1.0:
        x = ops.levels(x, p.black, p.white)
    if p.stops:
        x = ops.exposure(x, p.stops)
    if p.contrast:
        x = ops.contrast(x, p.contrast, p.pivot)
    if p.vibrance:
        x = ops.vibrance(x, p.vibrance)
    if p.reference is not None and ref_strength > 0:
        src_mean, src_std = lab_stats(x)
        ref_mean, ref_std = (t.to(x.device, x.dtype) for t in p.reference)
        x = ops.match_stats(x, ref_mean, ref_std, src_mean, src_std, ref_strength)
    return x.clamp(0.0, 1.0)


# ------------------------------------------------------------------ entry

def to_tensor(image, device):
    import numpy as np
    arr = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    return torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0).to(device)


def to_image(x):
    import numpy as np
    from PIL import Image
    arr = x[0].clamp(0.0, 1.0).permute(1, 2, 0).cpu().numpy()
    # np.rint, not a truncating cast: truncation is half a level dark on average.
    return Image.fromarray(np.rint(arr * 255.0).astype(np.uint8), "RGB")


@torch.no_grad()
def correct(image, s, reference=None, device="cpu"):
    """Return (corrected PIL image, Plan). The image is untouched if nothing is off."""
    alpha = image.getchannel("A") if image.mode == "RGBA" else None
    x = torch.nan_to_num(to_tensor(image, device), nan=0.0, posinf=1.0, neginf=0.0)
    ref = to_tensor(reference, device) if reference is not None else None
    p = plan(x, s, ref)
    if not p.changes() or s["strength"] <= 0:
        return image, p
    out = apply(x, p, s["ref_strength"] if ref is not None else 0.0)
    if s["strength"] < 1.0:
        out = torch.lerp(x, out, s["strength"])
    result = to_image(out)
    if alpha is not None:
        result.putalpha(alpha)
    return result, p
