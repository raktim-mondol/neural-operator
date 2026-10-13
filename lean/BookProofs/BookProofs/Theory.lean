/-
  Machine-checked theory for "The Infinite-Dimensional Learner".

  SCOPE, STATED HONESTLY. The book's functional analysis lives on Sobolev spaces
  over bounded domains: H^s(Omega), the Rellich-Kondrachov compact injection, the
  Darcy energy form int_Omega a grad u . grad v. mathlib has no Sobolev spaces on
  domains -- only Bessel potential spaces on Euclidean space
  (Analysis/FunctionalSpaces/BesselPotentialSpace.lean) and one Sobolev-type
  inequality there. The book's theorems AS LITERALLY STATED therefore cannot be
  written in Lean today, and a weakened look-alike would be worse than nothing.

  What is checked here is the layer that does not depend on the domain:
    1. that the book's ellipticity hypothesis and mathlib's `IsCoercive` are
       literally the same condition        (`ass:ellipticity`, part1/03:103)
    2. the Lax-Milgram conclusion drawn from it: existence and uniqueness of the
       weak solution                       (`prop:ch03-darcy` via `thm:appa-lax-milgram`)
    3. that the hypothesis is necessary, not decorative (the degenerate limit)
    4. the error split                     (`eq:ch01-error-split`)

  See REPORT.md for the statements deliberately NOT attempted and why.
-/
module

import Mathlib

open Real InnerProductSpace

noncomputable section

variable {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [CompleteSpace V]

/-! ## 1. The book's ellipticity is mathlib's coercivity, verbatim

  `ass:ellipticity` supplies `a_min > 0` with `a_min * ‖u‖ * ‖u‖ ≤ B u u`.
  mathlib's `IsCoercive` asks for exactly that. The two lemmas are the
  translation in both directions, so nothing is smuggled in when the book
  invokes Lax-Milgram. -/

theorem ellipticity_is_coercivity (B : V →L[ℝ] V →L[ℝ] ℝ) (a_min : ℝ) (hpos : 0 < a_min)
    (h : ∀ u, a_min * ‖u‖ * ‖u‖ ≤ B u u) : IsCoercive B :=
  ⟨a_min, hpos, h⟩

theorem coercivity_is_ellipticity (B : V →L[ℝ] V →L[ℝ] ℝ) (hB : IsCoercive B) :
    ∃ C, 0 < C ∧ ∀ u, C * ‖u‖ * ‖u‖ ≤ B u u := hB

/-! ## 2. Lax-Milgram: the weak solution exists and is unique

  The book's `prop:ch03-darcy` conclusion in the abstract setting the proof
  consumes: for every datum `z`, representing the load functional
  `v ↦ ⟪z, v⟫` through Riesz, there is exactly one `u` with `B u w = ⟪z, w⟫` for
  every test function `w`. The abstraction is the domain and the gradient; the
  logical step is not. -/

theorem weak_solution_exists_unique (B : V →L[ℝ] V →L[ℝ] ℝ) (hB : IsCoercive B) (z : V) :
    ∃! u : V, ∀ w : V, B u w = ⟪z, w⟫_ℝ := by
  let A : V ≃L[ℝ] V := hB.continuousLinearEquivOfBilin
  have hA : ∀ v w : V, ⟪A v, w⟫_ℝ = B v w :=
    fun v w => IsCoercive.continuousLinearEquivOfBilin_apply hB v w
  refine ⟨A.symm z, ?_, ?_⟩
  · intro w
    rw [← hA, A.apply_symm_apply]
  · intro u hu
    have hz : z = A u := hB.unique_continuousLinearEquivOfBilin (fun w => (hu w).symm)
    have : A.symm z = u := by rw [hz]; exact A.symm_apply_apply u
    exact this.symm

/-! ## 3. The hypothesis is necessary

  The book says of Assumption 3.1 that the coercive half is precisely what fails
  when the coefficient may approach zero. That is a claim about necessity, and the
  degenerate limit is checkable: on a nontrivial space the zero form, which is
  what a coefficient vanishing in one direction degenerates to, is coercive for
  no positive constant. -/

theorem zero_form_not_coercive [Nontrivial V] : ¬ IsCoercive (0 : V →L[ℝ] V →L[ℝ] ℝ) := by
  intro h
  obtain ⟨C, hC, hle⟩ := h
  obtain ⟨x, y, hne⟩ := exists_pair_ne V
  have hv : 0 < ‖x - y‖ := norm_pos_iff.mpr (sub_ne_zero.mpr hne)
  have h1 : C * ‖x - y‖ * ‖x - y‖ ≤ (0 : ℝ) := by simpa using hle (x - y)
  nlinarith [mul_pos hC hv, mul_pos hv hv]

/-! ## 4. The error split

  `eq:ch01-error-split` is the triangle inequality; the book itself says it
  "follows from the triangle inequality alone", and that is checkable. The
  four-point version is the form used when a discretization term is inserted
  between approximation and estimation. -/

theorem error_split {E : Type*} [SeminormedAddCommGroup E] (u v w : E) :
    ‖u - w‖ ≤ ‖u - v‖ + ‖v - w‖ := by
  have h : u - w = (u - v) + (v - w) := by abel
  rw [h]
  exact norm_add_le _ _

theorem error_split_four {E : Type*} [SeminormedAddCommGroup E] (u v w x : E) :
    ‖u - x‖ ≤ ‖u - v‖ + ‖v - w‖ + ‖w - x‖ := by
  have h1 := error_split u w x
  have h2 := error_split u v w
  nlinarith
