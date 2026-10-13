/-
  Machine-checked arithmetic for "The Infinite-Dimensional Learner".

  Each statement is a numeric claim the book makes, cited to its file and line.
  Where the book writes `approx`, an explicit tolerance is stated instead of
  leaving the rounding to the reader.

  Two claims are deliberately NOT given here in sharp form: the decimal value of
  1 / (2 pi) and of exp (-0.01 (2 pi * 8)^2). mathlib carries only coarse
  enclosure of pi (3 < pi <= 4) and no decimal enclosure of `exp`, so the sharp
  digits in those two cases remain the responsibility of
  `figures/make_figures.py`, which computes them and asserts the printed string.
  What Lean checks instead is the rigorous enclosure the prose actually leans on.
-/
module

import Mathlib

open Real Finset

noncomputable section

/-! ## 1. Speedup quotients — chapters/part2/07-production-deployment...tex:358-361

  The hardware table lists a classical latency, a surrogate latency and a
  quotient. Each row is checked against its own operands. -/

theorem darcy_speedup_quotient : (1.45 : ℝ) / 0.0012 = 1208 + 1 / 3 := by norm_num
theorem darcy_speedup_rounded : |(1.45 : ℝ) / 0.0012 - 1200| ≤ 9 := by norm_num

theorem ns_speedup_quotient : (4.80 : ℝ) / 0.0021 = 2285 + 5 / 7 := by norm_num
theorem ns_speedup_rounded : |(4.80 : ℝ) / 0.0021 - 2280| ≤ 6 := by norm_num

theorem weather_speedup_exact : (120 * 60 : ℝ) / 1.8 = 4000 := by norm_num

/-! ## 2. The disputed aerodynamic quotient —
  chapters/part3/02-external-aerodynamics...tex:332-333

  The chapter asserts that 9e2 s over 1e-2 s is 9e4, and that the table's 2.6e4
  does not follow from those two numbers. Both halves are checked. -/

theorem aero_quotient_is_9e4 : (9 * 10 ^ 2 : ℝ) / (1 * 10 ^ (-2 : ℤ)) = 9 * 10 ^ 4 := by norm_num
theorem aero_2p6e4_is_not_that_quotient : (9 * 10 ^ 4 : ℝ) ≠ 2.6 * 10 ^ 4 := by norm_num
theorem aero_discrepancy_ratio : (9 * 10 ^ 4 : ℝ) / (2.6 * 10 ^ 4) > 3 := by norm_num

/-! ## 3. Inviscid gradient catastrophe — backmatter/appendix_c.tex:130

  t_* = (2 pi A)^{-1} with A = 1. What the prose leans on is that both recorded
  snapshots, t = 0.5 and t = 1, lie past t_*. The enclosure below gives
  t_* in [1/8, 1/6), which is more than enough and is all that pi > 3 supports. -/

theorem two_pi_bounds : (6 : ℝ) < 2 * Real.pi ∧ 2 * Real.pi ≤ 8 := by
  refine ⟨by nlinarith [Real.pi_gt_three], by nlinarith [Real.pi_le_four]⟩

theorem catastrophe_is_early : 1 / (2 * Real.pi) < 0.5 := by
  have h := two_pi_bounds.1
  rw [show (0.5 : ℝ) = 1 / 2 by norm_num]
  refine (one_div_lt_one_div (by positivity) (by positivity)).mpr ?_
  linarith

theorem catastrophe_upper : 1 / (8 : ℝ) ≤ 1 / (2 * Real.pi) := by
  have h := two_pi_bounds.2
  refine (one_div_le_one_div (by positivity) (by positivity)).mpr ?_
  linarith

theorem snapshots_lie_past_t_star : ¬ ((0.5 : ℝ) < 1 / (2 * Real.pi)) := by
  intro h; exact (lt_irrefl (0.5 : ℝ) (lt_trans h catastrophe_is_early)).elim

/-! ## 4. Viscous shock width — backmatter/appendix_c.tex:127-129

  l_nu = 4 nu / (u^- - u^+) approx 0.04 for nu = 0.01 across an order-unity
  jump, "about five cells at N = 128 and two and a half at N = 64". -/

theorem shock_width_unit_jump : 4 * (0.01 : ℝ) / 1 = 0.04 := by norm_num
theorem shock_cells_N128 : (0.04 : ℝ) * 128 = 5.12 := by norm_num
theorem shock_cells_N64 : (0.04 : ℝ) * 64 = 2.56 := by norm_num
theorem five_cells_claim : |(0.04 : ℝ) * 128 - 5| < 1 := by norm_num
theorem two_and_a_half_claim : |(0.04 : ℝ) * 64 - 2.5| < 0.1 := by norm_num

/-! ## 5. Dynamic pressure — the scale cited in chapters/part3/02...tex

  A span of order 1e3 Pa is what a freestream near 40 m/s generates through
  1/2 rho U^2 in air at standard density rho = 1.225. -/

theorem dynamic_pressure_40 : (1 / 2 : ℝ) * 1.225 * 40 ^ 2 = 980 := by norm_num
theorem dynamic_pressure_order : 100 ≤ (1 / 2 : ℝ) * 1.225 * 40 ^ 2 ∧
    (1 / 2 : ℝ) * 1.225 * 40 ^ 2 < 10000 := by norm_num
theorem dynamic_pressure_10 : (1 / 2 : ℝ) * 1.225 * 10 ^ 2 = 61.25 := by norm_num
theorem dynamic_pressure_70 : (1 / 2 : ℝ) * 1.225 * 70 ^ 2 = 3001.25 := by norm_num

-- The deleted raster printed a velocity colorbar saturating at 2 m/s while the
-- chapter's own operating range starts at 10 m/s. That is arithmetic, not taste.
theorem velocity_bar_below_operating_range : (2 : ℝ) < 10 := by norm_num

