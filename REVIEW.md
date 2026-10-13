# Fresh Review Report — *The Infinite-Dimensional Learner*

**Date:** 2026-10-13 · **Reviewer passes:** 7 independent readers (Part I ×2, Part II, Part III ×2, front/back matter, assets audit) + build verification
**State reviewed:** `master` @ `f04a157` plus an uncommitted 4-hunk change to `Neural_Operator_Book.tex` (PDF bookmarks / `\phantomsection` list anchors — benign, and the shipped PDF was built from this state).

---

## 1. Verdict

The book's infrastructure is honest and verified: it compiles clean (302 pages, zero errors, zero undefined references or citations), every one of the nine `\includegraphics` targets exists and is tracked, Appendix B's FNO run reproduces bit-exactly on a fresh machine, the Lean project really contains 40 theorems with no `sorry`/`admit`/`axiom`, and the transcriptions of the FNO-paper Tables 3/4 and most externally sourced numbers in Part III were re-verified against the primary papers by the reviewers.

What the fresh pass found is a recurring, specific failure mode: **the provenance-discipline revision fixed captions, tables, and appendices, but the body prose still describes what used to be there.** The result is a book that contradicts itself at its own strongest points — four passages describe phantom figure panels with data that the plates deliberately do not contain; the synthesis chapter reprints three numbers its own earlier chapters explicitly audit and reject; one sentence was destroyed by a paragraph-splitting commit, leaving a literal `""` in the running text. On top of that, the central convergence theorem of Part I (`thm:fno_convergence`) is not a well-formed statement, and the flagship deployment lesson of Part II (JIT shape-baking) is empirically false on the torch version the book itself runs — a reviewer executed the listings and the archive handles unseen resolutions bit-exactly.

Counting across all passes: **~16 critical, ~35 major, ~45 minor findings.** None require rewriting the book; most are local. The critical tier is a few hours of surgical work.

---

## 2. Build & mechanical state (verified good)

- `latexmk` log: no `!` errors, 0 undefined references/citations, 0 overfull boxes reported.
- All `\ref`/`\eqref`/`\label` pairs across chapters resolve; all 27 bib keys used exist in `references.bib` (27 entries total — see §7 on thinness).
- `covers/cover.pdf` present; uncommitted bookmark patch improves outline correctness; note that `HEAD` alone does not reproduce the shipped PDF's bookmark tree — commit it.
- README's "~300 pages" and "24 numbered chapters" are accurate (302 pages, 9+7+8).

---

## 3. Critical defects — fix before anything else

**Mathematical misstatement (Part I)**

1. `part1/05…:314-326` — **`thm:fno_convergence` is not a well-formed theorem.** The display has no "there exists θ" quantifier: as written it claims *every* network of depth L, width d_v satisfies the bound, including random ones. `E_NN(L,d_v)` is never defined; prose admits it is an infimum, which cannot upper-bound an arbitrary member. Fix: `inf_{θ∈Θ(L,d_v,k_max)} sup_{u∈K} ‖G(u)−G_θ(u)‖ ≤ C₁k_max^{−α} + E_NN(L,d_v)`.
2. `part1/05…:336-341` — **the proof's exponent contradicts the theorem's.** The tail bound derives `k_max^{−(s+α)}` and then converts it to `k_max^{−α}` by "absorbing C into C₁," which is nonsense (absorbing a constant cannot move an exponent). It also contradicts the book's own upstream lemma `eq:ch02-tail` (ch02:179-186). Propagated into `notation.tex:53`, `glossary.tex:66`, `part1/08…:68`, `part1/09…:246-254`. Fix: state `−(s+α)`, or label `−α` explicitly degraded, and repair the four downstream sites.
3. `part1/05…:303-312` — **K assumed bounded, "restated from Kovachki–Lanthaler–Mishra," but KLM assume compactness**, and bounded K does not give the `H^{s+α}` bound the proof consumes. Also directly contradicts ch02:45 ("on bounded-but-not-compact sets their hypotheses simply are not met"). Fix: assume K compact.
4. `part1/04…:52-60` — **`thm:deeponet_error` is dressed as a theorem but is not one.** Type error (LHS at a single input θ; RHS operator-class quantities), and LMK's actual estimate is multiplicative-Hölder, not additive in this shape. Fix: retitle as a remark, or restate the true inequality with μ, α-Hölder continuity, and infima over branch/trunk classes.
5. `part1/02…:223-229` — **Aubin–Lions–Simon stated with `1 ≤ r ≤ ∞`; the r = 1 endpoint is false** (Simon 1987, Thm 1; the Evans copy in the bib assumes r > 1). Fix: `1 < r ≤ ∞`.
6. `part1/06…:449-463, 512-514` — **the chapter's central rate estimate `eq:ch06-rate` is asserted at theorem strength with no citation, no environment, no proof**, while Appendix A claims §6.5 "derives" it and Ch. 9 treats it as settled — a three-way circular attribution. Separately, "rigorous with matching upper and lower bounds … by Subedi and Tewari" **inverts the cited paper**, which explicitly states there is a *gap* between its upper and lower bounds for the statistical and discretization terms (repeated at `appendix_a.tex:324-326`).

