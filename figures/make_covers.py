#!/usr/bin/env python3
"""Generate the book's cover artwork with gemini-3-pro-image.

Provenance rules, same as make_diagrams.py and for the same reason: the prompt is
committed here, the exact text sent is written beside the image, and a JSON
sidecar records model, prompt hash, aspect ratio and date. Re-running reproduces
the shipped files.

The critical constraint for a COVER is different from a diagram. A cover carries
the book's title, subtitle, author and blurb, and an image model asked to write
those will produce a plausible-looking title with a letter out of place, or worse,
a plausible-looking ISBN. So the artwork is generated with NO TEXT AT ALL, and
every word on the front and back is typeset by LaTeX in covers/cover.tex, using
the book's own palette and Computer Modern. The model draws; the typesetter
writes. That split is the whole design.

Run:  GEMINI_API_KEY=... python3 make_covers.py
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MODEL = os.environ.get("IMAGE_MODEL", "gemini-3-pro-image")
HOST = "https://generativelanguage.googleapis.com"
HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "covers" / "art"

NAVY = "deep navy blue (hex 123060)"
MAROON = "muted crimson (hex 7d202d)"
STEEL = "steel blue (hex 2a6f97)"

STYLE = (
    "Abstract editorial book-cover artwork, refined and quiet, for a graduate "
    "monograph on mathematics and machine learning. Flat vector-like rendering with "
    f"subtle depth, restrained palette of {NAVY}, {STEEL}, {MAROON} and warm off-white. "
    "Generous negative space, precise geometry, no photorealism, no gradients that "
    "look like stock art, no lens flare, no glow, no stars, no circuit boards, no "
    "gears, no human figures, no hands, no human faces, no robots. "
    "ABSOLUTELY NO TEXT, no letters, no words, no numbers, no labels, no axis ticks, "
    "no mathematical symbols, no logos, no watermark, no signature, no barcode."
)

PROMPTS: dict[str, dict] = {
    "front": {
        "aspect": "2:3",
        "text": (
            "Composition: a single continuous wave entering from the lower left and "
            "resolving, as it travels upward and right, into a small number of clean "
            "horizontal bands of decreasing detail, then into a sparse field of dots "
            "near the top right. Read as one object becoming a few numbers: a smooth "
            "function resolving into its retained modes. The wave is drawn as a thin "
            f"crisp line in {STEEL}; the bands are flat {NAVY} shapes with one {MAROON} "
            "accent band; the dots are small and evenly spaced. Background warm "
            "off-white. Asymmetric, editorial, calm, high contrast between the fine "
            "line and the flat shapes. Leave the whole lower third nearly empty for a "
            "title block."
        ),
    },
    "back": {
        "aspect": "2:3",
        "text": (
            "Composition: the inverse reading of the same idea, for a back cover. A "
            "sparse regular grid of small dots at the lower left that, moving upward "
            "and to the right, merges into an increasingly smooth continuous curve, "
            "until at the top it is a single unbroken line. Points becoming a function. "
            f"Dots in {NAVY}, the emerging curve in {STEEL} with one short {MAROON} "
            "segment near the middle. Background warm off-white, very quiet, most of "
            "the canvas empty so body text can sit on it. Editorial, minimal, calm."
        ),
    },
}


def call(prompt: str, aspect: str) -> tuple[bytes, tuple[int, int]]:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("IMAGE_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set; refusing to run silently.")
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            # A4 is 210:297 = 1:1.414; 2:3 = 1:1.5 is the nearest portrait the model
            # offers, and cover.tex crops the surplus rather than letterboxing it.
            "imageConfig": {"aspectRatio": aspect},
        },
    }
    req = urllib.request.Request(
        f"{HOST}/v1beta/models/{MODEL}:generateContent",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.load(r)
    for p in data["candidates"][0]["content"]["parts"]:
        if "inlineData" in p:
            from io import BytesIO
            from PIL import Image
            im = Image.open(BytesIO(base64.b64decode(p["inlineData"]["data"]))).convert("RGB")
            buf = BytesIO()
            im.save(buf, format="PNG", optimize=True)
            return buf.getvalue(), im.size
    raise RuntimeError("no image part returned")


CROP = {
    # The models deliver 2:3; A4 is 1:1.4142, so 5.1% of the height is surplus.
    # Trimming it here rather than letterboxing in LaTeX means the artwork bleeds
    # to all four page edges and no background-colour strip can show at the sides
    # when the page is merged into the book. Both trims come off the top, where
    # the two compositions are emptiest: on the front nothing is clipped above the
    # dot field, and on the back the cut stays above the curve's apex. The lower
    # half is left whole because that is where cover.tex puts the type.
    "front": "top",
    "back": "top",
}


def fit(name: str) -> tuple[int, int]:
    """Crop art/<name>.png to the A4 ratio and write art/<name>_a4.png."""
    from PIL import Image

    src = OUT / f"{name}.png"
    im = Image.open(src).convert("RGB")
    w, h = im.size
    want = 210.0 / 297.0
    have = w / h
    if have > want:
        nw = int(round(h * want))
        off = 0 if CROP[name] == "left" else (w - nw if CROP[name] == "right" else (w - nw) // 2)
        box = (off, 0, off + nw, h)
    else:
        nh = int(round(w / want))
        off = 0 if CROP[name] == "top" else (h - nh if CROP[name] == "bottom" else (h - nh) // 2)
        box = (0, off, w, off + nh)
    out = im.crop(box)
    out.save(OUT / f"{name}_a4.png", format="PNG", optimize=True)
    return out.size


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if "--fit-only" in sys.argv:
        for name in PROMPTS:
            size = fit(name)
            sidecar = OUT / f"{name}.json"
            if sidecar.exists():  # the shipped raster changed shape, so say so
                meta = json.loads(sidecar.read_text())
                meta["a4_pixels"] = list(size)
                meta["a4_crop"] = CROP[name]
                sidecar.write_text(json.dumps(meta, indent=2) + "\n")
            print(f"refit {name}_a4.png {size[0]}x{size[1]}")
        return 0
    for name, spec in PROMPTS.items():
        prompt = f"{STYLE}\n\n{spec['text']}"
        blob, size = call(prompt, spec["aspect"])
        (OUT / f"{name}.png").write_bytes(blob)
        (OUT / f"{name}.prompt.txt").write_text(prompt + "\n")
        fitted = fit(name)
        meta = {
            "name": f"{name} cover artwork",
            "model": MODEL,
            "requested_aspect": spec["aspect"],
            "pixels": list(size),
            "a4_pixels": list(fitted),
            "a4_crop": CROP[name],
            "content_policy": "no text of any kind; all cover typography is set by "
                              "covers/cover.tex so the model cannot garble a title "
                              "or invent an identifier",
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "bytes": len(blob),
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        (OUT / f"{name}.json").write_text(json.dumps(meta, indent=2) + "\n")
        print(f"wrote {name}.png {size[0]}x{size[1]} -> {name}_a4.png "
              f"{fitted[0]}x{fitted[1]}  sha {meta['prompt_sha256'][:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
