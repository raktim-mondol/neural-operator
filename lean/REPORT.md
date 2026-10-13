# Lean 4 verification report

Project: `book/lean/BookProofs` — Lean v4.34.1 + mathlib (pinned in
`lean-toolchain` / `lake-manifest.json`).

```
lake build          # 40 theorems, 0 sorry, 0 admit, 0 axiom
```

Verification state at this writing: `elan`/`lake` are not on PATH in the book's
working environment, so the command above was not re-run here. The claim is
backed by the archived build artifacts — `.lake` oleans carry all 40 theorem
names with no `sorryAx` anywhere and are newer than their sources — and by
`grep -rn 'sorry\|admit\|axiom\|native_decide' BookProofs/`, which returns
nothing. No GitHub Actions workflow is configured: the standard lean-action
inputs do not support this nested project path, and the earlier template
workflows sat where GitHub would never read them; the 0-sorry invariant is a
local check, run after any edit to `BookProofs/`.

Two staleness notes after the revision cycle: line-number citations inside
.lean source comments refer to pre-revision line positions (labels are the
durable referents); and the section header at `Arithmetic.lean:151` phrases its
attribution to part1/05 more strongly than the book speaks --- part1/05 gives
the sufficient direction only, while the endpoint divergence is the project's
own addition. The Lean results themselves are unaffected.

`Arithmetic.lean` — 34 results. `Theory.lean` — 6 results.

## What this does and does not establish

Read this before the table.

**It does establish:** that specific numbers printed in the book follow from the
operands printed next to them, and that one chain of reasoning in the book
(ellipticity → coercivity → Lax-Milgram → unique weak solution) is a valid
implication, checked by a kernel.

**It does not establish that the book is correct.** Two limits, and the second is
the serious one:

1. Lean checked *my formalization* of each claim. Where the formalization is
   faithful (every numeric claim, the coercivity translation, the error split)
   that is close to nothing lost. Where it is not, the gap is labelled below.

2. **The book's central analytic theorems could not be stated at all.** The
   Sobolev machinery — H^s(Ω) on a bounded C¹ domain, Rellich-Kondrachov
   compactness, the Sobolev embeddings, the Darcy energy form ∫_Ω a ∇u·∇v — does
   not exist in mathlib. mathlib has Bessel potential spaces on Euclidean space
   and one Sobolev-type inequality there; that is a different object from what
   the book defines in `def:appa-hs`. So for roughly a third of the book's
   numbered statements, no Lean check was possible, and the `THEORY.lean`
   Lax-Milgram result proves the *implication* "if the form is coercive then the
   weak solution exists and is unique" — not that the book's Darcy form is
   coercive, which is the half that needs the domain integral.

A green build here is therefore not a certificate for the monograph. It is a
certificate for the arithmetic and for one abstract step.

## Verified: numeric claims

Each row is the book's claim, the citation, and what Lean proves.

| book claim | site | what Lean proves |
|---|---|---|
| Darcy speedup ≈ 1,200× | part2/07, `tab:benchmarks_hardware` | 1.45/0.0012 = 1208⅓, and within 9 of 1200 |
| Navier-Stokes speedup ≈ 2,280× | part2/07, `tab:benchmarks_hardware` | 4.80/0.0021 = 2285+5/7, within 6 of 2280 |
| Weather speedup ≈ 4,000× | part2/07, `tab:benchmarks_hardware` | 7200/1.8 = 4000 exactly |
| "9e2 s over 1e-2 s is 9e4, not 2.6e4" | part3/02, `sec:ch32-ledger` | quotient = 9e4; 9e4 ≠ 2.6e4; ratio > 3 |
| t\* = (2πA)⁻¹ ≈ 0.16, snapshots past it | appendix_c, `tab:appc_specs` | 1/8 ≤ 1/(2π) < 1/6, so ¬(0.5 < t\*) |
| ℓ_ν ≈ 0.04; "five cells at N=128", "two and a half at N=64" | appendix_c, `tab:appc_specs` | 4(0.01)/1 = 0.04; 0.04·128 = 5.12; 0.04·64 = 2.56; both roundings bounded |
| dynamic pressure ≈ 10³ Pa at 40 m/s | part3/02 (new caption/prose) | ½·1.225·40² = 980, in [10², 10⁴) |
| deleted raster's 0–2 m/s bar impossible for 10–70 m/s flow | part3/02 | 2 < 10; and ½ρU² at 10 and 70 m/s computed |
| doubling factors 2^(s−½) = 1.4 / 2.8 / 5.7 | part1/05, tail of §Rates near `fig:spectral_decay` | identities 2^(1/2)=√2, 2^(3/2)=2√2, 2^(5/2)=4√2 and enclosures 1.4–1.42, 2.8–2.84, 5.6–5.68 |
| truncation ratio: one direction + endpoint | part1/05 (tail of §Rates; citations below predate the exponent revision) | `tail_ratio_well_defined` proves the forward direction (convergence for exponent > ½ of the energy series). `s_one_diverges` proves divergence at **series exponent p = 1**, which is the book's s = ½ boundary, not s = 1 — the name is kept because the archived oleans carry it; at s = 1 (p = 2) the series converges and the book plots it. The converse (⟸) is not formalized. |
| heat multiplier decays in k, tiny by k=8 | part1/05, `fig:spectral_decay` discussion | exponent strictly antitone; exp(−0.01(2π·8)²) < exp(−20) |