**Destroyed / corrupt text**

7. `part1/06…:474` — **a literal `""` sits in the middle of §6.5** where a sentence used to be; the next paragraph starts mid-clause at lowercase. Introduced by commit `0124479` ("Break up 16 more clustered paragraphs"), which over-deleted. Restore verbatim from `499903b`.
8. `part1/05…:26` — **`\\mathbb{T}^d` corrupt**: the stray double backslash typesets the literal string "mathbbT" in the PDF (confirmed with `pdftotext`). Compiles silently.

**Phantom figures — prose describes data the plates do not contain**

9. `part2/05…:483, 152, 229` + `part2/02…:369-377` — "the Darcy curve in Figure (b)" and Ch. 11's entire empirical verdict on DeepONet rest on a **nonexistent Darcy panel**; `fig:benchmarks` is the one-panel Burgers figure, and ch14's own caption at :50 states no Darcy curve was measured. Fix: delete the passages or generate the panel with archived provenance.
10. `part2/03…:66-72, 153, 185` — the "walk the diagram" paragraph **reads shape labels off an AI-generated raster that contains none** (verified against `fig_fno_spectral_layer.png` and its on-disk prompt), calls it three boxes where it has four, and cites a caption that never mentions zero-padding.
11. `part3/03…:379-381` — "Its vorticity contours are smooth and its jets are broad" describes panel (b) of the aero plate, which is **a bare wireframe sphere** — and ch 3.2's own caption says "Neither panel shows a computed field."
12. `part3/05…:48, 367` — the cardiac chapter contains **no figure at all**, yet promises "the figure of a rotor" and asserts "Panel (b) is thus the visual form of the objection." `part3/06…:377-378` similarly refers to "box B of Figure fig:vol3_ct" while that figure's caption says no phantom reconstruction is drawn.

**Claims falsified by execution**

13. `part2/07…:107-127, 88-91` — the chapter's core deployment lesson ("tracing freezes shapes; an archive traced at B=1 cannot serve 256² or B=16") is **false on the book's own torch (2.14.1)**: a reviewer ran Listings 12.1+12.2+16.1 end-to-end and the loaded archive returned bit-exact results at 256² and B=16 — sizes are SSA values, not constants. The ONNX remedy is wrong twice over (`torch.onnx.export` also traces; `aten::fft_rfft2` is outside the ATen→ONNX mapping). Fix: restate as version-dependent shape specialization, demonstrate it, and recommend `torch.export` with `Dim(dynamic=True)` (jit is already deprecated on this install).
14. `part2/05…:191-197` — claims the t=1.0 Burgers trace "crests marginally above the initial maximum"; re-solving Cole–Hopf gives 1.0000 → 0.6207 → 0.3312, strictly decreasing, and the figure's own caption says the same. The maximum-principle diagnostic is built on a violation that does not exist.

**The synthesis chapter launders the numbers it exists to police**

15. `part3/08…:108-109, 83, 211` — matrix prints the reservoir cost ratio **"6×10⁴"** and "**L²** saturation error 1.6%" while ch 3.4 states the honest two-network ratio is "nearer 3×10⁴" and the 1.6% is a plume MAE, not a relative L² error. `:101` prints "ACC > 0.6 through day 7" — the exact inherited misreport that ch 3.1 (:383-388) quotes at length to disclaim. Under a caption promising "a fidelity cell carries a measured claim only where a published study states one."

**Dimensional error**

16. `appendix_b.tex:391-392` (+ `part2/01…:419`) — reported relative-L² percentages are called "in physical units, there being no normalizer." A relative L² error is a quotient of norms of the same field: **dimensionless**. The glossary (:633-634) and Appendix C say the opposite; three sites disagree.

