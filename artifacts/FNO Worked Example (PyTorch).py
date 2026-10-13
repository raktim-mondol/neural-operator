"""
fno_example.py — Fourier Neural Operator tutorial example (PyTorch, CPU).

Problem: 1-D periodic heat diffusion.
    u_t = alpha * u_xx,   u(x,0) = u_0(x),   x in [0,1) periodic
    alpha = 0.01, T = 1.0.

Analytic solution (spectral; exact, up to numerical precision, on grids that resolve these band-limited periodic inputs):
    u(x,T) = F^{-1}( F(u_0)_k * exp(-alpha (2 pi k)^2 T) )

Target operator:  G: u_0(.) -> u(.,T)    (function-to-function map)

We build a small FNO with one Fourier layer, train on random smooth
initial functions, then test on unseen initial functions AND on a finer
grid (zero-shot super-resolution: no retraining).
"""
import torch
import numpy as np

torch.manual_seed(0)
np.random.seed(0)
ALPHA, T_END = 0.01, 1.0
DTYPE = torch.float32

# ---------------------------------------------------------------
# 1) Data generation: random smooth periodic functions
# ---------------------------------------------------------------
def make_init_fns(n_funcs, n_modes=8):
    """Callables u0(x): random superpositions of cosines (smooth, periodic)."""
    funcs = []
    for _ in range(n_funcs):
        coeffs = np.random.randn(n_modes)
        phases = np.random.uniform(0, 2*np.pi, n_modes)
        amps   = 1.0 / np.arange(1, n_modes+1) ** 1.5
        funcs.append((coeffs, phases, amps))
    def make_u0(params):
        c, p, a = params
        def u0(x):
            s = np.zeros_like(x)
            for k in range(len(c)):
                s += c[k]*a[k]*np.cos(2*np.pi*(k+1)*x + p[k])
            return s
        return u0
    return [make_u0(p) for p in funcs]

def heat_solve_exact(u0_t, alpha=ALPHA, T=T_END):
    """Exact periodic heat solution. u0_t: torch (B,N,1)."""
    with torch.no_grad():
        N = u0_t.shape[1]
        c = torch.fft.rfft(u0_t, dim=1)                       # (B,F,1)
        k = torch.fft.rfftfreq(N, device=u0_t.device) * N
        decay = torch.exp(-alpha*(2*np.pi*k)**2 * T)[None, :, None]
        return torch.fft.irfft(c * decay, n=N, dim=1)          # (B,N,1)

def dataset(fns, N):
    x = np.linspace(0, 1, N, endpoint=False)
    U0 = np.stack([f(x) for f in fns])[:, :, None]
    U0 = torch.tensor(U0, dtype=DTYPE)
    return U0, heat_solve_exact(U0)

# ---------------------------------------------------------------
# 2) Tiny FNO in PyTorch (one Fourier layer)
# ---------------------------------------------------------------
class TinyFNO(torch.nn.Module):
    """
    v1  = P(u)                              lift (pointwise linear)
    v2  = tanh( W1 v1 + FFT^{-1}(R * FFT(v1)) + b1 )   Fourier layer
    out = Q(v2)                              project (pointwise linear)

    R: complex tensor (n_modes, d_hidden, d_hidden), applied per retained
    Fourier mode (channel mixing). Modes above n_modes are truncated.
    """
    def __init__(self, d_in=1, d_out=1, d_hidden=16, n_modes=12):
        super().__init__()
        self.P  = torch.nn.Parameter(torch.randn(d_in, d_hidden) / d_hidden**0.5)
        self.W1 = torch.nn.Parameter(torch.randn(d_hidden, d_hidden) / d_hidden**0.5)
        self.b1 = torch.nn.Parameter(torch.zeros(d_hidden))
        # complex weights: R[m, h, i]
        Rr = torch.randn(n_modes, d_hidden, d_hidden) / d_hidden**0.5
        Ri = torch.randn(n_modes, d_hidden, d_hidden) / d_hidden**0.5
        self.Rr = torch.nn.Parameter(Rr)
        self.Ri = torch.nn.Parameter(Ri)
        self.Q  = torch.nn.Parameter(torch.randn(d_hidden, d_out) / d_hidden**0.5)
        self.n_modes = n_modes

    def forward(self, u):
        B, N, _ = u.shape
        v1 = torch.einsum('bnm,mh->bnh', u, self.P)            # (B,N,H)
        v1_f = torch.fft.rfft(v1, dim=1)                        # (B,F,H) complex
        F = v1_f.shape[1]
        m = min(self.n_modes, F)
        vf = v1_f[:, :m]                                         # (B,m,H)
        vr, vi = vf.real, vf.imag
        # complex multiply as real arithmetic:
        # (vr + i vi) * (Rr + i Ri) = (vr Rr - vi Ri) + i (vr Ri + vi Rr)
        Rf_re = torch.einsum('bfh,fhi->bfi', vr, self.Rr[:m]) - torch.einsum('bfh,fhi->bfi', vi, self.Ri[:m])
        Rf_im = torch.einsum('bfh,fhi->bfi', vr, self.Ri[:m]) + torch.einsum('bfh,fhi->bfi', vi, self.Rr[:m])
        Rf = torch.zeros(B, F, v1.shape[2], dtype=torch.complex64,
                         device=u.device)
        Rf[:, :m] = Rf_re.to(torch.complex64) + 1j*Rf_im.to(torch.complex64)
        ker = torch.fft.irfft(Rf, n=N, dim=1)                    # (B,N,H)
        z = torch.einsum('bnh,hi->bni', v1, self.W1) + ker + self.b1
        a = torch.tanh(z)
        return torch.einsum('bnh,hk->bnk', a, self.Q)

