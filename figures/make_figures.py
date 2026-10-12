#!/usr/bin/env python3
"""Generate the two quantitative figures used in Chapters 5 and 6.

Both figures are COMPUTED, not drawn. Every curve is produced by the code below
from an exactly solvable model problem, so the book can state the construction
in the caption instead of asserting a number.

PROVENANCE POLICY FOR THIS FILE (what may reach a PDF):

  1. A curve is plotted only if an array computed here produces it.
  2. A NUMBER printed on a figure is formatted out of such an array by the
     helper ``sig()``; no numeric literal is ever typed into a label. Every one
     of them is additionally re-checked by ``check_caption_numbers()`` at the
     end of the run and dumped to ``figure_manifest.json`` next to the PDFs, so
     a caption can be audited without re-reading the plot.
  3. Nothing from a training run is drawn. Appendix B's worked example is
     therefore absent from both panels that used to carry it: its archive
     (fno_results.npz) is not in this repository, torch is not installed here,
     and the only text in the tree that states its outcome is a chat export
     headed "Actual observed numbers from the run". A number that cannot be
     recomputed is not a number this figure may print, and from now on the
     figures say so instead of drawing a horizontal line for it.

Model problem (identical to Appendix B's worked example):
1-D periodic heat equation

    du/dt = alpha d2u/dx2,  x in [0,1) periodic, alpha = 0.01, T = 1.0

whose solution operator is the Fourier multiplier

    u(.,T) = F^-1[ F[u0](k) * exp(-alpha (2 pi k)^2 T) ]

so the exact solution is available to machine precision on any grid that
resolves the input. Input family:

    u0(x) = sum_{k=1}^{K} c_k k^-1.5 cos(2 pi k x + phi_k),
    c_k ~ N(0,1), phi_k ~ U(0,2pi), K = 8

Outputs fig_spectral_decay.pdf and fig_super_resolution.pdf next to this file.
Run:  python3 make_figures.py            (add --png for raster copies to eyeball)
"""
from __future__ import annotations

import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ALPHA = 0.01
T_END = 1.0
K_MODES = 8
SEED = 20261010
HERE = os.path.dirname(os.path.abspath(__file__))

# Everything the captions print is collected here from COMPUTED arrays and
# written to figure_manifest.json, so caption and figure cannot silently drift.
MANIFEST: dict = {}

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif", "Times New Roman"],
    "mathtext.fontset": "dejavuserif",
    "axes.grid": True,
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})
PRIMARY = "#123060"
SECONDARY = "#7d202d"
ACCENT = "#2a6f97"


def sig(v: float, n: int = 3) -> str:
    """Mathtext for a COMPUTED value with n significant digits.

    8.26e-3 with n=2 -> '$8.3 \\times 10^{-3}$'; 1.70 with n=3 -> '$1.70$'.
    Every number printed inside a figure goes through here, so what the reader
    sees is an array element and never a literal typed into the source.
    """
    if v == 0:
        return "$0$"
    e = int(np.floor(np.log10(abs(v))))
    mant = abs(v) / 10.0 ** e
    if e < -2 or e >= 3:
        return rf"${mant:.{n - 1}f} \times 10^{{{e}}}$"
    return rf"${v:.{max(0, n - 1 - e)}f}$"