---

## 4. Major findings by region

### Part I (ch 1–9)
- `part1/03…:423-426` — Biot–Savart labeled "order zero"; the velocity recovery is order −1 (only its gradient is the CZ operator). Also `:414-427` drops the mean-zero compatibility on T² it imposed earlier at `:285-286`; `:440-443` claims vortex stretching "adds a term of this same sign" — the stretching pairing has no fixed sign.
- `part1/01…:38-40` vs ch 3 — Ch. 1 says Ch. 3 "verifies" Navier–Stokes continuity/smoothing; Ch. 3 proves a closed enstrophy estimate and takes the rest as hypothesis.
- `part1/04…:21-37` — Chen–Chen misquoted in three ways (single compactum K₂; dangling {y_k}; double-sum form that is DeepONet-style, not the published single sum); **the sensor hypothesis s > d/2 is never checked against the book's own lognormal-Darcy flagship, which a.s. has no point values** (ch 14 says so explicitly); `thm:no_universality` quantifies an a-independent kernel while claiming to approximate the a-dependent class, and its monotonicity "repair" concedes the mismatch; the three-step proof sketch omits the step (representing the sensing functionals) that does the work; no Cybenko/Leshno/Stone–Weierstrass source in `references.bib` for the attributions at `:19, :103`.
- `part1/05…:26, 325 vs 456-461` — "`C₂` independent of the spatial discretization" is vacuous for a continuum-layer theorem, then reinterpreted as the grid-consistency claim that belongs to Ch. 6.
- `part1/06…` — Figure 6.2's caption is a ~272-word section with five disclaimers (also triplicated in prose and Appendix B); a 357-word paragraph carries the chapter's central epistemic payload.
- `part1/08…:135-136` — Table 8.1 marks GINO "discretization invariant" and both DeepONet and GINO "PINO: Supported" — both contradicted by ch 8's own prose (:70, :105) and ch 7 (:343-350). The Tucker/low-rank axis (`eq:ch8-tucker`) carries **no citation** though `guibas2021afno` is in the bib, and the AFNO idea is attributed to FourCastNet instead.
- `part1/09…` — `:150-151` claims no lower bounds are known "for operator classes" while citing, six lines later, the paper that proves one (for the linear model); `:107` uses `asymp` two lines before saying two-sidedness is unknown (self-refuting); `:282-294` explains the flat Burgers error with a Gibbs/discontinuity story, but the benchmark (ν = 0.1, T = 1) has an effectively analytic target with ~4 modes — the correct explanation is the opposite; `:103-148` silently swaps hypothesis-class entropy for input-ball entropy in the rate derivation (an open problem disguised as an exercise); `:433-451` offers an L² absorbing bound in the very spot it said a strictly-above-norm bound is required, plus a Navier–Stokes millennium-problem non sequitur.
- `part1/07…:105-109` — the PINO well-posedness "conditional" attached to the trivial statement instead of the one that needs it; `:337` cites Raissi 2019 for a negative claim about PINNs that the PINO paper is the source of.

### Part II (ch 10–16)
- `part2/02…:153-157` — **the flagship DeepONet listing ships knowingly broken code**: `einsum('bp,pp->bp')`/`'bp,bpp->bp'` reuse `p`; it raises at p=64, P=256 and silently returns a diagonal when P=p. The corrected strings (`bp,qp->bq`) are analyzed but never printed as a listing.
- `part2/04…` — "from-scratch" GNO claims never implemented or attributed: neighbor search / `edge_index` construction, Voronoi dual areas, SDF channels; the one GNO layer carries **no quadrature weights** though ch 10 promises ch 13 "keeps them attached."
- `part2/03…:524-541` vs `part2/01…` — the canonical library workflow calls `LpLoss(d=2, p=2)` (sums over samples/channels) after ch 14 declares an unlabeled averaging order "an unidentifiable quantity"; the from-scratch loss means instead. Also two incompatible "reference configurations" (d_v=32/m=12/L=4 vs hidden 64/n_modes 16/lr 8e-3) run through chs 12/14/15/16 and Appendix D.
- `part2/06…:156-165, 293-303` — Adam gradient-rescaling argument self-contradicts under decoupled decay; the AMP story is attributed to autocast demoting the spectral contraction — **measured: autocast leaves rfft2 and the complex einsum in fp32** (the overflow scenario needs explicit `.half()`).
- `part2/07…:283-289, 349-364` — the "B\* = 10–100" batch claim is refuted by the chapter's own numbers (its own t_field gives B\* ≈ 0.2); Table 16.1 prints four wall-clock "production benchmarks," two with no provenance at all, which are then used as measurements downstream — unlike Appendix B, which ships a run log. The part-level takeaway's "four orders of magnitude" leans on a cost–accuracy ratio its own caption says is not a timing pair, and on "complete implementations" of listings that are broken.

