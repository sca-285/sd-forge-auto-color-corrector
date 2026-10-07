"""Repairs that Auto measures before it fixes: JPEG blocking and ringing,
noise, a tilted horizon. Pure torch, (B, 3, H, W) sRGB in 0..1.

JPEG de-blocking and de-ringing came over from Digital Mastering; here they
are applied only as strongly as the blocking actually measured calls for.
"""

from __future__ import annotations

import math

import torch
import torch.nn.functional as F

from . import ops


def _gauss(x, sigma):
    if sigma <= 0:
        return x
    r = max(1, int(math.ceil(3 * sigma)))
    t = torch.arange(-r, r + 1, device=x.device, dtype=x.dtype)
    k = torch.exp(-0.5 * (t / sigma) ** 2)
    k = k / k.sum()
    c = x.shape[1]
    mode = "reflect" if r < min(x.shape[-2:]) else "replicate"
    x = F.conv2d(F.pad(x, (r, r, 0, 0), mode=mode), k.view(1, 1, 1, -1).expand(c, 1, 1, -1), groups=c)
    return F.conv2d(F.pad(x, (0, 0, r, r), mode=mode), k.view(1, 1, -1, 1).expand(c, 1, -1, 1), groups=c)


def _sobel(y):
    kx = y.new_tensor([[-1.0, 0.0, 1.0], [-2.0, 0.0, 2.0], [-1.0, 0.0, 1.0]]).view(1, 1, 3, 3) / 4.0
    p = F.pad(y, (1, 1, 1, 1), mode="replicate")
    gx = F.conv2d(p, kx)
    gy = F.conv2d(p, kx.transpose(2, 3))
    return torch.sqrt(gx * gx + gy * gy + 1e-12)


# ------------------------------------------------------------------ JPEG

def blockiness(x):
    """How much stronger the steps across the 8-pixel JPEG grid are than the
    steps inside the blocks: about 1.0 for a clean image, 1.2+ when blocking
    shows. Measured on the full-size image (resizing hides the grid)."""
    y = ops.luma(x)[0, 0]
    h, w = y.shape
    if h < 32 or w < 32:
        return 1.0
    dx = (y[:, 1:] - y[:, :-1]).abs()
    dy = (y[1:, :] - y[:-1, :]).abs()
    on_x = (torch.arange(w - 1, device=x.device) % 8) == 7
    on_y = (torch.arange(h - 1, device=x.device) % 8) == 7
    edge = dx[:, on_x].mean() + dy[on_y, :].mean()
    inner = dx[:, ~on_x].mean() + dy[~on_y, :].mean()
    return float(edge / inner.clamp_min(1e-6))


def deblock(x, strength):
    """Soften the two pixels either side of each 8x8 JPEG block boundary."""
    _, _, h, w = x.shape
    rows = torch.arange(h, device=x.device)
    cols = torch.arange(w, device=x.device)
    on_r = ((rows % 8 == 7) & (rows < h - 1)) | ((rows % 8 == 0) & (rows > 0))
    on_c = ((cols % 8 == 7) & (cols < w - 1)) | ((cols % 8 == 0) & (cols > 0))
    mask = (on_r.view(1, 1, h, 1) | on_c.view(1, 1, 1, w)).to(x.dtype)
    k = x.new_tensor([[1.0, 2.0, 1.0], [2.0, 4.0, 2.0], [1.0, 2.0, 1.0]]) / 16.0
    blurred = F.conv2d(F.pad(x, (1, 1, 1, 1), mode="replicate"), k.expand(3, 1, 3, 3), groups=3)
    return torch.lerp(x, blurred, mask * strength)


def dering(x, strength):
    """Smooth the flat areas right next to strong edges, where ringing lives."""
    halo = _sobel(ops.luma(x))
    halo = F.max_pool2d(halo, (1, 5), stride=1, padding=(0, 2))
    halo = F.max_pool2d(halo, (5, 1), stride=1, padding=(2, 0))
    halo = (halo * 3.0).clamp(0.0, 1.0)
    return torch.lerp(x, _gauss(x, 1.0), halo * strength)


# ------------------------------------------------------------------ noise

def noise_sigma(x):
    """Noise level (standard deviation, 0..1 scale) by Immerkaer's method,
    taken only over the flatter half of the picture so texture is not
    mistaken for noise. Uses at most a 1024 px centre crop."""
    _, _, h, w = x.shape
    if min(h, w) < 16:
        return 0.0
    ch, cw = min(h, 1024), min(w, 1024)
    t, l = (h - ch) // 2, (w - cw) // 2
    y = ops.luma(x[:, :, t:t + ch, l:l + cw])
    k = y.new_tensor([[1.0, -2.0, 1.0], [-2.0, 4.0, -2.0], [1.0, -2.0, 1.0]]).view(1, 1, 3, 3)
    resp = F.conv2d(y, k).abs()
    grad = _sobel(y)[:, :, 1:-1, 1:-1]
    flat = grad <= torch.quantile(grad.flatten()[::7].float(), 0.5)
    if int(flat.sum()) < 100:
        return 0.0
    return float(math.sqrt(math.pi / 2) / 6.0 * resp[flat].mean())


