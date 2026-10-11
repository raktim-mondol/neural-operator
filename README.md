# The Infinite-Dimensional Learner

**Neural Operators: From Function Spaces to Scientific Machine Learning**

A graduate-level academic monograph, in three parts:

- **Part I — Mathematical Foundations:** functional analysis, Sobolev regularity,
  operator approximation and universality, the Fourier Neural Operator's spectral
  convergence theory, discretization invariance, and physics-informed operators.
- **Part II — Architectures and Implementation:** DeepONet, FNO, GNO/GINO built
  from scratch in PyTorch, canonical PDE benchmarks, training regimes, and
  production deployment.
- **Part III — Applications:** external aerodynamics, global weather, subsurface
  CO₂ storage, cardiac electrophysiology, and tomographic reconstruction, with a
  synthesis matrix and deployment roadblocks.

Back matter: Appendices A–E (functional-analysis reference, a complete runnable
FNO, PDE benchmark specs, training recipes, an index of architectural variants),
a glossary, a fully published bibliography, and a subject index.

## Build

Requires a standard LaTeX distribution (TeX Live) with `latexmk`, `bibtex`, and
`makeindex`.

```bash
latexmk -pdf Neural_Operator_Book.tex
makeindex Neural_Operator_Book.idx
latexmk -pdf Neural_Operator_Book.tex
```

The output is `Neural_Operator_Book.pdf` (~300 pages). Build artifacts are
git-ignored.

## Layout

```
Neural_Operator_Book.tex   main file (preamble, parts, back matter)
frontmatter/               preface, notation master table
chapters/part1|2|3/        the 24 numbered chapters
backmatter/                appendices A-E, glossary
figures/                   images + make_figures.py (the two computed data plots)
references.bib             bibliography (all entries resolved to published records)
```

## About this book

This entire book was written by AI, and prompted, edited
and reviewed by Dr Raktim Mondol, who is responsible for its contents. Every
bibliographic entry was resolved against a published journal or conference
record.
