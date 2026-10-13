#!/usr/bin/env python3
"""Generate the book's structural diagrams with gemini-3-pro-image.

WHY THIS FILE EXISTS. Seven figures in this book were AI-generated rasters with
no generating script, no prompt, and no data archive, and three of them were
byte-identical copies of files named Gemini_Generated_Image_*.jpg. Their labels
were wrong in ways a reader could not detect: an axis triad printed Z, Z, X; a
colorbar running +20, +10, 0, -15, -30; a static-pressure scale of 0-1000 Pa on
a 10-70 m/s external flow. The defect was never "made by a model". It was
"unaccountable".

So this file keeps the model and removes the unaccountability:

  1. Every prompt is committed here, verbatim, and the exact text sent is
     written next to the image as <name>.prompt.txt with the model, the date and
     a sha256 of the prompt. A figure can be re-run and audited.
  2. A diagram may only carry STRUCTURAL content: named blocks, arrows,
     relations, and symbols the surrounding text defines. It may never carry a
     measured value, a data curve, an axis tick, a colorbar or a field rendering.
     Anything numeric is COMPUTED in make_figures.py instead, from an exactly
     solvable model, and this split is the whole point.
  3. The output is inspected before it is committed. A label that is misspelled,
     a box that contradicts the chapter, or stray invented text means the figure
     is regenerated or dropped, not shipped with an apology in the caption.
  4. Captions of these plates say they are schematic renderings of the
     construction defined in the text. They do not present a picture as evidence.

Run:  GEMINI_API_KEY=... python3 make_diagrams.py [name ...]
Without a key it exits 1 rather than silently skipping, so a missing figure is
never mistaken for an up-to-date one.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MODEL = os.environ.get("IMAGE_MODEL", "gemini-3-pro-image")
HOST = "https://generativelanguage.googleapis.com"
HERE = Path(__file__).resolve().parent
OUT = HERE / "generated"

STYLE = (
    "Minimal academic block diagram for a graduate monograph. Black strokes on white, "
    "thin rules, serif type matching Computer Modern, no shading, no gradients, no 3D "
    "extrusion, no icons, no decorative imagery, no drop shadows. Generous white margin. "
    "Spelling must be exact and every symbol must be typeset as mathematics. "
    "Render no text other than what is listed below."
)

# Structural content only. Every label is taken from the host chapter's own prose,
# equation or table; none is a measurement.
PROMPTS: dict[str, dict] = {
    "fig_fno_spectral_layer": {
        "host": "chapters/part2/03-fourier-neural-operators-fno-from-scratch.tex",
        "text": (
            "A single-row pipeline with a bypass wire. The leftmost element is the text $v$ with "
            "shape $(B, C_{\\mathrm{in}}, H, W)$ written beneath it, and a single horizontal "
            "arrow leaves $v$ to the right. Draw no other arrow touching $v$ and nothing "
            "above it. The input splits: one "
            "branch goes down and around the whole row as a bypass wire labelled "
            "$W v + b$ (pointwise), rejoining at the final summing node; the other branch "
            "passes left to right through four boxes joined by rightward arrows:\n"
            "  1. rfft2\n"
            "  2. keep $|k| \\le k_{\\max}$\n"
            "  3. multiply by $R_{\\phi}$\n"
            "  4. irfft2\n"
            "After box 4 the two branches meet at a circle containing a plus sign, and the "
            "output arrow to the right is labelled $\\sigma$\n"
            "No numbers, no colorbar, no axes, no curves."
        ),
    },
    "fig_gino_pipeline": {
        "host": "chapters/part2/04-graph-neural-operators-gno-and-irregular-g.tex",
        "text": (
            "Five boxes in a row joined by rightward arrows, with a label above each box "
            "and one line of mathematics beneath it.\n"
            "  1. label 'Irregular surface mesh'   math $\\mathcal{M}_{\\mathrm{surf}}$\n"
            "  2. label 'Point-to-grid GNO encoder'  math 'surface to latent grid'\n"
            "  3. label 'Latent 3D Fourier layers'   math $\\Omega_{\\mathrm{latent}}$\n"
            "  4. label 'Grid-to-point GNO decoder'  math 'latent grid to surface'\n"
            "  5. label 'Surface field at query points'  math $v_{\\mathrm{surf}}(x_j)$\n"
            "Box 3 is drawn slightly taller than the others. No numbers, no colorbar, no "
            "car, no mesh artwork, no field rendering, no curves."
        ),
    },
    "fig_architectures": {
        "host": "chapters/part1/04-operator-approximation-theory-and-universa.tex",
        "text": (
            "Three panels stacked vertically, each a small block diagram followed by one "
            "trailing line of text. Panel letters (a), (b), (c) at the left of each row.\n"
            "PANEL (a): boxes 'Fixed grid $\\mathcal{M}_N$' then 'MLP or CNN' then 'output "
            "vector'. Trailing line: 'parameters attach to grid indices'.\n"
            "PANEL (b): two boxes side by side, 'Branch: $m$ sensors' above 'Trunk: "
            "$y \\in \\Omega$', both feeding a circle containing a dot labelled 'inner "
            "product', which points to 'output'. Trailing line: 'branch attaches to sensor "
            "slots, trunk to the query coordinate'.\n"
            "PANEL (c): boxes 'lift' then 'band-limited multiplier $R_{\\phi}$' then "
            "'project'. Trailing line: 'parameters attach to wavenumbers'.\n"
            "No numbers, no colorbar, no curves, no artwork."
        ),
    },
    "fig_aero_setup": {
        "host": "chapters/part3/02-external-aerodynamics-and-surface-flows.tex",
        "text": (
            "A two-panel figure, panels labelled (a) and (b), side by side.\n"
            "PANEL (a): a simple closed 2D outline of a bluff body with a slanted rear "
            "window and a flat vertical base, drawn as a thin black polygon on a white "
            "background, sitting inside a larger rectangle representing the domain. Four "
            "leader lines point to it with these exact labels: 'inflow' at the left edge "
            "of the rectangle, 'outlet' at the right edge, 'body surface' at the top of "
            "the polygon, 'base and wake' at the vertical rear edge. Below the polygon, "
            "one line of mathematics: $a \\mapsto (p, \\tau_w)$ on the body surface.\n"
            "PANEL (b): a circle with three latitude arcs and three longitude arcs drawn inside "
            "it to indicate a sphere grid. Exactly two leader lines: one labelled 'pole' "
            "pointing to the single topmost point of the circle, and one labelled 'equator' "
            "pointing to the widest middle latitude arc. Below it, one line of text: a sphere of fixed radius.\n"
            "Absolutely no color, no colorbar, no shading, no numbers, no axis ticks, no "
            "flow field, no streamlines, no vectors, no curves of data."
        ),
    },
    "fig_subsurface_geometry": {
        "host": "chapters/part3/04-subsurface-multiphase-flow-and-carbon-stor.tex",
        "text": (
            "Two panels side by side, labelled (a) and (b). Clean textbook cross-section, thin black "
            "lines on white, generous spacing, no clutter.\n\n"
            "PANEL (a) - the setting. A wide rectangle divided by three horizontal lines into four "
            "stacked bands. Name each band inside its own band, left aligned, top to bottom: "
            "'overburden', 'caprock', 'reservoir', 'basement'. One straight fault line runs "
            "diagonally from the top edge to the bottom edge, cutting all four bands, and the bands "
            "right of the fault are drawn slightly lower than left of it so the throw is visible. "
            "Label it 'fault' with a short leader line onto the diagonal. A well enters vertically "
            "through overburden and caprock, then turns horizontal inside the reservoir; label it "
            "'injection well'. A shaded lens-shaped body sits in the reservoir touching the underside "
            "of the caprock; label it 'CO2 plume'. Add a small upward arrow under the lens and a "
            "rightward arrow along the top of the reservoir.\n\n"
            "PANEL (b) - what must be resolved. Three small copies of the same layer stack side by "
            "side, fault omitted for clarity. First: a small blob just above the well tip with an "
            "upward arrow, captioned 'rises'. Second: the blob flattened against the underside of the "
            "caprock, captioned 'arrests'. Third: a wide thin lens spread along the caprock, "
            "captioned 'spreads'. Below the three, one line: 'the far edge, not the interior, is what "
            "containment asks about'.\n\n"
            "No numbers, no depths, no thicknesses, no distances, no years, no axis ticks, no "
            "colorbar, no grayscale field. The only filled shape is the plume lens."
        ),
    },
    "fig_ct_geometry": {
        "host": "chapters/part3/06-medical-imaging-and-tomographic-reconstruc.tex",
        "text": (
            "Two panels side by side, labelled (a) and (b). Clean textbook diagram of a computed "
            "tomography scanner viewed from above. Thin black lines on white, no grayscale, no "
            "anatomical detail, no clutter.\n\n"
            "PANEL (a) - every angle measured. A circle in the middle labelled 'object', containing "
            "two small inner ellipses so it reads as an object with structure. Around it, evenly "
            "spaced all the way round, twelve source-detector pairs: each source is a small FILLED "
            "TRIANGLE pointing inward, and directly opposite it a short THICK RECTANGULAR BAR as the "
            "detector. Draw one straight line from one triangle through the object to its opposite "
            "bar, and put the single word 'ray' beside the middle of that line. In the upper-left "
            "corner place a two-row legend: first row a lone filled triangle followed by the word "
            "'source', second row a lone thick bar followed by the word 'detector'. Do not draw any "
            "leader line from those two words to the ring. Beneath the panel write 'every angle "
            "measured'.\n\n"
            "PANEL (b) - most angles missing. The same object circle with the same two inner "
            "ellipses, but only four source-detector pairs, at top, right, bottom and left, leaving "
            "wide empty gaps between them. Fill one of those empty wedge regions with light diagonal "
            "hatching and write 'missing angular range' beside the hatched region. Beneath the panel "
            "write 'most angles missing'.\n\n"
            "Both panels use the same object size and the same triangle and bar shapes, so the only "
            "visible difference is how many angles were sampled. The ray must be a plain thin line "
            "with NO arrowhead at either end, so it cannot be mistaken for a source. No numbers, no "
            "digits, no degrees, no axis ticks, no colorbar, no reconstructed image."
        ),
    },

}


def call(prompt: str) -> bytes:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("IMAGE_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set; refusing to run silently.")
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
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
            return base64.b64decode(p["inlineData"]["data"])
    raise RuntimeError("no image part returned")


def refit(src: bytes, name: str) -> tuple[bytes, tuple[int, int]]:
    r"""Trim the model's dead white margin and re-encode as true PNG.

    Two reasons. The API returns JPEG in a payload we name .png, and a file whose
    extension lies about its codec is a latent build failure. And every plate comes
    back 1408x768 whatever its content, so a five-box row or a stacked three-panel
    figure is mostly whitespace: at print width that wastes the resolution budget
    and shrinks the labels. Cropping to the ink restores each plate's real aspect
    and lets \includegraphics scale it at full width.
    """
    from io import BytesIO
    from PIL import Image, ImageChops

    im = Image.open(BytesIO(src)).convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    diff = ImageChops.difference(im, bg).convert("L")
    bbox = diff.point(lambda v: 255 if v > 12 else 0).getbbox()
    if bbox:
        pad = 14
        l = max(0, bbox[0] - pad)
        u = max(0, bbox[1] - pad)
        r = min(im.width, bbox[2] + pad)
        d = min(im.height, bbox[3] + pad)
        im = im.crop((l, u, r, d))
    out = BytesIO()
    im.save(out, format="PNG", optimize=True)
    return out.getvalue(), im.size


def main() -> int:
    if "--refit-only" in sys.argv:  # reprocess committed files, no API call
        from io import BytesIO
        from PIL import Image
        for name in PROMPTS:
            j = OUT / f"{name}.jpg"
            f = OUT / f"{name}.png"
            src = j if j.exists() else f
            if not src.exists():
                continue
            blob, size = refit(src.read_bytes(), name)
            f.write_bytes(blob)
            meta = json.loads((OUT / f"{name}.json").read_text())
            meta["bytes"], meta["pixels"] = len(blob), list(size)
            (OUT / f"{name}.json").write_text(json.dumps(meta, indent=2) + "\n")
            print(f"refit {name}.png {size[0]}x{size[1]} {len(blob)} bytes")
        return 0

    wanted = [a for a in (sys.argv[1:] or list(PROMPTS)) if not a.startswith("--")]
    OUT.mkdir(exist_ok=True)
    for name in wanted:
        spec = PROMPTS[name]
        prompt = f"{STYLE}\n\n{spec['text']}"
        blob, size = refit(call(prompt), name)
        (OUT / f"{name}.png").write_bytes(blob)
        (OUT / f"{name}.prompt.txt").write_text(prompt + "\n")
        meta = {
            "name": name,
            "model": MODEL,
            "host": spec["host"],
            "content_class": "structural schematic; carries no measured value",
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "bytes": len(blob),
            "pixels": list(size),
            "codec": "PNG (re-encoded from the model's JPEG; see refit)",
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        (OUT / f"{name}.json").write_text(json.dumps(meta, indent=2) + "\n")
        print(f"wrote {name}.png  {len(blob)} bytes  sha {meta['prompt_sha256'][:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