(`zeta_four` remains in `Arithmetic.lean` as an exercise in its own right; the
manuscript no longer prints ζ(4) or π⁴/90 anywhere, so it cites no book statement.)

**Not restated in Lean, deliberately:** the sharp digit 1.1×10⁻¹¹ in
part1/05.
mathlib bounds π only as 3 < π ≤ 4 and has no decimal enclosure of `exp`, so the
sharp values would need a numerical-enclosure argument that adds nothing. Those
digits are produced and *asserted by `figures/make_figures.py`*, which fails the
build if they drift — a different mechanism, honestly labelled in the file header.

## Verified: theory

| book statement | Lean result | faithfulness |
|---|---|---|
| `ass:ellipticity` (part1/03, label `ass:ellipticity`) | `ellipticity_is_coercivity`, `coercivity_is_ellipticity` | **abstract**: the book's stated assumption is a pointwise bound on the coefficient $a(x)$, and its printed coercivity is in the gradient seminorm; the formalized rows assume a form-valued coercivity directly. The coefficient-to-form step (the $\int_\Omega$) is not formalized, so this row matches the honest Darcy row below, not "exact". |
| `prop:ch03-darcy` weak solution exists and is unique | `weak_solution_exists_unique` | **abstract**: proves the implication from coercivity, via mathlib's Lax-Milgram. Does NOT prove the Darcy form is coercive — that needs ∫_Ω a∇u·∇v |
| "the coercive half is precisely what fails if a → 0" | `zero_form_not_coercive` | models the degenerate limit as the zero form on a nontrivial space |
| `eq:ch01-error-split` "follows from the triangle inequality alone" | `error_split`, `error_split_four` | exact |

## Not attempted — expressible, but real work

- `thm:ch02-riesz-rep`, `thm:appa-riesz` — mathlib already has this
  (`exists_represents_continuousLinearMap`); a direct restatement is a one-liner
  and is the obvious next addition.
- `prop:ch09-lip` (Lipschitz constant of a layer stack is the product) —
  `LipschitzWith.comp`/`.mul` cover it.
- `prop:appa-alias` (aliasing on equispaced nodes) and `prop:ch06-zeroshot` —
  need the root-of-unity orthogonality sum; expressible, moderate.
- `prop:ch09-jump` (Fourier coefficients of 1_[0,1/2]) — an `intervalIntegral`
  computation.
- `thm:appa-compactness` (Arzelà-Ascoli) — mathlib has Ascoli; connecting it to
  the book's phrasing is moderate.
- `thm:chen_chen`, `thm:appa-no-universality`, `thm:appa-fno-universal` —
  Stone-Weierstrass plus explicit network constructions; large.

## Out of reach of current mathlib

`thm:ch02-rellich`, `thm:appa-rellich`, `prop:ch02-sobolev-embeddings`,
`prop:appa-embeddings`, `def:appa-hs`, `lem:appa-aubin-lions`,
`prop:appa-entropy`, `cor:ch03-precompact`, `thm:fno_convergence`,
`thm:appa-fno-rate`, `thm:deeponet_error`, `thm:appa-deeponet-error`,
`thm:appa-hilbert-schmidt`.

Blocker in every case: no Sobolev spaces on bounded domains, no compact
embedding theorems for them, no Bochner-in-time compactness. These statements
cannot be *written*, let alone proved. This is a gap in the library, not
evidence about the book.

## Not mathematical claims

The 10 `remark` environments, the applied-case statements in Part III, and the
evidentiary passages ("what has to be measured before this phrase means
anything") are argument and judgement, not theorems. Lean has nothing to say
about them, and the book should not be read as if it did.