# ---------------------------------------------------------------- core solver
def sample_input(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Band-limited smooth input from the worked example's family."""
    u0 = np.zeros_like(x)
    for k in range(1, K_MODES + 1):
        c = rng.normal()
        phi = rng.uniform(0, 2 * np.pi)
        u0 += (c / k ** 1.5) * np.cos(2 * np.pi * k * x + phi)
    return u0


def heat_exact(u0: np.ndarray, alpha=ALPHA, t=T_END) -> np.ndarray:
    """Apply the exact heat semigroup as a Fourier multiplier."""
    n = u0.size
    k = np.fft.rfftfreq(n, d=1.0 / n)          # integer wavenumbers
    uh = np.fft.rfft(u0)
    return np.fft.irfft(uh * np.exp(-alpha * (2 * np.pi * k) ** 2 * t), n=n)


def rel_l2(pred: np.ndarray, exact: np.ndarray) -> float:
    return float(np.linalg.norm(pred - exact) / np.linalg.norm(exact))


# ------------------------------------------------------- figure 1: spectral
def truncation_curve(s: int, kmax_range: np.ndarray, k_support: int = 513) -> np.ndarray:
    """Exact relative L2 truncation error of the band projection |k| <= kmax.

    For the Sobolev model u_hat(k) = |k|^-s xi_k with iid standard normal xi_k,
    E|u_hat(k)|^2 = k^-2s, so the expected squared tail share is
    sum_{k>kmax} k^-2s / sum_{k>=1} k^-2s, computed exactly (deterministic).
    """
    kk = np.arange(1, k_support)
    pw = kk.astype(float) ** (-2.0 * s)
    total = pw.sum()
    return np.array([np.sqrt(pw[km:].sum() / total) for km in kmax_range])


def spectral_decay():
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.3))

    # (a) energy spectrum of Sobolev-s fields: a_hat(k) = |k|^-s * xi_k
    rng = np.random.default_rng(SEED)
    kmax = 256
    k = np.arange(1, kmax + 1)
    axes[0].axvline(16, color="0.55", lw=1.0, ls=":", zorder=1)
    axes[0].text(17, 3e-1, r"retained $|k|\leq k_{\max}$", fontsize=8, color="0.35")
    for s, col in [(1, ACCENT), (2, PRIMARY), (3, SECONDARY)]:
        # E[|u_hat(k)|^2] = k^{-2s}; plot the empirical average of 40 draws
        energy = np.mean([np.abs(rng.normal(size=kmax) / k ** s) ** 2
                          for _ in range(40)], axis=0)
        axes[0].loglog(k, energy, lw=1.6, color=col,
                       label=rf"$s={s}$  ($\sim k^{{{-2 * s}}}$)")
    axes[0].set_xlabel(r"wavenumber $|k|$")
    axes[0].set_ylabel(r"mean spectral energy $\mathbb{E}|\hat{u}(k)|^2$")
    axes[0].set_title("(a) Spectral energy decay of Sobolev fields", fontsize=10)
    axes[0].legend(fontsize=8, frameon=False)
    axes[0].set_ylim(1e-9, 3)

    # (b) exact truncation error of retaining |k| <= kmax, and nothing else
    kmax_range = np.arange(2, 65)
    curves = {}
    for s, col in [(1, ACCENT), (2, PRIMARY), (3, SECONDARY)]:
        errs = truncation_curve(s, kmax_range)
        curves[s] = errs
        axes[1].loglog(kmax_range, errs, lw=1.8, color=col,
                       label=rf"$s={s}$, slope $-(s-1/2)$")
    axes[1].axvline(16, color="0.55", lw=1.0, ls=":", zorder=1)

    # --- every printed quantity below is read off `curves`, not typed in ------
    v16 = {s: float(curves[s][list(kmax_range).index(16)]) for s in (1, 2, 3)}
    axes[1].annotate(
        f"$s=2$ at $k_{{\\max}}=16$: {sig(v16[2], 2)}",
        xy=(16, v16[2]), xytext=(20, 1.8e-2), fontsize=8, color=PRIMARY,
        arrowprops=dict(arrowstyle="-", color=PRIMARY, lw=0.9,
                        connectionstyle="arc3,rad=-0.15"),
    )
    axes[1].set_xlabel(r"retained modes $k_{\max}$")
    axes[1].set_ylabel(r"relative $L^2$ truncation error")
    axes[1].set_title("(b) Truncation error vs cutoff, computed exactly", fontsize=10)
    axes[1].legend(fontsize=8, frameon=False, loc="lower left")
    axes[1].set_ylim(1e-6, 2)

    fig.tight_layout()
    out = os.path.join(HERE, "fig_spectral_decay.pdf")
    fig.savefig(out, bbox_inches="tight")
    if "--png" in sys.argv:
        fig.savefig(out.replace(".pdf", ".png"), dpi=200, bbox_inches="tight")
    plt.close(fig)

    # error-reduction factor when the band is doubled, kmax = 32 -> 64
    factors = {f"s={s}": float(curves[s][list(kmax_range).index(32)]
                              / curves[s][list(kmax_range).index(64)]) for s in (1, 2, 3)}
    MANIFEST["fig_spectral_decay"] = {
        "panel_b_exact_truncation_error": {
            "s=1 at k_max=16": v16[1], "s=2 at k_max=16": v16[2],
            "s=3 at k_max=16": v16[3],
            "s=1 at k_max=64": float(curves[1][-1]),
            "s=2 at k_max=64": float(curves[2][-1]),
        },
        "panel_b_ratio_s1_over_s2_at_k_max_16": v16[1] / v16[2],
        "panel_b_doubling_factor_k32_to_k64": factors,
        "asymptotic_doubling_factor_2_pow_(s-1/2)": {
            "s=1": 2.0 ** 0.5, "s=2": 2.0 ** 1.5, "s=3": 2.0 ** 2.5},
        "panel_b_theoretical_loglog_slope": {"s=1": -0.5, "s=2": -1.5, "s=3": -2.5},
        "nothing_from_any_training_run_is_plotted": True,
        "removed_vs_previous_revision": [
            "axhline(1.4e-2) labelled 'neural approximation floor'",
        ],
    }