### Part III (ch 17–24)
- `part3/03…:18-20` — opens by attributing a "fifty-member, ten-day" cost unit to FourCastNet; the same chapter at :306 correctly says 100-member, 24-hour (Table 2). The "**≈2 h per member**" table row is contradicted by the cell it sits in (82 min total wall-clock for the 51-member run); Ch 3.1's headline 10³–10⁵ band rests on that phantom 2 h.
- `part3/02…:98-101` — boundary-layer thickness computed with **laminar Blasius Re^{−1/2} scaling for a turbulent full-scale vehicle** — wrong by ~250× (turbulent Re^{−1/5} gives δ ≈ 0.38 m, not 1.5 mm); `:208-215` prices 7.2×10⁶ cells as O(10⁷) and calls the Ahmed sampling six parameters plus velocity "seven"; the **26,000× speedup is presented for the field regression, but the source attaches it to the variant trained with drag in the loss** — which is exactly the field-vs-functional distinction ch 3.1 is built on, discarded.
- `part3/01…:11-13` — "a grid of a few thousand points" for the Part II benchmarks that run to 1.8×10⁵; `:250` places the PINO citation in a "procedural clinical" row (PINO does Darcy/Burgers/NS/airfoil — nothing cardiac); `:225-227` prints "1.2 ± 3.5 mmHg" to one decimal, unverifiable in pass, in the one chapter whose stated rule is that every number is audited in its owning chapter; phantom 1.2% drag figures persist at `:379-381`/`02:319-321` as "numbers-in-denial."
- `part3/04…:254-264` — "Commercial reservoir simulators … Eclipse, CMG, and the open-source MRST" is self-refuting (MRST is not commercial; only Eclipse generated labels), and FIM/upwinding practice is cited to Quarteroni, a general num-PDE text; `:281-290` attributes "3× the training data" and "9.2%" to an un-named convolutional baseline, conflating plume MAE with front-position error in the "40%" claim; `:446-448` prices the wavefront upstroke at ~1 mm (actual: ~0.1 mm) one paragraph after making spatial sharpness the point.
- `part3/05…:42-44` — "monodomain operator is not coercive in any useful sense" states the wrong reason (the elliptic part *is* coercive modulo constants; what breaks the estimate is the non-monotone cubic reaction and the evolutionary setting); `:187-190` "no operator surrogate reaches anywhere in this book's bibliography" misleads — cardiac-FNO emulation work exists (e.g. Heart FNO 2023) and should be cited-and-distinguished; `:162-164` cites LeVeque's *hyperbolic* FVM book for the parabolic Δt ≤ h²/2D restriction; `:11-13` has the electrical/mechanical timescale comparison backwards; openCARP and fully-ionic models named three times with zero citations.
- `part3/06…:165-240` — the two learned-CT arrangements are presented as existing practice with **zero tomography-learning citations** (references.bib contains no learned-CT entry; ch 3.8 then cites `li2021fourier` — a Darcy/Burgers/NS paper — as the source of a CT reconstruction system); FBP printed without convention constants; section title says "Continuous Inverse Radon" for a forward/FBP section; bare cross-part `Section~\ref{sec:ch06-*}` refs render as confusing "Section 6.x" inside Part III.
- `part3/08…:10, 134-146` — opens "the five application chapters each reported two numbers," contradicted by two of its own rows; the closing "hardware-bound provenance" claim silently drops the unattributed IFS "120 min" and the "15–45 min CPU solve" that chs 3.1/3.2 flag as an unattributed pairing.
- Ch 3.7 (BC enforcement) was checked line-by-line and is **mathematically clean** — the only Part III chapter with no mathematics findings.

