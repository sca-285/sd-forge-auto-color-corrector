"""Colour maths. Pure torch, (B, 3, H, W) float sRGB in 0..1, no WebUI imports."""

from __future__ import annotations

import torch

LUMA = (0.2126, 0.7152, 0.0722)   # Rec.709, the sRGB primaries


def luma(x):
    w = x.new_tensor(LUMA).view(1, 3, 1, 1)
    return (x * w).sum(1, keepdim=True)


def srgb_to_linear(x):
    x = x.clamp(0.0, 1.0)
    return torch.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(x):
    x = x.clamp(0.0, 1.0)
    return torch.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055)


def chroma(x):
    """max - min of the channels: 0 for greys, up to 1 for pure colours."""
    return x.amax(1, keepdim=True) - x.amin(1, keepdim=True)


def opponent(x):
    """Two colour axes that are 0 on greys: a = green..magenta, b = blue..yellow."""
    r, g, b = x[:, 0:1], x[:, 1:2], x[:, 2:3]
    return (r + b) / 2 - g, (r + g) / 2 - b


def white_balance(x, gains):
    """Channel gains in linear light, as a camera's white balance works."""
    return linear_to_srgb(srgb_to_linear(x) * gains.view(1, 3, 1, 1))


def levels(x, black, white):
    """Map black..white to 0..1 on all channels alike, so colours keep their hue."""
    return ((x - black) / max(white - black, 1e-3)).clamp(0.0, 1.0)


def _scale_luma(x, new_y, y):
    """Give x the luminance new_y while keeping each pixel's hue and saturation."""
    out = x * (new_y / y.clamp_min(1e-4))
    # Where a channel would clip, desaturate the pixel towards its own
    # luminance just enough to fit, instead of letting the hue shift.
    top = out.amax(1, keepdim=True)
    ny = new_y.clamp(0.0, 1.0)
    t = ((1.0 - ny) / (top - ny).clamp_min(1e-6)).clamp(0.0, 1.0)
    t = torch.where(top > 1.0, t, torch.ones_like(t))
    return (ny + (out - ny) * t).clamp(0.0, 1.0)


def exposure(x, stops):
    """Exposure in linear light with a shoulder: mids move by `stops`, black
    stays black and white stays white, so nothing clips."""
    g = 2.0 ** stops
    lin = srgb_to_linear(x)
    y = luma(lin)
    new_y = g * y / (1.0 + (g - 1.0) * y)
    return linear_to_srgb(_scale_luma(lin, new_y, y))


def contrast(x, amount, pivot):
    """S-curve on luminance around `pivot` (sRGB): + more contrast, - less.
    0, 1 and the pivot stay where they are."""
    p = min(max(float(pivot), 0.05), 0.95)
    k = 1.0 + amount
    y = luma(x).clamp(0.0, 1.0)
    lo = p * (y / p).clamp(0.0, 1.0) ** k
    hi = 1.0 - (1.0 - p) * ((1.0 - y) / (1.0 - p)).clamp(0.0, 1.0) ** k
    new_y = torch.where(y < p, lo, hi)
    return _scale_luma(x, new_y, y)


def vibrance(x, amount):
    """Raise (or lower) colour where it is weak, leave strong colour and skin
    alone. amount 1 roughly doubles the colour of a dull pixel."""
    y = luma(x)
    c = chroma(x)
    weight = (1.0 - c).clamp(0.0, 1.0) ** 2
    # Skin and other warm mid-saturation tones: red highest, then green, then blue.
    r, g, b = x[:, 0:1], x[:, 1:2], x[:, 2:3]
    skin = ((r > g) & (g > b) & (c > 0.08) & (c < 0.6)).to(x.dtype)
    weight = weight * (1.0 - 0.6 * skin)
    return (y + (x - y) * (1.0 + amount * weight)).clamp(0.0, 1.0)


# ------------------------------------------------------------- CIELAB (D65)

_M = ((0.4124, 0.3576, 0.1805), (0.2126, 0.7152, 0.0722), (0.0193, 0.1192, 0.9505))
_WHITE = (0.95047, 1.0, 1.08883)


def to_lab(x):
    lin = srgb_to_linear(x)
    m = x.new_tensor(_M)
    xyz = torch.einsum("ij,bjhw->bihw", m, lin) / x.new_tensor(_WHITE).view(1, 3, 1, 1)
    f = torch.where(xyz > 0.008856, xyz.clamp_min(1e-8) ** (1 / 3), 7.787 * xyz + 16 / 116)
    return torch.cat((116 * f[:, 1:2] - 16, 500 * (f[:, 0:1] - f[:, 1:2]), 200 * (f[:, 1:2] - f[:, 2:3])), 1)


def from_lab(lab):
    fy = (lab[:, 0:1] + 16) / 116
    f = torch.cat((fy + lab[:, 1:2] / 500, fy, fy - lab[:, 2:3] / 200), 1)
    xyz = torch.where(f > 0.2069, f ** 3, (f - 16 / 116) / 7.787) * lab.new_tensor(_WHITE).view(1, 3, 1, 1)
    lin = torch.einsum("ij,bjhw->bihw", torch.linalg.inv(lab.new_tensor(_M)), xyz)
    return linear_to_srgb(lin)


def match_stats(x, ref_mean, ref_std, src_mean, src_std, amount):
    """Reinhard colour transfer in Lab: move x's per-channel mean and spread
    towards the reference's. Lightness moves half as far, so the reference
    sets the colour more than the exposure."""
    lab = to_lab(x)
    scale = (ref_std / src_std.clamp_min(1e-3)).clamp(0.5, 2.0)
    moved = (lab - src_mean) * scale + ref_mean
    w = x.new_tensor([0.5, 1.0, 1.0]).view(1, 3, 1, 1) * amount
    return from_lab(torch.lerp(lab, moved, w)).clamp(0.0, 1.0)
