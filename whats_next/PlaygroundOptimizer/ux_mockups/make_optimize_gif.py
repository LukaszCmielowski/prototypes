#!/usr/bin/env python3
"""Generate an animated GIF visualizing Playground 'Find better settings'."""

from __future__ import annotations

import math
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 960, 540
FPS = 12
OUT = Path(__file__).with_name("playground_optimize.gif")

# Palette (RHOAI-ish, avoid purple clichés)
BG = (18, 22, 28)
PANEL = (28, 34, 42)
PANEL2 = (36, 44, 54)
LINE = (70, 80, 94)
TEXT = (240, 242, 245)
MUTED = (160, 170, 182)
BLUE = (0, 120, 212)
BLUE_GLOW = (64, 168, 255)
GREEN = (62, 160, 70)
GOLD = (230, 180, 50)
WHITE = (255, 255, 255)
RED = (201, 25, 11)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


F_TITLE = font(28, True)
F_H = font(20, True)
F_BODY = font(15)
F_SMALL = font(12)
F_TINY = font(11)
F_SCORE = font(26, True)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def rounded(draw: ImageDraw.ImageDraw, xy, r, fill=None, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def glow_circle(img: Image.Image, cx, cy, radius, color, alpha=80):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(4, 0, -1):
        a = int(alpha * (i / 4) * 0.45)
        d.ellipse(
            [cx - radius * i * 0.55, cy - radius * i * 0.55, cx + radius * i * 0.55, cy + radius * i * 0.55],
            fill=(*color, a),
        )
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(*color, min(255, alpha + 40)))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def draw_chrome(draw: ImageDraw.ImageDraw, subtitle: str):
    rounded(draw, (24, 24, W - 24, H - 24), 16, fill=PANEL, outline=LINE, width=1)
    # top bar
    rounded(draw, (24, 24, W - 24, 72), 16, fill=PANEL2)
    draw.rectangle([24, 56, W - 24, 72], fill=PANEL2)
    draw.ellipse([40, 38, 54, 52], fill=RED)
    draw.text((64, 36), "OpenShift AI  ·  Playground", font=F_BODY, fill=TEXT)
    draw.text((W - 40, 38), subtitle, font=F_SMALL, fill=MUTED, anchor="ra")


