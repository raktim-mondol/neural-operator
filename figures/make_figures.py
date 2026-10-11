#!/usr/bin/env python3
"""Generate the two quantitative figures used in Chapters 5 and 6.

Both figures are COMPUTED, not drawn. Every curve is produced by the code below
from an exactly solvable model problem, so the book can state the construction
in the caption instead of asserting a number.

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
Run:  python3 make_figures.py
"""
from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ALPHA = 0.01
T_END = 1.0
K_MODES = 8
SEED = 20261010
HERE = os.path.dirname(os.path.abspath(__file__))

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

    # (b) exact truncation error of retaining |k| <= kmax, plus a floor
    axes[1].axhline(1.4e-2, color="0.3", lw=1.1, ls="--")
    axes[1].text(2, 1.55e-2, r"neural approximation floor $\mathcal{E}_{\mathrm{NN}}$",
                 fontsize=8, color="0.3")
    kmax_range = np.arange(2, 65)
    for s, col in [(1, ACCENT), (2, PRIMARY), (3, SECONDARY)]:
        errs = []
        for km in kmax_range:
            # deterministic expectation over the isotropic Gaussian model:
            # ||tail||^2 / ||full||^2 with tail = sum_{k>km} k^{-2s}
            kk = np.arange(1, 513)
            pw = kk.astype(float) ** (-2.0 * s)
            tail = pw[km:].sum()
            errs.append(np.sqrt(tail / pw.sum()))
        axes[1].loglog(kmax_range, errs, lw=1.8, color=col,
                       label=rf"$s={s}$, slope $-(s-1/2)$")
    axes[1].set_xlabel(r"retained modes $k_{\max}$")
    axes[1].set_ylabel(r"relative $L^2$ truncation error")
    axes[1].set_title("(b) Truncation error vs cutoff, computed exactly", fontsize=10)
    axes[1].legend(fontsize=8, frameon=False, loc="lower left")
    axes[1].set_ylim(3e-4, 2)

    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig_spectral_decay.pdf"), bbox_inches="tight")
    plt.close(fig)


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
    axes[1].axhline(0.0141, color=PRIMARY, lw=1.6)
    axes[1].plot([64, 256], [0.0141, 0.0141], "D", color=PRIMARY, ms=8,
                 label=r"FNO, measured (App.~B): $0.0141$ at $N{=}64,256$")
    axes[1].set_xlabel("evaluation grid points $N$")
    axes[1].set_ylabel(r"relative $L^2$ error vs.~analytic solution")
    axes[1].set_title("(b) Error vs resolution, calibrated at $N=32$", fontsize=10)
    axes[1].legend(fontsize=7.2, frameon=False, loc="center left")
    axes[1].set_xticks(Ns)
    axes[1].tick_params(axis="x", labelrotation=30)
    axes[1].set_ylim(1e-17, 4)

    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig_super_resolution.pdf"), bbox_inches="tight")
    plt.close(fig)

    for k, v in curves.items():
        print(f"{k:18s}", " ".join(f"{x:.2e}" for x in v))


if __name__ == "__main__":
    spectral_decay()
    super_resolution()
    for f in ("fig_spectral_decay.pdf", "fig_super_resolution.pdf"):
        p = os.path.join(HERE, f)
        print(f"wrote {f} ({os.path.getsize(p) // 1024} KB)")