### Front matter, back matter, glossary, bib
- `preface.tex:126-128` — "the book does not use the authorial plural": false; 22 of 23 `we`s in the sources are authorial plural. Pick: keep the promise (rewrite ~11 sentences) or drop it.
- `preface.tex:35-39` — promises Part III applications are "scored against the solvers they displace … and, in Chapter 22, filtered backprojection": ch 22 explicitly carries no score (and chs 21, 22 report neither ratio nor error).
- `glossary.tex:184-185` — "no closed bounded set in an infinite-dimensional space is compact" is **false** (the seq. e₁/n together with 0 is a counterexample); Appendix A states the correct version. `:469-472` — "`p` is always an integrability exponent and never a parameter count or latent width, as Ch. 1 states and Table 1 records" — both cited sources use p exactly as latent width and parameter count. `:637-640` claims the ε-guard issue is "handled by batch normalization" — the implementations clamp per-sample; `:440` defines HU as "linear attenuation scale" while ch 22 gives the correct affine formula; `:178-180` is a pseudo-"equivalently" (precompact = has compact closure); `:101, :515-519` contain unparseable sentences.
- `notation.tex:12-18` — "no symbol in the book has a silent double reading" is not kept by the table itself: σ (std / activation / Hölder exponent), L (layers / body length), A (input space / forward operator), m (sensors / modes), P (queries / projectors). The F, F⁻¹ row fixes no FFT normalization convention, yet ch 6's aliasing and Appendix B turn on it.
- `references.bib:145-153` — **"Li, Boying" should be Boyi Li; "Otta, Sanjeev" should be Shourya Otta** (GINO, the book's key surface-geometry source). Key/year drift at `li2021physics` (2024), `pathak2022fourcastnet` (2023), `guibas2021afno` (2022). The whole apparatus is **27 entries for ~92k words** — no Kak/Natterer/Shepp–Logan for the tomography chapter, no Brooks–Corey, no monodomain source, no Menter/Wilcox closure, no `neuraloperator` library citation, ch 12 cites exactly one key in 4,872 words.
- `appendix_b.tex:445-448, 462` — Table B.2 asserts the record has "no per-epoch curve" while the archived run log *is* an eight-point per-epoch curve the appendix itself quotes; the 0.0159 → 0.0141 val→test dip deserves one sentence. `appendix_c.tex:94-97` drops the PCANN/LNO/MGNO rows of Table 4 silently; `appendix_d.tex:54-57` propagates ch 15's wrong FFT-normalization gradient claim (reviewer derived it both ways: with norm="ortho" the gradient is *identical*).
- `Neural_Operator_Book.tex:42-43, 157-160` — stale self-audit comments with wrong page numbers (xxv vs actual xxiii; 248 vs 240), and the two comments contradict each other.

### Lean, figures, artifacts
- `lean/REPORT.md:71` — `ass:ellipticity` row labeled "**exact**" misquotes the book (formalizes a later step; the coefficient→form integral step is unformalized) and `:57` claims an **iff** where one direction plus an endpoint is proven; `s_one_diverges` is misnamed (p=1 is s=1/2 under the book's own energy). All three CI workflows sit under `lean/BookProofs/.github/` — **inert; nothing enforces the 0-sorry claim on change**.
- `figures/make_figures.py:382 vs :466` — the manifest is dumped *before* `burgers_exact()` populates it: the four Burgers attestation values are computed and discarded, so `figure_manifest.json` holds 2 of 9 plates (the same gap ch 14's caption relies on). `:17-19` — the header's justification for omitting the FNO line is now false on all three clauses (npz is tracked, torch is installed, the record is the appendix). `make_diagrams.py:259 vs 265` — `prompt_sha256` hashes the string without the trailing newline actually written to the `.prompt.txt` files, so none of the six committed hashes verify with `sha256sum`.
- `artifacts/appendix_b_run.json:16` — `npz_sha256` stores a 16-hex prefix presented as a digest (it does match — cosmetic honesty issue); its byte-identity reference file lives outside the repo, so the recorded command isn't runnable by a reader.
- The six AI plates print at ~234–243 ppi (below 300 ppi) as JPEG-origin line art — fine for screen, marginal for print.

---

## 5. The systemic pattern

Nearly every critical finding is an instance of one failure: **corrections were made at the object (caption, table, manifest) and not propagated to the prose that consumes it.**

| Object corrected | Prose left behind |
|---|---|
| "no Darcy curve exists" (ch 14 caption, honest) | two chapters discuss the Darcy panel as if plotted |
| aero plate redesigned as wireframe-only | ch 19 reads vorticity contours off it |
| CT plate disclaimer rewritten | ch 22 body still says "the boundary recovered in box B" |
| reservoir ratio audited down to 3×10⁴ | synthesis matrix reprints 6×10⁴ with an "L²" label |
| ACC day-7 claim disclaimed in ch 17 | ch 24 matrix launders it back in |
| figures regenerated "honestly" | ch 13 prose reads shapes the new plate doesn't have |

Recommend a **"consumer sweep" pass**: for every figure/table/caption that was revised in the provenance commits (`a291e21`, `612a37a`, `495edba`, `cdda546`), grep the whole tree for references to that object and re-read each consumer sentence.

Second systemic issue: **a handful of quantitative claims function as load-bearing measurements with no provenance** — Table 16.1's two unsourced rows, the "2 h per member," "B\* = 10–100," "1.2 ± 3.5 mmHg," "15–45 min CPU solve," "120 min IFS." Each is quoted downstream by another chapter. Either measure-and-archive them (the Appendix B pattern the book already demonstrates it can do) or downgrade them to explicit order-of-magnitude estimates at first mention.

---

## 6. Writing quality (quantified)

- The AI-**vocabulary** audit is clean: no delve/robust/comprehensive/landscape/seamless/groundbreaking residue anywhere.
- The residual tell is structural: **negative parallelism** ("not X but Y" / "X rather than Y") — 19 hits in Part I chs 1–3, 37 in chs 6–9, 84 ("rather than" alone) in Part II (~2.4/k words), 48 in Part III chs 17–20. Em-dashes ~6/k words. Fix: cut roughly half to bare assertions.
- **Self-grading of the book's own candor** recurs everywhere ("the honest statement/price/choice," "honesty is cheapest," "exactly the distinction this chapter has been at pains to make," "nothing drawn here establishes it"). Keep one per chapter at most.
- **Duplicated chapter-opening template** in all 7 Part II chapters ("Part I … ends with … / The reader should bring PyTorch … / The route is N sections …").
- Remaining 200+ word paragraph clusters: `part2` ch 8:24-39, ch 9:137-192, 296-331, 66-101, ch 6:497-535, 408-439, ch 7:217-252; `part1` ch 2 (lines are single-line paragraphs, hiding bloat from diff tools); `part3` ch 3.7 opening roll-call; ~35 clusters total per the paragraph-count commit's own metric.
- Figure captions litigating with hypothetical reviewers (`part3` 06:135-143, 05:446-455, 08:83) — disclaimers belong in the body that already makes the point.
- Ch 24 aphorism density ("slower than inference and quicker than hope," …) is the one cadence still reading as generated.

---

## 7. Verified sound (so rework is not wasted)

- **Appendix B is real and reproducible**: listings byte-identical (166 lines, 0 diffs) to the reference script; re-execution reproduced the archived run log exactly, including 0.0141/0.0141 and the npz exemplar 0.0092 with matching digest prefix. FFT normalization, band slicing, schedule, and no train/val/test leakage all confirmed.
- **Lean**: 40 theorems, zero `sorry`/`admit`/`axiom`/`native_decide`; `.lake` oleans show it genuinely built from current sources. (Headline true; the faithfulness *labels* in REPORT.md are the issue, not the proofs.)
- All figure files exist and resolve; no orphan figures; independently re-derived Burgers peaks 0.620736/0.331224, spectral-decay ensemble values, and `2^{s−1/2}` factors — all correct.
- FNO-paper Table 3/4 transcriptions (Burgers 0.0139–0.0160, Darcy 0.0108–0.0098, baselines' ranges) match arXiv:2010.08895 exactly; Part II parameter/flop/memory counts (589,824; 2.36→9.4 MB; 65,536 vs 65,504) all check; the from-scratch `SpectralConv2d` runs and transfers 64²→256² to 2e-7.
- Part III's external numbers are largely genuine: GINO, FourCastNet, U-FNO, and reservoir figures were traced to sources and hold (the failures are the ~6 laundried/phantom ones listed above).
- Ch 3.7 (BC enforcement) math fully correct; Ch 6's aliasing identity, Wilbraham–Gibbs constant, jump-tail Parseval estimate, Grönwall rollout bound all correct; Subedi–Tewari and KLM bib records match published entries.
- Glossary/Preface structural promises (section numbers, Definition 6.1, Theorem 5.2, eq. 5.5, prerequisites paragraph) all verify.

---

## 8. Recommended fix order

1. **Integrity tier (1 day):** the phantom-panel passages (§3 items 9–12), the laundried synthesis cells (15), the destroyed sentence and `\\mathbb{T}` bug (7, 8), the "physical units" error (16), the falsified JIT lesson (13), the maximum-principle claim (14). These are factual falsehoods *inside a book whose thesis is provenance* — highest reputational cost per word.
2. **Theorem hygiene tier (2–3 days):** quantifier/`E_NN` fix + exponent reconciliation in `thm:fno_convergence` and its four downstream sites; K compact in ch 5; retitle/replace `thm:deeponet_error`; Aubin–Lions r > 1; Subedi–Tewari attribution + `eq:ch06-rate` demotion; ch 4's Chen–Chen statement and the sensor-vs-Darcy s > d/2 check; Table 8.1's two contradicted rows.
3. **Back matter tier (1–2 days):** glossary's five wrong/contradictory entries; notation-table's universal claim + FFT convention; preface's broken promises; `references.bib` author fixes + the missing primary sources for tomography, cardiac, reservoir, closures, and the library; appendix B/C/D small honesty repairs; make the manifest dump and prompt-hash plumbing actually work; relocate the Lean CI files to the repo root.
4. **Prose tier (ongoing):** consumer sweep after every future object-level correction; negative-parallelism budget; de-duplicate chapter openings; break the ~35 remaining clusters.

Items in tier 1–3 are all local edits; none threatens the book's architecture, figure set, or the verified-good apparatus listed in §7.

---

## 9. Resolution log (2026-10-14)

**Status: tiers 1–3 fully applied; tier 4 (prose style) left open by agreement.**

- **Verification discipline.** Fixes were applied tier by tier and re-reviewed with fresh adversarial agents after each batch: eleven verification rounds total. Findings per round fell ~45 → 21 → 12 → 9 → 9 → 8 → 3 → 6 → 3 → 5 → 0 critical/major. Round 11 (final) reported "no CRITICAL or MAJOR defects remain"; its two cheap MINOR items (tomography caption clause "where no published pair of timings exists"; comma parity "multi-core, two-V100") were applied and rebuilt.
- **Round-10 specifics (synthesis matrix, Ch. 24).** The table caption was restructured to name exactly the three printed cost ratios and their true provenances (aerodynamic: published cost–accuracy ratio; weather: 1.8 s carried against an attributed 120-min member cost; carbon-storage: reported 10-min solve against 0.02 s = the published 0.01 s per-field time doubled for two networks). The unsupported "baseline on the same single V100" in Ch. 24 and in Table 16.1's caption was corrected to the study's own multi-core, two-V100 GPU OpenFOAM configuration (per Ch. 22's reported 7–19 h label generation). "Neither quotient … CPU vs accelerator" was rewritten true of both pairings. The guarantee column's contradiction (carbon cell prints eq:ch09-jump-tail while prose said "not one row carries a guarantee") was resolved in both the regulatory paragraph and the Part III takeaway: no row names a theorem proved for the architecture as deployed. "Two of its five cost ratios" → two of five cost cells print no number. Fidelity quantities now match Ch. 24's own sources (plume-restricted saturation MAE, relative pressure-buildup error).
- **Mechanical state at close:** `latexmk -pdf -bibtex` + `makeindex` + re-run: 310 pages, exit 0; 0 errors, 0 undefined references or citations, 0 overfull boxes, 0 float warnings, 0 BibTeX warnings.
- **Reproducibility re-attested:** Appendix B re-executed byte-identical (0.0141/0.0141, npz digest match); all figure manifest hashes verify against regenerated artifacts.
- **Tier 4 leftovers (documented, not applied):** negative-parallelism budget (~190 hits book-wide), ~35 long-paragraph clusters, the seven near-duplicate Part II chapter openings, self-grading candor motifs, and Ch. 24's aphorism density. These are stylistic and do not affect the integrity of any statement.
- **Working tree:** all changes remain uncommitted (never requested). Untracked additions: this report and `artifacts/FNO Worked Example (PyTorch).py` (vendored for Appendix B); `lean/.github/` workflows deleted (nested-path CI unsupported; local verification documented in `lean/REPORT.md`).