def denoise(x, amount):
    """Chroma noise smoothed hard (it is the ugly part), luma noise gently and
    only away from edges, so detail stays."""
    if amount <= 0:
        return x
    m = x.new_tensor([[0.299, 0.587, 0.114], [-0.169, -0.331, 0.5], [0.5, -0.419, -0.081]])
    ycc = torch.einsum("ij,bjhw->bihw", m, x)
    y, c = ycc[:, 0:1], ycc[:, 1:3]
    c = torch.lerp(c, _gauss(c, 1.5 + 2.5 * amount), min(1.0, amount * 1.5))
    edges = (_sobel(y) * 8.0).clamp(0.0, 1.0)
    y = torch.lerp(y, _gauss(y, 0.7 + 0.8 * amount), amount * (1.0 - edges))
    return torch.einsum("ij,bjhw->bihw", torch.linalg.inv(m), torch.cat((y, c), 1)).clamp(0.0, 1.0)


# ------------------------------------------------------------------ horizon

def tilt(x, limit=8.0):
    """(degrees to turn the picture to level it, confidence), from the long
    straight edges near horizontal and vertical (horizons, buildings, door
    frames). Confidence is how far the winning direction stands above an even
    spread: around 1-2 for pictures without straight lines, 5 and up for
    streets and buildings."""
    y = ops.luma(x)
    s = 768.0 / max(y.shape[-2:])
    if s < 1.0:
        y = F.interpolate(y, scale_factor=s, mode="area")
    kx = y.new_tensor([[-1.0, 0.0, 1.0], [-2.0, 0.0, 2.0], [-1.0, 0.0, 1.0]]).view(1, 1, 3, 3)
    p = F.pad(y, (1, 1, 1, 1), mode="replicate")
    gx, gy = F.conv2d(p, kx), F.conv2d(p, kx.transpose(2, 3))
    # Structure tensor: the local edge direction and how consistent it is,
    # so long straight edges count and texture does not.
    jxx, jxy, jyy = _gauss(gx * gx, 4.0), _gauss(gx * gy, 4.0), _gauss(gy * gy, 4.0)
    energy = jxx + jyy
    coherence = torch.sqrt((jxx - jyy) ** 2 + 4 * jxy * jxy) / (energy + 1e-9)
    theta = 0.5 * torch.rad2deg(torch.atan2(2 * jxy, jxx - jyy))
    w = (energy * (coherence > 0.85)).flatten()
    dev = ((theta + 45.0) % 90.0 - 45.0).flatten()
    near = (dev.abs() <= limit) & (w > 0)
    if int(near.sum()) < 200:
        return 0.0, 0.0
    nb = int(limit * 8)                                       # quarter-degree bins
    idx = ((dev[near] + limit) / (2 * limit) * (nb - 1)).round().long()
    hist = torch.zeros(nb, device=x.device, dtype=x.dtype).index_add_(0, idx, w[near])
    smooth = F.conv1d(hist.view(1, 1, -1), x.new_tensor([[[1.0, 2.0, 3.0, 2.0, 1.0]]]) / 9.0, padding=2)[0, 0]
    k = int(smooth.argmax())
    # Sub-bin peak by a parabola through the three bins around it.
    off = 0.0
    if 0 < k < nb - 1:
        a, b, c = (float(v) for v in smooth[k - 1:k + 2])
        den = a - 2 * b + c
        off = 0.5 * (a - c) / den if abs(den) > 1e-12 else 0.0
    angle = -limit + 2 * limit * (k + off) / (nb - 1)
    return angle, float(smooth[k] / smooth.mean().clamp_min(1e-9))


def rotate(x, degrees):
    """Turn the picture and scale it just enough that no empty corner shows."""
    if abs(degrees) < 1e-3:
        return x
    _, _, h, w = x.shape
    t = math.radians(degrees)
    c, s = math.cos(t), math.sin(t)
    a = w / h
    zoom = abs(c) + abs(s) * max(a, 1.0 / a)
    yy, xx = torch.meshgrid(torch.linspace(-1, 1, h, device=x.device, dtype=x.dtype),
                            torch.linspace(-1, 1, w, device=x.device, dtype=x.dtype), indexing="ij")
    px, py = xx * a / zoom, yy / zoom
    gx = (px * c - py * s) / a
    gy = px * s + py * c
    grid = torch.stack((gx, gy), -1).unsqueeze(0).expand(x.shape[0], -1, -1, -1)
    return F.grid_sample(x, grid, mode="bicubic", padding_mode="border", align_corners=True).clamp(0.0, 1.0)
