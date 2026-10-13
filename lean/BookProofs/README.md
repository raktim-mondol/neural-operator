# BookProofs

Lean 4 + mathlib verification of selected statements from the monograph.
Build with `lake build` from this directory (requires elan; see
`lean-toolchain`). What is formalized, and what each result does and does
not claim about the book, is documented in `../REPORT.md`. The 0-sorry
invariant is enforced locally: `lake build`, plus
`grep -rn "sorry\|admit\|axiom\|native_decide" .` returning nothing.