def scene_playground(t: float) -> Image.Image:
    """Chat + settings, then spotlight on Find better settings."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw_chrome(draw, "Try & tweak")

    # chat pane
    rounded(draw, (44, 92, 620, H - 44), 12, fill=(24, 28, 34), outline=LINE)
    draw.text((64, 108), "You", font=F_TINY, fill=MUTED)
    rounded(draw, (64, 128, 500, 168), 10, fill=BLUE)
    draw.text((78, 140), "Explain binary search with a Python example", font=F_SMALL, fill=WHITE)

    draw.text((64, 190), "Assistant", font=F_TINY, fill=MUTED)
    rounded(draw, (64, 210, 560, 300), 10, fill=PANEL2, outline=LINE)
    draw.text((78, 224), "Binary search finds a value by cutting the list in half…", font=F_SMALL, fill=TEXT)
    draw.text((78, 248), "def binary_search(arr, target):", font=F_TINY, fill=BLUE_GLOW)
    draw.text((78, 268), "    …", font=F_TINY, fill=MUTED)

    # settings pane
    rounded(draw, (640, 92, W - 44, H - 44), 12, fill=(24, 28, 34), outline=LINE)
    draw.text((660, 108), "Your settings", font=F_H, fill=TEXT)
    for i, (label, val) in enumerate(
        [("Model", "QLM 3.3"), ("Creativity", "Low"), ("Tools", "On")]
    ):
        y = 150 + i * 42
        draw.text((660, y), label, font=F_TINY, fill=MUTED)
        rounded(draw, (660, y + 16, W - 64, y + 40), 6, fill=PANEL2, outline=LINE)
        draw.text((672, y + 22), val, font=F_SMALL, fill=TEXT)

    # CTA pulse
    pulse = 0.5 + 0.5 * math.sin(t * math.pi * 2)
    btn_y0, btn_y1 = H - 130, H - 88
    glow = int(40 + 80 * pulse)
    img = glow_circle(img, (640 + W - 44) // 2, (btn_y0 + btn_y1) // 2, 28 + 10 * pulse, BLUE, glow)
    draw = ImageDraw.Draw(img)
    rounded(draw, (660, btn_y0, W - 64, btn_y1), 8, fill=BLUE)
    draw.text(((660 + W - 64) // 2, (btn_y0 + btn_y1) // 2), "Find better settings", font=F_BODY, fill=WHITE, anchor="mm")

    if t > 0.55:
        alpha = ease((t - 0.55) / 0.45)
        tip = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        td = ImageDraw.Draw(tip)
        td.text((W // 2, H - 28), "One button. Many tries. Clear ranking.", font=F_BODY, fill=(*MUTED, int(255 * alpha)), anchor="mm")
        img = Image.alpha_composite(img.convert("RGBA"), tip).convert("RGB")

    return img


def scene_searching(t: float) -> Image.Image:
    """Orbiting config nodes converging into evaluation."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw_chrome(draw, "Working…")

    cx, cy = W // 2, H // 2 + 10
    draw.text((W // 2, 100), "Trying setting combinations", font=F_H, fill=TEXT, anchor="ma")
    draw.text((W // 2, 128), "Models  ·  Instructions  ·  Creativity  ·  Tools", font=F_SMALL, fill=MUTED, anchor="ma")

    # progress ring
    ring_r = 110
    img = img.convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r], outline=(*LINE, 180), width=4)
    # arc progress
    extent = int(360 * ease(t))
    # approximate arc with pieslice outline trick
    od.arc([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r], start=-90, end=-90 + extent, fill=(*BLUE_GLOW, 255), width=6)
    # center score climbing
    score = int(lerp(40, 81, ease(t)))
    od.text((cx, cy - 8), f"{score}%", font=F_SCORE, fill=(*GREEN, 255), anchor="mm")
    od.text((cx, cy + 22), "best so far", font=F_TINY, fill=(*MUTED, 255), anchor="mm")
    img = Image.alpha_composite(img, overlay)

    # orbiting chips
    labels = ["Granite", "Llama", "QLM", "T=0", "T=0.2", "Tools on", "Tools off", "Concise", "Tutor"]
    for i, lab in enumerate(labels):
        ang = t * math.pi * 2 * (0.35 + i * 0.03) + i * (2 * math.pi / len(labels))
        r = 170 + 12 * math.sin(t * 6 + i)
        x = cx + r * math.cos(ang)
        y = cy + r * math.sin(ang) * 0.72
        chip = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(chip)
        tw = 54 + len(lab) * 4
        cd.rounded_rectangle([x - tw / 2, y - 12, x + tw / 2, y + 12], 8, fill=(*PANEL2, 230), outline=(*BLUE, 160))
        cd.text((x, y), lab, font=F_TINY, fill=(*TEXT, 255), anchor="mm")
        img = Image.alpha_composite(img, chip)

    # particles inward
    rng = np.random.default_rng(7)
    for i in range(28):
        a = rng.random() * 2 * math.pi
        dist = lerp(220, 40, ease((t + rng.random() * 0.2) % 1.0))
        px = cx + dist * math.cos(a + t)
        py = cy + dist * math.sin(a + t) * 0.7
        d = ImageDraw.Draw(img)
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=BLUE_GLOW)

    return img.convert("RGB")


def scene_leaderboard(t: float) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw_chrome(draw, "See the winners")

    draw.text((W // 2, 96), "Here’s what worked best", font=F_H, fill=TEXT, anchor="ma")
    lift = ease(min(1.0, t * 1.2))
    draw.text(
        (W // 2, 124),
        f"Best score 83%   ·   +{int(21 * lift)} pts vs your old settings",
        font=F_BODY,
        fill=GREEN if lift > 0.4 else MUTED,
        anchor="ma",
    )

    rows = [
        ("1", "Granite · short & precise", "83%", GOLD, True),
        ("2", "Llama · patient tutor", "79%", (180, 180, 190), False),
        ("3", "Granite · no extra tools", "71%", (180, 140, 100), False),
        ("—", "Your old settings", "62%", MUTED, False),
    ]

    for i, (rank, title, score, accent, win) in enumerate(rows):
        appear = ease(max(0.0, (t - i * 0.12) / 0.35))
        if appear <= 0:
            continue
        y = 160 + i * 70
        x_off = int((1 - appear) * 40)
        alpha_bg = PANEL2 if not win else (32, 52, 38)
        rounded(draw, (80 + x_off, y, W - 80, y + 58), 12, fill=alpha_bg, outline=GREEN if win else LINE, width=2 if win else 1)
        # badge
        bx, by = 110 + x_off, y + 29
        draw.ellipse([bx - 18, by - 18, bx + 18, by + 18], fill=accent if rank != "—" else LINE)
        draw.text((bx, by), rank, font=F_BODY, fill=BG if rank != "—" else TEXT, anchor="mm")
        draw.text((150 + x_off, y + 18), title, font=F_BODY, fill=TEXT)
        if win and appear > 0.6:
            draw.text((150 + x_off, y + 38), "Recommended", font=F_TINY, fill=GREEN)
        draw.text((W - 110, y + 29), score, font=F_SCORE, fill=GREEN if win else TEXT, anchor="rm")

    return img


def scene_save(t: float) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw_chrome(draw, "Save your agent")

    # check burst
    cx, cy = W // 2, 210
    scale = ease(min(1.0, t * 1.5))
    img = glow_circle(img, cx, cy, int(36 * scale), GREEN, int(100 * scale))
    draw = ImageDraw.Draw(img)
    r = int(34 * scale)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN)
    # checkmark
    if scale > 0.4:
        draw.line([(cx - 12, cy), (cx - 2, cy + 12), (cx + 16, cy - 12)], fill=WHITE, width=5)

    fade = ease(max(0.0, (t - 0.35) / 0.5))
    draw.text((W // 2, 280), "Python coding helper", font=F_H, fill=lerp_color(BG, TEXT, fade), anchor="ma")
    draw.text((W // 2, 312), "Saved from optimizer winner  ·  83% quality", font=F_BODY, fill=lerp_color(BG, MUTED, fade), anchor="ma")

    if fade > 0.2:
        rounded(draw, (W // 2 - 160, 360, W // 2 + 160, 408), 10, fill=BLUE)
        draw.text((W // 2, 384), "Agent ready to use", font=F_BODY, fill=WHITE, anchor="mm")

    # confetti
    rng = np.random.default_rng(3)
    for i in range(40):
        px = rng.integers(60, W - 60)
        py = lerp(-20, H + 20, (t * 0.7 + rng.random()) % 1.0)
        color = [GOLD, BLUE_GLOW, GREEN, WHITE][i % 4]
        draw.rectangle([px, py, px + 6, py + 10], fill=color)

    return img


def scene_title(t: float) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    a = ease(t)
    draw.text((W // 2, H // 2 - 30), "Find better settings", font=F_TITLE, fill=lerp_color(BG, TEXT, a), anchor="mm")
    draw.text((W // 2, H // 2 + 14), "Playground Optimize  ·  stop guessing", font=F_BODY, fill=lerp_color(BG, MUTED, a), anchor="mm")
    # underline grow
    uw = int(220 * a)
    draw.rectangle([W // 2 - uw // 2, H // 2 + 40, W // 2 + uw // 2, H // 2 + 44], fill=BLUE)
    return img


def build_frames() -> list[Image.Image]:
    frames: list[Image.Image] = []
    # title 1.2s
    for i in range(int(1.2 * FPS)):
        frames.append(scene_title(i / (1.2 * FPS)))
    # playground 2.2s
    for i in range(int(2.2 * FPS)):
        frames.append(scene_playground(i / (2.2 * FPS)))
    # searching 2.8s
    for i in range(int(2.8 * FPS)):
        frames.append(scene_searching(i / (2.8 * FPS)))
    # leaderboard 2.6s
    for i in range(int(2.6 * FPS)):
        frames.append(scene_leaderboard(i / (2.6 * FPS)))
    # save 2.2s
    for i in range(int(2.2 * FPS)):
        frames.append(scene_save(i / (2.2 * FPS)))
    # hold last
    frames.extend([frames[-1]] * int(0.8 * FPS))
    return frames


def main():
    frames = build_frames()
    # slightly compress palette for smaller gif
    arrays = [np.asarray(f.convert("P", palette=Image.ADAPTIVE, colors=128).convert("RGB")) for f in frames]
    imageio.mimsave(
        OUT,
        arrays,
        duration=1 / FPS,
        loop=0,
    )
    print(f"Wrote {OUT} ({len(frames)} frames, {OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
