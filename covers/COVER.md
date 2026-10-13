# Cover — what to change and where

Two A4 pages, the same size as the book: `cover.pdf` page 1 is the front cover and
page 2 is the back cover. `Neural_Operator_Book.tex` pulls them in with
`\includepdf` — the front as page 1 of the PDF (followed by the usual blank verso),
the back as the last page.

| File | What it holds |
| --- | --- |
| `cover.tex` | Every word on both covers, and where each block sits. Edit this to change text. |
| `art/front.png`, `art/back.png` | The artwork as the model returned it (2:3). |
| `art/front_a4.png`, `art/back_a4.png` | The same artwork trimmed to A4. These are the files `cover.tex` uses. |
| `art/*.prompt.txt`, `art/*.json` | The exact prompt sent, the model, the pixel counts, the prompt hash. |
| `../figures/make_covers.py` | The generator. Also does the A4 trim. |
| `cover.pdf` | The build output. Not hand-edited. |

## Rebuild

```bash
cd book/covers && latexmk -pdf cover.tex     # writes cover.pdf
cd .. && latexmk -pdf Neural_Operator_Book.tex
```

`cover.pdf` has to exist before the book builds, because `\includepdf` reads it as a
file. If you only change the book text, the second command is enough.

## Changing the words

Each block is one TikZ node. The node options are the layout, the body is the copy.

**Front, title block** (`cover.tex:49`)

```
\node[inner sep=0pt,anchor=north west,text width=284pt,align=left]
  at ([xshift=258pt,yshift=-566pt]current page.north west)
```

- `xshift` / `yshift` — where the block starts, measured from the top-left corner of
  the page, in pt. `yshift` is negative because it moves down. A4 is 595.276 × 841.89 pt.
- `text width` — how wide the block is before it wraps. Keep `xshift + text width`
  under about 540 pt or the type runs into the right margin.
- `\fontsize{24}{28.5}` — size over leading. Each line of the block has its own.
- `\vspace{...}` — the gaps between title, rule, subtitle, author, edition.

The title breaks by hand after "Infinite-Dimensional" so the compound stays on one
line. It cannot be set larger than 24 pt at this measure: the phrase is 278 pt at
24 pt and 313 pt at 27 pt, and the block is only 284 pt wide because its left edge
is pinned to the 43 % line, where the artwork's bands start.

Current copy, top to bottom:

```
The Infinite-Dimensional                24 pt bold, primary (navy)
Learner
——                                      58 pt × 2.2 pt rule, secondary (maroon)
Neural Operators                        15.5 pt bold, secondary
From Function Spaces to                 11.5 pt, accent (steel blue)
Scientific Machine Learning
Dr Raktim Mondol                        13 pt, primary
First Edition • 2026                    9 pt, 52 % black
```

**Back, top-left running title** (`cover.tex:73`) — small caps title at 12 pt plus the
author at 9.5 pt, sitting in the clear space above the curve.

**Back, blurb** (`cover.tex:80`) — 9.8 pt, 246 pt wide, in the pocket right of the dot
field. Current copy:

> A neural operator learns a map between function spaces. Its input is a coefficient
> field, its output a solution field, and neither is tied to the grid the training data
> happened to live on. That change of address is what makes these models worth the
> functional analysis they require.
>
> The book works from the estimates that bound approximation error, through the Fourier
> layer and its relatives, to fluid flow, subsurface transport, structural dynamics,
> imaging and weather. Where a number appears it is either computed by a script in the
> accompanying repository or read from the cited paper, and the arithmetic claims are
> checked in Lean.
>
> Written by AI, prompted, edited and reviewed by Dr Raktim Mondol
> First Edition • 2026

The second paragraph's last sentence is a claim about how the book was sourced. It is
true, and it is also the kind of thing that reads as an internal note rather than as
copy. Cut it and the paragraph ends at "imaging and weather."

## Keeping the type out of the artwork

The blocks sit where the two compositions have no ink. Measured off the trimmed
rasters, as a fraction of the page:

- **Front** — clear right of 42 % width below 55 % height; clear below 85 % height
  across the full width. The wave comes down the left edge to about 80 %.
- **Back** — the whole upper-left quadrant is clear down to 55 % height; right of
  46 % width is clear below 60 % height. The dot field owns the lower-left.

If you move a block outside those pockets, or make it taller, it lands on the art.
Render and look before you commit:

```bash
pdftoppm -r 100 -f 1 -l 1 -png cover.pdf /tmp/c && pdftoppm -r 100 -f 2 -l 2 -png cover.pdf /tmp/c
```

## Regenerating the artwork

```bash
cd book/figures
GEMINI_API_KEY=... IMAGE_MODEL=gemini-3-pro-image python3 make_covers.py   # calls the model
python3 make_covers.py --fit-only                                          # only redo the A4 trim
```

Two rules the generator enforces, both worth keeping:

1. **No text in the image, ever.** The prompt says so explicitly. An image model asked
   to write a title produces a plausible title with one letter wrong, and asked for an
   identifier it invents one. All type is set in `cover.tex`.
2. **The A4 trim comes off the top.** 2:3 is taller than A4, so 5.1 % of the height is
   surplus; trimming it in Python rather than letterboxing in LaTeX is what lets the
   artwork bleed to all four edges. `CROP` at `make_covers.py:112` controls the anchor.

A new generation moves everything: the ink lands somewhere else, the pockets change,
and the node coordinates need re-measuring against the new raster.

## Identifiers

Neither page carries an ISBN, an ISSN, a DOI or a barcode. If that changes for a print
run, the space to put one is the front cover's bottom-right or the back cover's
bottom-right, both of which are empty.