# --------------------------------------------- figure 2: resolution invariance
def input_fun(x, coeffs):
    """Analytic band-limited input, evaluable at any x."""
    out = np.zeros_like(x)
    for k, (c, phi) in coeffs.items():
        out += (c / k ** 1.5) * np.cos(2 * np.pi * k * x + phi)
    return out


def heat_fun(x, coeffs):
    """Analytic exact solution at T, evaluable at any x."""
    out = np.zeros_like(x)
    for k, (c, phi) in coeffs.items():
        damp = np.exp(-ALPHA * (2 * np.pi * k) ** 2 * T_END)
        out += (c / k ** 1.5) * damp * np.cos(2 * np.pi * k * x + phi)
    return out


def make_coeffs(trial):
    rng = np.random.default_rng(SEED + 500 + trial)
    return {k: (rng.normal(), rng.uniform(0, 2 * np.pi)) for k in range(1, K_MODES + 1)}


def circular_smooth(u, s_phys):
    """Periodic Gaussian smoothing with PHYSICAL width s_phys on [0,1).

    A Gaussian of physical std s has transfer exp(-2 pi^2 s^2 k^2) at integer
    wavenumber k. The heat semigroup exp(-alpha (2 pi k)^2 T) is exactly this
    with s = sqrt(2 alpha T), so smoothing with s_phys = sqrt(2 alpha T) IS the
    solution operator -- that identity is what makes this figure honest.
    """
    n = u.size
    k = np.fft.rfftfreq(n, d=1.0 / n)
    return np.fft.irfft(np.fft.rfft(u) * np.exp(-2 * np.pi ** 2 * s_phys ** 2 * k ** 2), n=n)