/-! ## 6. Asymptotic doubling factors — chapters/part1/05...tex:410-413

  Doubling k_max divides the truncation error by 2^(s - 1/2). The book quotes
  1.4 / 2.8 / 5.7 asymptotically and 1.46 / 2.80 / 5.55 as computed. The
  asymptotic constants are enclosed here; the computed ones come from
  `figures/make_figures.py`. -/

theorem sqrt2_bounds : 1.4 < Real.sqrt 2 ∧ Real.sqrt 2 < 1.42 := by
  have s0 : 0 ≤ Real.sqrt 2 := Real.sqrt_nonneg 2
  have s1 : (Real.sqrt 2) ^ 2 = 2 := Real.sq_sqrt (by norm_num)
  constructor <;> nlinarith [s0, s1]

theorem doubling_s1 : (2 : ℝ) ^ (1 / 2 : ℝ) = Real.sqrt 2 := Eq.symm (Real.sqrt_eq_rpow 2)

theorem doubling_s2 : (2 : ℝ) ^ (3 / 2 : ℝ) = 2 * Real.sqrt 2 := by
  rw [show (3 / 2 : ℝ) = (1 : ℝ) + (1 / 2 : ℝ) by norm_num,
      Real.rpow_add (by norm_num : (0 : ℝ) < 2), Real.rpow_one, doubling_s1]

theorem doubling_s3 : (2 : ℝ) ^ (5 / 2 : ℝ) = 4 * Real.sqrt 2 := by
  rw [show (5 / 2 : ℝ) = (3 / 2 : ℝ) + (1 : ℝ) by norm_num,
      Real.rpow_add (by norm_num : (0 : ℝ) < 2), doubling_s2, Real.rpow_one]
  ring

theorem doubling_s1_between : 1.4 < (2 : ℝ) ^ (1 / 2 : ℝ) ∧ (2 : ℝ) ^ (1 / 2 : ℝ) < 1.42 := by
  rw [doubling_s1]; exact sqrt2_bounds

theorem doubling_s2_between : 2.8 < (2 : ℝ) ^ (3 / 2 : ℝ) ∧ (2 : ℝ) ^ (3 / 2 : ℝ) < 2.84 := by
  rw [doubling_s2]; have ⟨h1, h2⟩ := sqrt2_bounds; constructor <;> nlinarith

theorem doubling_s3_between : 5.6 < (2 : ℝ) ^ (5 / 2 : ℝ) ∧ (2 : ℝ) ^ (5 / 2 : ℝ) < 5.68 := by
  rw [doubling_s3]; have ⟨h1, h2⟩ := sqrt2_bounds; constructor <;> nlinarith

/-! ## 7. Heat-semigroup mode decay — chapters/part1/05...tex:430

  The multiplier exp (-alpha (2 pi k)^2 T) is strictly decreasing in k, and by
  k = 8 it is below exp (-20). The book's sharper 1.1e-11 is computed by the
  figure script; see the file header for why it is not restated here. -/

-- The exponent of the heat multiplier is strictly decreasing in the mode number.
-- (Stated for the exponent itself: the 0.01 prefactor is a positive constant and
-- composes trivially, so this is the content the chapter's argument uses.)
theorem multiplier_exponent_antitone (k₁ k₂ : ℕ) (h : k₁ < k₂) :
    -((2 * Real.pi * (k₂ : ℝ)) ^ 2) < -((2 * Real.pi * (k₁ : ℝ)) ^ 2) := by
  have hk : (k₁ : ℝ) < (k₂ : ℝ) := by exact_mod_cast h
  have hlt : 2 * Real.pi * (k₁ : ℝ) < 2 * Real.pi * (k₂ : ℝ) := by nlinarith [Real.pi_pos]
  have hw : 0 ≤ 2 * Real.pi * (k₁ : ℝ) := by positivity
  nlinarith [sq_nonneg (2 * Real.pi * (k₂ : ℝ) - 2 * Real.pi * (k₁ : ℝ)),
    mul_self_nonneg (2 * Real.pi * (k₁ : ℝ)), hlt, hw]

theorem heat_multiplier_k8_small :
    Real.exp (-0.01 * (2 * Real.pi * 8) ^ 2) < Real.exp (-20 : ℝ) := by
  refine Real.exp_lt_exp.mpr ?_
  have h : (48 : ℝ) < 2 * Real.pi * 8 := by nlinarith [Real.pi_gt_three]
  have hsq : (48 : ℝ) ^ 2 < (2 * Real.pi * 8) ^ 2 := by nlinarith
  nlinarith

/-! ## 8. Spectral-tail structure — chapters/part1/05...tex:415-417

  The truncation ratio converges exactly when s > 1/2, diverges at s = 1, and
  the s = 2 normalizer is pi^4 / 90. -/

theorem tail_ratio_well_defined (s : ℝ) (hs : (1 : ℝ) / 2 < s) :
    Summable (fun k : ℕ => (k : ℝ) ^ (-(2 * s))) := by
  have h : 1 < 2 * s := by linarith
  convert (summable_nat_rpow_inv (p := 2 * s)).mpr h using 1
  funext n; rw [Real.rpow_neg (Nat.cast_nonneg n)]

theorem s_one_diverges : ¬ Summable (fun n : ℕ => ((n : ℝ) ^ (1 : ℝ))⁻¹) :=
  (summable_nat_rpow_inv (p := 1)).not.mpr (by norm_num)

theorem zeta_four : (∑' n : ℕ, 1 / (n : ℝ) ^ 4) = Real.pi ^ 4 / 90 :=
  hasSum_zeta_four.tsum_eq