# ---------------------------------------------------------------
# 3) Train
# ---------------------------------------------------------------
N = 64
train_fns = make_init_fns(300)
val_fns   = make_init_fns(50)
U0_tr, UT_tr = dataset(train_fns, N)
U0_va, UT_va = dataset(val_fns, N)

model = TinyFNO(d_in=1, d_out=1, d_hidden=16, n_modes=12)
opt = torch.optim.Adam(model.parameters(), lr=1e-3)
sched = torch.optim.lr_scheduler.StepLR(opt, step_size=100, gamma=0.5)

def rel_l2(pred, true):
    num = (pred - true).norm(dim=(1,2))
    den = true.norm(dim=(1,2)).clamp_min(1e-9)
    return (num/den).mean().item()

EPOCHS, BATCH = 400, 32
for epoch in range(1, EPOCHS+1):
    perm = torch.randperm(len(U0_tr))
    for b in range(0, len(U0_tr), BATCH):
        sel = perm[b:b+BATCH]
        out = model(U0_tr[sel])
        # per-sample relative L2 squared (correct formula, no extra 1/N)
        num = (out - UT_tr[sel]).square().sum(dim=(1,2))
        den = UT_tr[sel].square().sum(dim=(1,2)).clamp_min(1e-12)
        loss = (num / den).mean()
        opt.zero_grad(); loss.backward(); opt.step()
    sched.step()
    if epoch % 50 == 0:
        with torch.no_grad():
            val_out = model(U0_va)
        print(f"epoch {epoch:3d}  val rel-L2 {rel_l2(val_out, UT_va):.4f}")

# ---------------------------------------------------------------
# 4) Evaluate on unseen initial functions (held-out)
# ---------------------------------------------------------------
test_fns = make_init_fns(50)
U0_te, UT_te = dataset(test_fns, N)
with torch.no_grad():
    pred = model(U0_te)
print(f"\n[64-pt grid]   held-out rel-L2 error: {rel_l2(pred, UT_te):.4f}")

# ---------------------------------------------------------------
# 5) Zero-shot super-resolution: same underlying functions, N=256
# ---------------------------------------------------------------
N2 = 256
U0_te2, UT_te2 = dataset(test_fns, N2)
with torch.no_grad():
    pred2 = model(U0_te2)
print(f"[256-pt grid]  held-out rel-L2 error (no retraining): {rel_l2(pred2, UT_te2):.4f}")

# save results for plotting
import os
np.savez(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fno_results.npz'),
         x=np.linspace(0,1,N,endpoint=False),
         u0=U0_te[0,:,0].numpy(), true=UT_te[0,:,0].numpy(), pred=pred[0,:,0].numpy(),
         x2=np.linspace(0,1,N2,endpoint=False),
         u0_2=U0_te2[0,:,0].numpy(), true2=UT_te2[0,:,0].numpy(), pred2=pred2[0,:,0].numpy())
print("saved fno_results.npz")