def super_resolution():
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.3))

    # (a) the SAME continuous function sampled on two grids
    coeffs = make_coeffs(0)
    for n, marker, col, lab in [(32, "o", PRIMARY, "$N=32$ (training grid)"),
                               (128, ".", SECONDARY, "$N=128$ (evaluation grid)")]:
        x = np.linspace(0, 1, n, endpoint=False)
        axes[0].plot(x, input_fun(x, coeffs), marker=marker,
                     ls="-" if n == 128 else "--", lw=1.0 if n == 128 else 1.4,
                     ms=4 if n == 32 else 2.5, color=col, label=lab, alpha=0.9)
    axes[0].set_xlabel(r"$x$")
    axes[0].set_ylabel(r"$u_0(x)$")
    axes[0].set_title("(a) One continuous field, two discretizations", fontsize=10)
    axes[0].legend(fontsize=8, frameon=False)

    # (b) error vs evaluation resolution, measured against the ANALYTIC solution
    n_train = 32
    sigma_phys = np.sqrt(2 * ALPHA * T_END)          # heat kernel's physical width
    sigma_px_train = sigma_phys * n_train            # same width, in training-grid units
    Ns = [32, 48, 64, 96, 128, 192, 256, 384, 512]
    trials = 80
    acc = {k: np.zeros(len(Ns)) for k in
           ["mesh_fixed_px", "mesh_fixed_phys", "linear_resample"]}

    for tr in range(trials):
        cf = make_coeffs(tr)
        for i, N in enumerate(Ns):
            x = np.linspace(0, 1, N, endpoint=False)
            target = heat_fun(x, cf)
            denom = np.linalg.norm(target)
            u0 = input_fun(x, cf)
            # (i) MESH-BOUND: kernel width frozen in GRID units, as a CNN trained
            #      at N=32 effectively does. Its physical footprint is
            #      sigma_px_train / N, so it shrinks as N grows and the operator
            #      silently stops smoothing.
            acc["mesh_fixed_px"][i] += rel_l2(
                circular_smooth(u0, sigma_px_train / N), target)
            # (ii) RESOLUTION-AWARE: width specified in physical units, i.e. a
            #      discretization-invariant operator. Identical at every N.
            acc["mesh_fixed_phys"][i] += rel_l2(
                circular_smooth(u0, sigma_phys), target)
            # (iv) solve on the training grid, then linearly resample the answer up
            xt = np.linspace(0, 1, n_train, endpoint=False)
            pred_t = heat_fun(xt, cf)
            acc["linear_resample"][i] += rel_l2(
                np.interp(x, xt, pred_t, period=1.0), target)

    curves = {k: v / trials for k, v in acc.items()}
    axes[1].semilogy(Ns, curves["mesh_fixed_px"], "o-", color=SECONDARY, lw=1.9, ms=5,
                     label="mesh-bound surrogate: kernel frozen in grid units")
    axes[1].semilogy(Ns, curves["linear_resample"], "^--", color=ACCENT, lw=1.5, ms=5,
                     label="training-grid solution, linearly resampled")
    axes[1].semilogy(Ns, curves["mesh_fixed_phys"], "s:", color="0.3", lw=1.5, ms=4,
                     label="resolution-aware operator: width in physical units")

    # --- the only numbers printed in this panel: endpoints of the arrays -----
    ends = {name: float(curves[name][-1]) for name in curves}
    callouts = {
        "mesh_fixed_px": (0.15, "mesh-bound", SECONDARY),
        "linear_resample": (1.1e-3, "resampled", ACCENT),
        "mesh_fixed_phys": (4e-14, "resolution-aware", "0.3"),
    }
    for name, (ytext, short, col) in callouts.items():
        axes[1].annotate(
            f"{short}, $N=512$: {sig(ends[name], 3)}",
            xy=(512, ends[name]), xytext=(300, ytext), fontsize=7.6, color=col,
            ha="left", va="center",
            arrowprops=dict(arrowstyle="-", color=col, lw=0.8,
                            connectionstyle="arc3,rad=0.15"),
        )
    axes[1].set_xlabel("evaluation grid points $N$")
    axes[1].set_ylabel("relative $L^2$ error vs. analytic solution")
    axes[1].set_title("(b) Error vs resolution, calibrated at $N=32$", fontsize=10)
    axes[1].legend(fontsize=7.2, frameon=False, loc="center left")
    axes[1].set_xticks([32, 64, 128, 256, 512])
    axes[1].tick_params(axis="x", labelrotation=30)
    axes[1].set_ylim(1e-17, 4)

    fig.tight_layout()
    out = os.path.join(HERE, "fig_super_resolution.pdf")
    fig.savefig(out, bbox_inches="tight")
    if "--png" in sys.argv:
        fig.savefig(out.replace(".pdf", ".png"), dpi=200, bbox_inches="tight")
    plt.close(fig)

    MANIFEST["fig_super_resolution"] = {
        "panel_b_endpoints_at_N512": ends,
        "panel_b_resolution_aware_max_over_all_grids":
            float(curves["mesh_fixed_phys"].max()),
        "panel_b_resolution_aware_span": [float(curves["mesh_fixed_phys"].min()),
                                         float(curves["mesh_fixed_phys"].max())],
        "panel_b_linear_resample_plateau_max": float(curves["linear_resample"].max()),
        "panel_b_mesh_bound_monotone_increasing":
            bool(np.all(np.diff(curves["mesh_fixed_px"][1:]) > 0)),
        "nothing_from_any_training_run_is_plotted": True,
        "removed_vs_previous_revision": [
            "axhline(0.0141) + two markers labelled 'FNO, measured (App. B)'",
        ],
    }
    for k, v in curves.items():
        print(f"{k:18s}", " ".join(f"{x:.2e}" for x in v))


def check_caption_numbers():
    """Fail loudly if a quantity the captions quote stops being what we compute.

    Checked as the STRINGS the figures print, so this is a check on the
    artefact, not on a private notion of the value.
    """
    man = MANIFEST["fig_spectral_decay"]
    f = man["panel_b_doubling_factor_k32_to_k64"]
    errs = man["panel_b_exact_truncation_error"]
    assert abs(f["s=1"] - 1.46) < 5e-3, f
    assert abs(f["s=2"] - 2.80) < 5e-3, f
    assert abs(f["s=3"] - 5.55) < 5e-3, f
    assert sig(errs["s=2 at k_max=16"], 2) == r"$8.3 \times 10^{-3}$", sig(errs["s=2 at k_max=16"], 2)
    assert abs(errs["s=1 at k_max=16"] - 0.189) < 1e-3, errs
    # the prose of Chapter 5 writes this as $9.1\times10^{-2}$
    assert sig(errs["s=1 at k_max=64"], 2) == r"$0.091$", sig(errs["s=1 at k_max=64"], 2)
    assert round(MANIFEST["fig_spectral_decay"]
                 ["panel_b_ratio_s1_over_s2_at_k_max_16"]) == 23
    sup = MANIFEST["fig_super_resolution"]
    ends = sup["panel_b_endpoints_at_N512"]
    assert sig(sup["panel_b_linear_resample_plateau_max"], 3) == r"$5.24 \times 10^{-3}$"
    assert sig(ends["mesh_fixed_phys"], 3) == r"$5.50 \times 10^{-16}$", sig(ends["mesh_fixed_phys"], 3)
    assert sig(ends["mesh_fixed_px"], 3) == r"$1.70$"
    assert sig(ends["linear_resample"], 3) == r"$5.24 \times 10^{-3}$"
    assert sup["panel_b_resolution_aware_max_over_all_grids"] < 1e-15
    span = sup["panel_b_resolution_aware_span"]
    assert sig(span[0], 3) == r"$5.48 \times 10^{-16}$", sig(span[0], 3)
    assert sig(span[1], 3) == r"$7.63 \times 10^{-16}$", sig(span[1], 3)
    assert sup["panel_b_mesh_bound_monotone_increasing"]


if __name__ == "__main__":
    spectral_decay()
    super_resolution()
    check_caption_numbers()
    with open(os.path.join(HERE, "figure_manifest.json"), "w") as fh:
        json.dump(MANIFEST, fh, indent=2)
    for f in ("fig_spectral_decay.pdf", "fig_super_resolution.pdf"):
        p = os.path.join(HERE, f)
        print(f"wrote {f} ({os.path.getsize(p) // 1024} KB)")
    print("caption-number self-check passed; provenance in figure_manifest.json")
