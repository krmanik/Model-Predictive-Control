#!/usr/bin/env python3
"""Author Model Predictive Control coding challenges, grouped by chapter and
tied to a specific book section. Reference solutions are pure-python so the
expected outputs are computed here and embedded -> src/lib/data/challenges.json"""
import json, math, os

CH = {}
def add(chap, **kw): CH.setdefault(chap, []).append(kw)

# ============================ reference solutions ============================
# --- shared linear algebra ---
def quad_form(Q, x):
    n = len(x)
    return sum(x[i]*Q[i][j]*x[j] for i in range(n) for j in range(n))
def matmul(A, B):
    n, m, p = len(A), len(B), len(B[0])
    return [[sum(A[i][k]*B[k][j] for k in range(m)) for j in range(p)] for i in range(n)]
def lin_step(A, B, x, u):
    return [A[0][0]*x[0]+A[0][1]*x[1]+B[0]*u, A[1][0]*x[0]+A[1][1]*x[1]+B[1]*u]

# --- Ch1: Getting Started ---
def c2d_scalar(a, b, dt):
    ad = math.exp(a*dt)
    bd = b*(math.exp(a*dt) - 1)/a
    return [ad, bd]
def in_box(lo, hi, x):
    return all(lo[i] <= x[i] <= hi[i] for i in range(len(x)))
def gaussian_pdf(x, mu, sigma):
    return math.exp(-0.5*((x-mu)/sigma)**2)/(sigma*math.sqrt(2*math.pi))
def riccati_step(P, a, b, q, r):
    return q + a*a*P - (a*P*b)**2/(r + b*b*P)
def lqr_gain_scalar(a, b, q, r):
    P = q
    for _ in range(1000):
        Pn = q + a*a*P - (a*P*b)**2/(r + b*b*P)
        if abs(Pn - P) < 1e-12: P = Pn; break
        P = Pn
    return (b*P*a)/(r + b*b*P)
def ctrb2(A, B):
    return [[B[0], A[0][0]*B[0]+A[0][1]*B[1]], [B[1], A[1][0]*B[0]+A[1][1]*B[1]]]
def is_controllable(A, B):
    Ab = [A[0][0]*B[0]+A[0][1]*B[1], A[1][0]*B[0]+A[1][1]*B[1]]
    return abs(B[0]*Ab[1] - B[1]*Ab[0]) > 1e-9
def is_observable(A, C):
    CA = [C[0]*A[0][0]+C[1]*A[1][0], C[0]*A[0][1]+C[1]*A[1][1]]
    return abs(C[0]*CA[1] - C[1]*CA[0]) > 1e-9
def is_stable_cl(a, b, k):
    return abs(a - b*k) < 1
def least_squares_1d(xs, ys):
    n = len(xs); sx = sum(xs); sy = sum(ys)
    sxx = sum(x*x for x in xs); sxy = sum(xs[i]*ys[i] for i in range(n))
    slope = (n*sxy - sx*sy)/(n*sxx - sx*sx)
    return [slope, (sy - slope*sx)/n]
def target_input(a, b, xsp):
    return (1 - a)*xsp/b

# --- Ch2: Regulation ---
def stage_cost(Q, R, x, u):
    return quad_form(Q, x) + quad_form(R, u)
def is_posdef2(Q):
    return Q[0][0] > 0 and (Q[0][0]*Q[1][1] - Q[0][1]*Q[1][0]) > 0
def traj_cost(xs, us, q, r, pf):
    return sum(q*x*x for x in xs[:-1]) + sum(r*u*u for u in us) + pf*xs[-1]*xs[-1]
def first_control(useq): return useq[0]
def terminal_cost(pf, x): return pf*sum(xi*xi for xi in x)
def lyap_decrease(Vx, Vnext, stage): return Vnext - Vx <= -stage + 1e-9
def is_exp_stable(a): return abs(a) < 1
def in_terminal_set(P, x, c): return quad_form(P, x) <= c + 1e-9
def shift_sequence(useq, uf): return useq[1:] + [uf]
def average_cost(cs): return sum(cs)/len(cs)
def quantize(u, levels): return min(levels, key=lambda L: abs(L - u))

# --- Ch3: Robust and Stochastic ---
def minkowski_interval(a, b): return [a[0]+b[0], a[1]+b[1]]
def pontry_diff(A, B): return [A[0]-B[0], A[1]-B[1]]
def tighten(box, m): return [box[0]+m, box[1]-m]
def support_box(lo, hi, d): return sum(max(lo[i]*d[i], hi[i]*d[i]) for i in range(len(d)))
def worst_case_cost(costs): return min(max(row) for row in costs)
def in_tube(center, radius, x):
    return all(abs(x[i]-center[i]) <= radius + 1e-9 for i in range(len(x)))
def robust_margin(box, dist): return (box[1]-box[0])/2 - dist
def reach_interval(a, box, w): return [a*box[0]-w, a*box[1]+w]
def mrpi_bound(alpha, w, n): return w*(1 - alpha**n)/(1 - alpha)
def chance_tighten(bound, k, sigma): return bound - k*sigma

# --- Ch4: State Estimation ---
def kalman_gain(ppred, h, r): return ppred*h/(h*h*ppred + r)
def kalman_update(xpred, ppred, y, h, r):
    K = ppred*h/(h*h*ppred + r)
    return [xpred + K*(y - h*xpred), (1 - K*h)*ppred]
def covariance_predict(a, p, q): return a*a*p + q
def innovation(y, h, x): return y - h*x
def weighted_sq(e, w): return w*e*e
def arrival_cost(x, xbar, pinv): return 0.5*pinv*(x - xbar)**2
def mhe_cost(arrival, stagecosts): return arrival + sum(stagecosts)
def kf_steady_variance(a, h, q, r):
    p = q
    for _ in range(1000):
        ppred = a*a*p + q
        pn = ppred - ppred*ppred*h*h/(h*h*ppred + r)
        if abs(pn - p) < 1e-13: p = pn; break
        p = pn
    return p

# --- Ch5: Output MPC ---
def disturbance_estimate(y, ymodel): return y - ymodel
def luenberger_step(xhat, a, b, u, l, c, y): return a*xhat + b*u + l*(y - c*xhat)
def is_detectable_scalar(a, c): return abs(a) < 1 or abs(c) > 1e-9
def augment_step(x, d, a, b, bd, u): return a*x + b*u + bd*d
def target_ss(a, b, c, d, ysp):
    xss = (ysp - d)/c
    return [xss, (1 - a)*xss/b]
def closed_poles(a, b, k, c, l): return [a - b*k, a - l*c]

# --- Ch6: Distributed MPC ---
def consensus_step(vals, i, neighbors):
    grp = [vals[i]] + [vals[j] for j in neighbors]
    return sum(grp)/len(grp)
def jacobi_step(A, b, x):
    n = len(b)
    return [(b[i] - sum(A[i][j]*x[j] for j in range(n) if j != i))/A[i][i] for i in range(n)]
def gauss_seidel_step(A, b, x):
    xn = list(x); n = len(b)
    for i in range(n):
        xn[i] = (b[i] - sum(A[i][j]*xn[j] for j in range(n) if j != i))/A[i][i]
    return xn
def convex_combine(xold, xnew, w):
    return [(1 - w)*xold[i] + w*xnew[i] for i in range(len(xold))]
def cooperative_cost(costs, weights):
    return sum(costs[i]*weights[i] for i in range(len(costs)))
def player_average(vals): return sum(vals)/len(vals)
def coupled_dynamics(A, x):
    n = len(x)
    return [sum(A[i][j]*x[j] for j in range(n)) for i in range(n)]
def max_diff(a, b): return max(abs(a[i]-b[i]) for i in range(len(a)))

# --- Ch7: Explicit Control Laws ---
def eval_pwa(regions, x):
    for lo, hi, gain, off in regions:
        if lo <= x < hi: return gain*x + off
    return None
def eval_pwq(regions, x):
    for lo, hi, a, b, c in regions:
        if lo <= x < hi: return a*x*x + b*x + c
    return None
def find_region(bounds, x):
    for i, (lo, hi) in enumerate(bounds):
        if lo <= x < hi: return i
    return -1
def in_region(H, g, x):
    return all(sum(H[i][j]*x[j] for j in range(len(x))) <= g[i] + 1e-9 for i in range(len(g)))
def saturate(u, umin, umax): return max(umin, min(umax, u))
def qp_scalar(q, c, umin, umax): return max(umin, min(umax, -c/q))
def explicit_lqr(k, x, umin, umax): return max(umin, min(umax, -k*x))

# --- Ch8: Numerical Optimal Control ---
def euler_step(x, u, a, b, dt): return x + dt*(a*x + b*u)
def implicit_euler(x, a, dt): return x/(1 - dt*a)
def rk2_step(x, a, dt):
    k1 = a*x
    return x + dt*a*(x + dt/2*k1)
def rk4_step(x, a, dt):
    f = lambda s: a*s
    k1 = f(x); k2 = f(x + dt/2*k1); k3 = f(x + dt/2*k2); k4 = f(x + dt*k3)
    return x + dt/6*(k1 + 2*k2 + 2*k3 + k4)
def newton_step(x, fx, dfx): return x - fx/dfx
def newton_sqrt(s, n):
    x = s if s > 0 else 1.0
    for _ in range(n): x = 0.5*(x + s/x)
    return x
def forward_diff(f0, f1, dx): return (f1 - f0)/dx
def central_diff(fm, fp, dx): return (fp - fm)/(2*dx)
def defect(xa, xb): return xa - xb
def normal_matrix(J):
    return [[J[i]*J[j] for j in range(len(J))] for i in range(len(J))]
def single_shooting(x0, us, a, b, dt):
    x = x0
    for u in us: x = x + dt*(a*x + b*u)
    return x

# ============================ challenge catalogue ============================
PI = math.pi
def C(chap, id, title, diff, func, tags, section, prompt, starter, sol, ref, args):
    add(chap, id=id, title=title, difficulty=diff, func=func, tags=tags,
        section=section, prompt=prompt, starter=starter, sol=sol, ref=ref, args=args)

# ------------------------------------------------------------------ Ch1
C('ch01','ch01-lin-step',"Linear State Update x⁺ = Ax + Bu",'Medium','lin_step',['model'],'1.2.1',
 "The core discrete linear model is x⁺ = A x + B u. For 2×2 A, length-2 B and scalar input u,\n\nImplement `lin_step(A, B, x, u)` returning the next state (length-2).",
 "def lin_step(A, B, x, u):\n    pass\n",lin_step,
 "def lin_step(A, B, x, u):\n    return [A[0][0]*x[0]+A[0][1]*x[1]+B[0]*u,\n            A[1][0]*x[0]+A[1][1]*x[1]+B[1]*u]\n",
 [[[[1,0.1],[0,1]],[0,0.1],[1,0],2],[[[0.9,0],[0,0.8]],[1,1],[2,-1],1]])

C('ch01','ch01-c2d',"Discretize a Scalar System",'Hard','c2d_scalar',['discretization'],'1.2.4',
 "Continuous ẋ = a x + b u sampled with zero-order hold over dt becomes x⁺ = a_d x + b_d u with\n\n    a_d = e^{a·dt},   b_d = b·(e^{a·dt} − 1)/a\n\nImplement `c2d_scalar(a, b, dt)` → [a_d, b_d] (assume a ≠ 0).",
 "import math\n\ndef c2d_scalar(a, b, dt):\n    pass\n",c2d_scalar,
 "import math\n\ndef c2d_scalar(a, b, dt):\n    ad = math.exp(a*dt)\n    bd = b*(math.exp(a*dt) - 1)/a\n    return [ad, bd]\n",
 [[-1,1,0.1],[0.5,2,0.2],[-2,1,0.5]])

C('ch01','ch01-inbox',"State Constraints (Box)",'Easy','in_box',['constraints'],'1.2.5',
 "Constraints X are often a box: lo ≤ x ≤ hi componentwise. Implement `in_box(lo, hi, x)` → bool.",
 "def in_box(lo, hi, x):\n    pass\n",in_box,
 "def in_box(lo, hi, x):\n    return all(lo[i] <= x[i] <= hi[i]\n              for i in range(len(x)))\n",
 [[[-1,-1],[1,1],[0.5,0]],[[-1,-1],[1,1],[2,0]]])

C('ch01','ch01-quadform',"Quadratic Form xᵀQx",'Easy','quad_form',['cost'],'1.3.1',
 "The LQ cost is built from quadratic forms xᵀQx = Σᵢ Σⱼ xᵢ Qᵢⱼ xⱼ. Implement `quad_form(Q, x)`.",
 "def quad_form(Q, x):\n    pass\n",quad_form,
 "def quad_form(Q, x):\n    n = len(x)\n    return sum(x[i]*Q[i][j]*x[j]\n              for i in range(n) for j in range(n))\n",
 [[[[2,0],[0,3]],[1,1]],[[[1,0.5],[0.5,1]],[2,-1]]])

C('ch01','ch01-riccati',"One Riccati Backward Step",'Medium','riccati_step',['dp','riccati'],'1.3.3',
 "The dynamic-programming (Riccati) recursion for the scalar LQ cost-to-go P is\n\n    P⁻ = q + a²P − (aPb)²/(r + b²P)\n\nImplement `riccati_step(P, a, b, q, r)`.",
 "def riccati_step(P, a, b, q, r):\n    pass\n",riccati_step,
 "def riccati_step(P, a, b, q, r):\n    return q + a*a*P - (a*P*b)**2/(r + b*b*P)\n",
 [[1,1,1,1,1],[0.5,1.2,1,2,1],[3,0.9,0.5,1,0.1]])

C('ch01','ch01-lqr',"Infinite-Horizon LQR Gain",'Hard','lqr_gain_scalar',['lqr','riccati'],'1.3.4',
 "Iterate the Riccati recursion to its fixed point P, then the optimal gain of x⁺ = a x + b u (cost Σ q x² + r u²) is K = bPa/(r + b²P), u = −Kx.\n\nImplement `lqr_gain_scalar(a, b, q, r)`.",
 "def lqr_gain_scalar(a, b, q, r):\n    pass\n",lqr_gain_scalar,
 "def lqr_gain_scalar(a, b, q, r):\n    P = q\n    for _ in range(1000):\n        Pn = q + a*a*P - (a*P*b)**2/(r + b*b*P)\n        if abs(Pn - P) < 1e-12:\n            P = Pn; break\n        P = Pn\n    return (b*P*a)/(r + b*b*P)\n",
 [[1,1,1,1],[1.1,1,1,1],[0.9,0.5,2,1]])

C('ch01','ch01-ctrb',"Controllability Matrix",'Medium','ctrb2',['controllability'],'1.3.5',
 "For (A, b) with 2×2 A the controllability matrix is 𝒞 = [b  Ab] (columns).\n\nImplement `ctrb2(A, B)` returning the 2×2 matrix [[b₀, (Ab)₀], [b₁, (Ab)₁]].",
 "def ctrb2(A, B):\n    pass\n",ctrb2,
 "def ctrb2(A, B):\n    return [[B[0], A[0][0]*B[0]+A[0][1]*B[1]],\n            [B[1], A[1][0]*B[0]+A[1][1]*B[1]]]\n",
 [[[[0,1],[0,0]],[0,1]],[[[1,1],[0,1]],[1,0]]])

C('ch01','ch01-controllable',"Is the System Controllable?",'Medium','is_controllable',['controllability'],'1.3.5',
 "(A, b) is controllable iff det[b  Ab] ≠ 0. Implement `is_controllable(A, B)` → bool.",
 "def is_controllable(A, B):\n    pass\n",is_controllable,
 "def is_controllable(A, B):\n    Ab = [A[0][0]*B[0]+A[0][1]*B[1],\n          A[1][0]*B[0]+A[1][1]*B[1]]\n    return abs(B[0]*Ab[1] - B[1]*Ab[0]) > 1e-9\n",
 [[[[0,1],[0,0]],[0,1]],[[[1,0],[0,1]],[1,0]]])

C('ch01','ch01-stable-cl',"Closed-Loop Stability (Scalar)",'Easy','is_stable_cl',['convergence'],'1.3.6',
 "The LQR closed loop x⁺ = (a − bK)x converges iff |a − bK| < 1.\n\nImplement `is_stable_cl(a, b, k)` → bool.",
 "def is_stable_cl(a, b, k):\n    pass\n",is_stable_cl,
 "def is_stable_cl(a, b, k):\n    return abs(a - b*k) < 1\n",
 [[1,1,0.5],[1,1,3],[1.2,1,0.1]])

C('ch01','ch01-gauss',"Gaussian Density",'Easy','gaussian_pdf',['estimation'],'1.4.1',
 "State estimation assumes Gaussian noise. The 1-D density is\n\n    p(x) = 1/(σ√(2π)) · exp(−½((x−μ)/σ)²)\n\nImplement `gaussian_pdf(x, mu, sigma)`.",
 "import math\n\ndef gaussian_pdf(x, mu, sigma):\n    pass\n",gaussian_pdf,
 "import math\n\ndef gaussian_pdf(x, mu, sigma):\n    return math.exp(-0.5*((x-mu)/sigma)**2)/(sigma*math.sqrt(2*math.pi))\n",
 [[0,0,1],[1,0,1],[2,2,0.5]])

C('ch01','ch01-lstsq',"Least-Squares Line Fit",'Medium','least_squares_1d',['least-squares'],'1.4.3',
 "Optimal estimation is rooted in least squares. Fit y = m x + c by the normal equations\n\n    m = (nΣxy − ΣxΣy)/(nΣx² − (Σx)²),   c = (Σy − mΣx)/n\n\nImplement `least_squares_1d(xs, ys)` → [m, c].",
 "def least_squares_1d(xs, ys):\n    pass\n",least_squares_1d,
 "def least_squares_1d(xs, ys):\n    n = len(xs); sx = sum(xs); sy = sum(ys)\n    sxx = sum(x*x for x in xs)\n    sxy = sum(xs[i]*ys[i] for i in range(n))\n    m = (n*sxy - sx*sy)/(n*sxx - sx*sx)\n    return [m, (sy - m*sx)/n]\n",
 [[[0,1,2,3],[1,3,5,7]],[[0,1,2],[1,1,1]]])

C('ch01','ch01-observable',"Is the System Observable?",'Medium','is_observable',['observability'],'1.4.5',
 "With output y = C x, the pair (A, C) is observable iff det[[C],[CA]] ≠ 0 (C a length-2 row).\n\nImplement `is_observable(A, C)` → bool.",
 "def is_observable(A, C):\n    pass\n",is_observable,
 "def is_observable(A, C):\n    CA = [C[0]*A[0][0]+C[1]*A[1][0],\n          C[0]*A[0][1]+C[1]*A[1][1]]\n    return abs(C[0]*CA[1] - C[1]*CA[0]) > 1e-9\n",
 [[[[1,1],[0,1]],[1,0]],[[[1,0],[0,1]],[1,0]]])

C('ch01','ch01-target',"Steady-State Input for a Setpoint",'Easy','target_input',['tracking'],'1.5.1',
 "To hold x at a setpoint x_sp for x⁺ = a x + b u, the steady input solves x_sp = a x_sp + b u_ss, so u_ss = (1 − a)x_sp/b.\n\nImplement `target_input(a, b, xsp)`.",
 "def target_input(a, b, xsp):\n    pass\n",target_input,
 "def target_input(a, b, xsp):\n    return (1 - a)*xsp/b\n",
 [[0.9,1,5],[0.5,2,3],[0.8,0.5,10]])

# ------------------------------------------------------------------ Ch2
C('ch02','ch02-stagecost',"MPC Stage Cost ℓ(x,u)",'Medium','stage_cost',['cost'],'2.2',
 "The regulation stage cost is ℓ(x,u) = xᵀQx + uᵀRu. Given matrices Q, R and vectors x, u,\n\nImplement `stage_cost(Q, R, x, u)`.",
 "def stage_cost(Q, R, x, u):\n    pass\n",stage_cost,
 "def stage_cost(Q, R, x, u):\n    def qf(M, v):\n        n = len(v)\n        return sum(v[i]*M[i][j]*v[j]\n                  for i in range(n) for j in range(n))\n    return qf(Q, x) + qf(R, u)\n",
 [[[[1,0],[0,1]],[[1]],[1,2],[3]],[[[2,0],[0,2]],[[0.5]],[1,1],[2]]])

C('ch02','ch02-trajcost',"Finite-Horizon Cost of a Trajectory",'Medium','traj_cost',['cost','horizon'],'2.3',
 "The MPC objective over a horizon (scalar states/inputs) is\n\n    J = Σₖ (q xₖ² + r uₖ²) + p_f x_N²\n\n`xs` has N+1 states, `us` has N inputs. Implement `traj_cost(xs, us, q, r, pf)`.",
 "def traj_cost(xs, us, q, r, pf):\n    pass\n",traj_cost,
 "def traj_cost(xs, us, q, r, pf):\n    j = sum(q*x*x for x in xs[:-1]) + sum(r*u*u for u in us)\n    return j + pf*xs[-1]*xs[-1]\n",
 [[[1,0.5,0],[1,1],1,1,5],[[2,1],[0.5],1,2,1]])

C('ch02','ch02-first',"Receding Horizon: Apply First Move",'Easy','first_control',['receding-horizon'],'2.2',
 "MPC solves for a whole input sequence but *applies only the first input*, then re-optimizes.\n\nImplement `first_control(useq)`.",
 "def first_control(useq):\n    pass\n",first_control,
 "def first_control(useq):\n    return useq[0]\n",
 [[[3,1,-2,0]],[[-1.5,2,2]]])

C('ch02','ch02-posdef',"Positive Definite Penalty (2×2)",'Easy','is_posdef2',['stability'],'2.4.2',
 "Stabilizing MPC needs Q ≻ 0. By Sylvester's criterion a symmetric 2×2 Q is PD iff Q₀₀ > 0 and det Q > 0.\n\nImplement `is_posdef2(Q)` → bool.",
 "def is_posdef2(Q):\n    pass\n",is_posdef2,
 "def is_posdef2(Q):\n    det = Q[0][0]*Q[1][1] - Q[0][1]*Q[1][0]\n    return Q[0][0] > 0 and det > 0\n",
 [[[[2,0],[0,3]]],[[[1,2],[2,1]]],[[[0,0],[0,1]]]])

C('ch02','ch02-lyap',"Lyapunov Descent Condition",'Medium','lyap_decrease',['stability'],'2.4.2',
 "The MPC value function is a Lyapunov function when it decreases by at least the stage cost:\n\n    V(x⁺) − V(x) ≤ −ℓ(x,u)\n\nGiven Vx = V(x), Vnext = V(x⁺) and stage = ℓ, implement `lyap_decrease(Vx, Vnext, stage)` → bool.",
 "def lyap_decrease(Vx, Vnext, stage):\n    pass\n",lyap_decrease,
 "def lyap_decrease(Vx, Vnext, stage):\n    return Vnext - Vx <= -stage + 1e-9\n",
 [[10,7,3],[10,8,3],[5,4,1]])

C('ch02','ch02-expstable',"Exponential Stability (Scalar)",'Easy','is_exp_stable',['stability'],'2.4.3',
 "A scalar mode x⁺ = a x is exponentially stable iff |a| < 1.\n\nImplement `is_exp_stable(a)` → bool.",
 "def is_exp_stable(a):\n    pass\n",is_exp_stable,
 "def is_exp_stable(a):\n    return abs(a) < 1\n",
 [[0.5],[1],[-0.9],[1.2]])

C('ch02','ch02-terminal',"Terminal Cost Vf(x)",'Easy','terminal_cost',['cost'],'2.5.1',
 "The unconstrained-LQR terminal cost is Vf(x) = p_f · xᵀx = p_f Σ xᵢ².\n\nImplement `terminal_cost(pf, x)`.",
 "def terminal_cost(pf, x):\n    pass\n",terminal_cost,
 "def terminal_cost(pf, x):\n    return pf*sum(xi*xi for xi in x)\n",
 [[10,[1,2]],[2,[0,0,3]],[1,[1,1,1,1]]])

C('ch02','ch02-termset',"Terminal Constraint Set Xf",'Medium','in_terminal_set',['terminal-set'],'2.6',
 "A common terminal set is the sublevel set X_f = {x : xᵀP x ≤ c}.\n\nImplement `in_terminal_set(P, x, c)` → bool.",
 "def in_terminal_set(P, x, c):\n    pass\n",in_terminal_set,
 "def in_terminal_set(P, x, c):\n    qf = sum(x[i]*P[i][j]*x[j]\n            for i in range(len(x)) for j in range(len(x)))\n    return qf <= c + 1e-9\n",
 [[[[1,0],[0,1]],[0.5,0.5],1],[[[1,0],[0,1]],[1,1],1]])

C('ch02','ch02-shift',"Warm-Start Shift (Suboptimal MPC)",'Medium','shift_sequence',['suboptimal'],'2.7',
 "Suboptimal MPC warm-starts by shifting the previous input sequence: drop the applied first input and append a terminal input u_f.\n\nImplement `shift_sequence(useq, uf)`.",
 "def shift_sequence(useq, uf):\n    pass\n",shift_sequence,
 "def shift_sequence(useq, uf):\n    return useq[1:] + [uf]\n",
 [[[1,2,3],0],[[0.5,-1,2,4],0]])

C('ch02','ch02-avg',"Asymptotic Average Cost",'Easy','average_cost',['economic'],'2.8.1',
 "Economic MPC studies the average stage cost over time, (1/N)Σ ℓₖ.\n\nImplement `average_cost(cs)` (mean of the list).",
 "def average_cost(cs):\n    pass\n",average_cost,
 "def average_cost(cs):\n    return sum(cs)/len(cs)\n",
 [[[1,2,3,4]],[[5,5,5]]])

C('ch02','ch02-quantize',"Discrete Actuator: Nearest Level",'Medium','quantize',['discrete-actuators'],'2.9',
 "With discrete actuators the input must snap to an allowed level. Return the level nearest to u (ties → the one that appears first).\n\nImplement `quantize(u, levels)`.",
 "def quantize(u, levels):\n    pass\n",quantize,
 "def quantize(u, levels):\n    return min(levels, key=lambda L: abs(L - u))\n",
 [[0.7,[0,1,2]],[1.4,[0,1,2]],[-0.6,[-1,0,1]]])

# ------------------------------------------------------------------ Ch3
C('ch03','ch03-margin',"Inherent Robustness Margin",'Easy','robust_margin',['robustness'],'3.2',
 "A box constraint [lo, hi] tolerates a disturbance up to half its width minus the current offset. Return (hi − lo)/2 − dist.\n\nImplement `robust_margin(box, dist)`.",
 "def robust_margin(box, dist):\n    pass\n",robust_margin,
 "def robust_margin(box, dist):\n    return (box[1]-box[0])/2 - dist\n",
 [[[-2,2],0.5],[[-1,1],1]])

C('ch03','ch03-minmax',"Min-Max Robust Cost",'Medium','worst_case_cost',['min-max'],'3.3',
 "Min-max MPC picks the control minimizing the worst-case cost over the disturbance. `costs` is a matrix: row = control, column = disturbance. Return minᵣₒw maxᵨₗ.\n\nImplement `worst_case_cost(costs)`.",
 "def worst_case_cost(costs):\n    pass\n",worst_case_cost,
 "def worst_case_cost(costs):\n    return min(max(row) for row in costs)\n",
 [[[[3,1],[2,4]]],[[[5,5,5],[9,1,2]]]])

C('ch03','ch03-reach',"One-Step Reachable Interval",'Medium','reach_interval',['tube'],'3.4',
 "For x⁺ = a x + w with a ≥ 0, disturbance |w| ≤ W and x ∈ [lo, hi], the next state lies in\n\n    [a·lo − W, a·hi + W]\n\nImplement `reach_interval(a, box, w)`.",
 "def reach_interval(a, box, w):\n    pass\n",reach_interval,
 "def reach_interval(a, box, w):\n    return [a*box[0]-w, a*box[1]+w]\n",
 [[0.5,[-1,1],0.2],[0.9,[0,2],0.5]])

C('ch03','ch03-mink',"Minkowski Sum of Intervals",'Easy','minkowski_interval',['tube','sets'],'3.5',
 "Tubes propagate uncertainty via Minkowski sums: [a₀,a₁] ⊕ [b₀,b₁] = [a₀+b₀, a₁+b₁].\n\nImplement `minkowski_interval(a, b)`.",
 "def minkowski_interval(a, b):\n    pass\n",minkowski_interval,
 "def minkowski_interval(a, b):\n    return [a[0]+b[0], a[1]+b[1]]\n",
 [[[-1,1],[-2,2]],[[0,3],[1,1]]])

C('ch03','ch03-pontry',"Pontryagin Difference of Intervals",'Medium','pontry_diff',['sets'],'3.5',
 "Tube MPC erodes a set by the disturbance via the Pontryagin difference: for intervals A ⊖ B = [a₀ − b₀, a₁ − b₁].\n\nImplement `pontry_diff(A, B)`.",
 "def pontry_diff(A, B):\n    pass\n",pontry_diff,
 "def pontry_diff(A, B):\n    return [A[0]-B[0], A[1]-B[1]]\n",
 [[[-3,3],[-1,1]],[[-2,5],[-1,2]]])

C('ch03','ch03-tighten',"Constraint Tightening",'Easy','tighten',['tube','constraints'],'3.5',
 "Tube MPC tightens a box [lo, hi] by the tube margin m → [lo+m, hi−m].\n\nImplement `tighten(box, m)`.",
 "def tighten(box, m):\n    pass\n",tighten,
 "def tighten(box, m):\n    return [box[0]+m, box[1]-m]\n",
 [[[-5,5],1],[[0,10],2.5]])

C('ch03','ch03-mrpi',"Invariant-Set Size (Geometric Bound)",'Medium','mrpi_bound',['invariant-set'],'3.5',
 "A rigid disturbance tube with contraction α and disturbance bound w has size after n steps\n\n    w·(1 − αⁿ)/(1 − α)\n\n(the partial geometric sum). Implement `mrpi_bound(alpha, w, n)`.",
 "def mrpi_bound(alpha, w, n):\n    pass\n",mrpi_bound,
 "def mrpi_bound(alpha, w, n):\n    return w*(1 - alpha**n)/(1 - alpha)\n",
 [[0.5,1,3],[0.8,2,5],[0.5,1,10]])

C('ch03','ch03-support',"Support Function of a Box",'Medium','support_box',['sets'],'3.5',
 "The support function of an axis-aligned box in direction d is Σᵢ max(loᵢ dᵢ, hiᵢ dᵢ).\n\nImplement `support_box(lo, hi, d)`.",
 "def support_box(lo, hi, d):\n    pass\n",support_box,
 "def support_box(lo, hi, d):\n    return sum(max(lo[i]*d[i], hi[i]*d[i])\n              for i in range(len(d)))\n",
 [[[-1,-1],[1,1],[1,0]],[[-1,-2],[1,2],[-1,1]]])

C('ch03','ch03-tube',"Inside the Tube?",'Easy','in_tube',['tube'],'3.5',
 "A state is inside a tube of radius R about a center (∞-norm) iff |xᵢ − centerᵢ| ≤ R for all i.\n\nImplement `in_tube(center, radius, x)` → bool.",
 "def in_tube(center, radius, x):\n    pass\n",in_tube,
 "def in_tube(center, radius, x):\n    return all(abs(x[i]-center[i]) <= radius + 1e-9\n              for i in range(len(x)))\n",
 [[[0,0],1,[0.5,-0.5]],[[1,1],0.5,[2,1]]])

C('ch03','ch03-chance',"Chance-Constraint Tightening",'Easy','chance_tighten',['stochastic'],'3.7',
 "Stochastic MPC turns P(x ≤ b) ≥ 1−ε into a tightened deterministic bound b − k·σ (k from the quantile).\n\nImplement `chance_tighten(bound, k, sigma)`.",
 "def chance_tighten(bound, k, sigma):\n    pass\n",chance_tighten,
 "def chance_tighten(bound, k, sigma):\n    return bound - k*sigma\n",
 [[10,1.64,2],[5,2.33,0.5]])

# ------------------------------------------------------------------ Ch4
C('ch04','ch04-gain',"Kalman Gain",'Easy','kalman_gain',['kalman'],'4.2',
 "The scalar Kalman gain is K = p⁻ h / (h² p⁻ + r).\n\nImplement `kalman_gain(ppred, h, r)`.",
 "def kalman_gain(ppred, h, r):\n    pass\n",kalman_gain,
 "def kalman_gain(ppred, h, r):\n    return ppred*h/(h*h*ppred + r)\n",
 [[1,1,1],[2,1,0.5],[4,2,1]])

C('ch04','ch04-kalman',"Scalar Kalman Update",'Medium','kalman_update',['kalman'],'4.2',
 "Measurement update (y = h x + noise, var r):\n\n    K = p⁻h/(h²p⁻+r),  x⁺ = x⁻ + K(y − hx⁻),  p⁺ = (1 − Kh)p⁻\n\nImplement `kalman_update(xpred, ppred, y, h, r)` → [x⁺, p⁺].",
 "def kalman_update(xpred, ppred, y, h, r):\n    pass\n",kalman_update,
 "def kalman_update(xpred, ppred, y, h, r):\n    K = ppred*h/(h*h*ppred + r)\n    return [xpred + K*(y - h*xpred), (1 - K*h)*ppred]\n",
 [[0,1,2,1,1],[1,2,1,1,0.5],[0,4,3,2,1]])

C('ch04','ch04-predict',"Covariance Prediction",'Easy','covariance_predict',['kalman'],'4.2',
 "The scalar covariance time-update is p⁻ = a² p + q (q = process-noise variance).\n\nImplement `covariance_predict(a, p, q)`.",
 "def covariance_predict(a, p, q):\n    pass\n",covariance_predict,
 "def covariance_predict(a, p, q):\n    return a*a*p + q\n",
 [[1,1,0.1],[0.9,2,0.5],[1.1,1,0]])

C('ch04','ch04-innov',"Innovation (Residual)",'Easy','innovation',['kalman'],'4.2',
 "The innovation is e = y − h·x. Implement `innovation(y, h, x)`.",
 "def innovation(y, h, x):\n    pass\n",innovation,
 "def innovation(y, h, x):\n    return y - h*x\n",
 [[5,1,3],[2,2,1],[0,1,0]])

C('ch04','ch04-wsq',"Weighted Squared Residual",'Easy','weighted_sq',['least-squares'],'4.2',
 "The estimation objective sums weighted squared residuals w·e². Implement `weighted_sq(e, w)`.",
 "def weighted_sq(e, w):\n    pass\n",weighted_sq,
 "def weighted_sq(e, w):\n    return w*e*e\n",
 [[2,1],[3,0.5],[-4,2]])

C('ch04','ch04-arrival',"MHE Arrival Cost",'Easy','arrival_cost',['mhe'],'4.3',
 "MHE summarizes old data with an arrival cost Z(x) = ½ · pinv · (x − x̄)².\n\nImplement `arrival_cost(x, xbar, pinv)`.",
 "def arrival_cost(x, xbar, pinv):\n    pass\n",arrival_cost,
 "def arrival_cost(x, xbar, pinv):\n    return 0.5*pinv*(x - xbar)**2\n",
 [[2,0,1],[1,1,4],[3,1,0.5]])

C('ch04','ch04-mhecost',"MHE Window Objective",'Medium','mhe_cost',['mhe'],'4.3',
 "The MHE objective is the arrival cost plus the sum of stage costs in the window:\n\n    Φ = Z + Σ ℓₖ\n\nImplement `mhe_cost(arrival, stagecosts)`.",
 "def mhe_cost(arrival, stagecosts):\n    pass\n",mhe_cost,
 "def mhe_cost(arrival, stagecosts):\n    return arrival + sum(stagecosts)\n",
 [[2,[1,1,1]],[0.5,[2,3]]])

C('ch04','ch04-steady',"Steady-State Filter Variance",'Hard','kf_steady_variance',['kalman','riccati'],'4.2',
 "Iterate the filtering Riccati recursion to its fixed point (posterior variance p):\n\n    p⁻ = a²p + q,   p = p⁻ − (p⁻)²h²/(h²p⁻ + r)\n\nImplement `kf_steady_variance(a, h, q, r)`.",
 "def kf_steady_variance(a, h, q, r):\n    pass\n",kf_steady_variance,
 "def kf_steady_variance(a, h, q, r):\n    p = q\n    for _ in range(1000):\n        ppred = a*a*p + q\n        pn = ppred - ppred*ppred*h*h/(h*h*ppred + r)\n        if abs(pn - p) < 1e-13:\n            p = pn; break\n        p = pn\n    return p\n",
 [[1,1,1,1],[0.9,1,0.5,1],[1,2,1,4]])

# ------------------------------------------------------------------ Ch5
C('ch05','ch05-method',"Observer + Controller State Update",'Medium','augment_step',['output-mpc'],'5.2',
 "Output MPC drives an estimate; the augmented (disturbance) model updates\n\n    x⁺ = a x + b u + b_d d\n\nImplement `augment_step(x, d, a, b, bd, u)`.",
 "def augment_step(x, d, a, b, bd, u):\n    pass\n",augment_step,
 "def augment_step(x, d, a, b, bd, u):\n    return a*x + b*u + bd*d\n",
 [[1,0.5,0.9,1,1,2],[0,1,0.8,0.5,1,1]])

C('ch05','ch05-luen',"Luenberger Observer Step",'Medium','luenberger_step',['observer'],'5.3.2',
 "The state estimate updates x̂⁺ = a x̂ + b u + l (y − c x̂).\n\nImplement `luenberger_step(xhat, a, b, u, l, c, y)`.",
 "def luenberger_step(xhat, a, b, u, l, c, y):\n    pass\n",luenberger_step,
 "def luenberger_step(xhat, a, b, u, l, c, y):\n    return a*xhat + b*u + l*(y - c*xhat)\n",
 [[0,1,1,2,0.5,1,1],[1,0.9,0.5,0,0.3,1,2]])

C('ch05','ch05-poles',"Separation Principle: Closed-Loop Poles",'Medium','closed_poles',['separation'],'5.3.2',
 "By separation, the output-feedback poles are the controller pole a − bK and the observer pole a − LC (independent).\n\nImplement `closed_poles(a, b, k, c, l)` → [a − bK, a − LC].",
 "def closed_poles(a, b, k, c, l):\n    pass\n",closed_poles,
 "def closed_poles(a, b, k, c, l):\n    return [a - b*k, a - l*c]\n",
 [[1,1,0.5,1,0.4],[0.9,0.5,0.6,1,0.3]])

C('ch05','ch05-dist',"Disturbance Estimate (Offset-Free)",'Easy','disturbance_estimate',['offset-free'],'5.5.1',
 "Offset-free MPC augments an integrating disturbance estimated from the output error d̂ = y − y_model.\n\nImplement `disturbance_estimate(y, ymodel)`.",
 "def disturbance_estimate(y, ymodel):\n    pass\n",disturbance_estimate,
 "def disturbance_estimate(y, ymodel):\n    return y - ymodel\n",
 [[5,4],[2.5,3],[0,0]])

C('ch05','ch05-target',"Offset-Free Steady-State Target",'Hard','target_ss',['offset-free'],'5.5.2',
 "Given the estimated disturbance d, the target (x_ss, u_ss) that makes output y = c x + d equal the setpoint y_sp solves\n\n    x_ss = (y_sp − d)/c,   u_ss = (1 − a)x_ss/b\n\nImplement `target_ss(a, b, c, d, ysp)` → [x_ss, u_ss].",
 "def target_ss(a, b, c, d, ysp):\n    pass\n",target_ss,
 "def target_ss(a, b, c, d, ysp):\n    xss = (ysp - d)/c\n    return [xss, (1 - a)*xss/b]\n",
 [[0.9,1,1,0.5,3],[0.8,0.5,2,1,4]])

C('ch05','ch05-detect',"Scalar Detectability",'Easy','is_detectable_scalar',['detectability'],'5.6',
 "A scalar mode is detectable if it is stable (|a| < 1) or seen at the output (c ≠ 0).\n\nImplement `is_detectable_scalar(a, c)` → bool.",
 "def is_detectable_scalar(a, c):\n    pass\n",is_detectable_scalar,
 "def is_detectable_scalar(a, c):\n    return abs(a) < 1 or abs(c) > 1e-9\n",
 [[0.5,0],[1.5,1],[1.2,0]])

# ------------------------------------------------------------------ Ch6
C('ch06','ch06-jacobi',"One Jacobi Iteration",'Hard','jacobi_step',['iteration'],'6.2',
 "Distributed solvers iterate locally. The Jacobi update for A x = b holds every other component fixed:\n\n    xᵢ⁺ = (bᵢ − Σⱼ≠ᵢ Aᵢⱼ xⱼ)/Aᵢᵢ\n\nImplement `jacobi_step(A, b, x)` (new full vector).",
 "def jacobi_step(A, b, x):\n    pass\n",jacobi_step,
 "def jacobi_step(A, b, x):\n    n = len(b)\n    return [(b[i] - sum(A[i][j]*x[j]\n            for j in range(n) if j != i))/A[i][i]\n            for i in range(n)]\n",
 [[[[2,1],[1,3]],[3,5],[0,0]],[[[4,1],[2,5]],[1,2],[1,1]]])

C('ch06','ch06-gs',"Gauss-Seidel Iteration",'Hard','gauss_seidel_step',['iteration'],'6.2',
 "Gauss-Seidel is like Jacobi but reuses components already updated this sweep (in index order).\n\nImplement `gauss_seidel_step(A, b, x)` returning the swept vector.",
 "def gauss_seidel_step(A, b, x):\n    pass\n",gauss_seidel_step,
 "def gauss_seidel_step(A, b, x):\n    xn = list(x); n = len(b)\n    for i in range(n):\n        xn[i] = (b[i] - sum(A[i][j]*xn[j]\n                for j in range(n) if j != i))/A[i][i]\n    return xn\n",
 [[[[2,1],[1,3]],[3,5],[0,0]],[[[4,1],[2,5]],[1,2],[1,1]]])

C('ch06','ch06-convex',"Cooperative Convex Combination",'Medium','convex_combine',['cooperative'],'6.3',
 "Cooperative MPC updates plans by a convex step between the old and candidate plan:\n\n    x = (1 − w)·x_old + w·x_new   (elementwise, 0 ≤ w ≤ 1)\n\nImplement `convex_combine(xold, xnew, w)`.",
 "def convex_combine(xold, xnew, w):\n    pass\n",convex_combine,
 "def convex_combine(xold, xnew, w):\n    return [(1 - w)*xold[i] + w*xnew[i]\n            for i in range(len(xold))]\n",
 [[[0,0],[2,4],0.5],[[1,1,1],[3,3,3],0.25]])

C('ch06','ch06-coop',"Cooperative (Weighted) Cost",'Easy','cooperative_cost',['cooperative'],'6.3',
 "A cooperative controller optimizes a weighted sum of local costs J = Σᵢ wᵢ Jᵢ.\n\nImplement `cooperative_cost(costs, weights)`.",
 "def cooperative_cost(costs, weights):\n    pass\n",cooperative_cost,
 "def cooperative_cost(costs, weights):\n    return sum(costs[i]*weights[i]\n              for i in range(len(costs)))\n",
 [[[1,2,3],[0.5,0.5,1]],[[4,4],[0.25,0.75]]])

C('ch06','ch06-consensus',"Consensus Averaging Step",'Medium','consensus_step',['consensus'],'6.4',
 "Subsystem i moves toward the average of itself and its neighbors:\n\n    vᵢ⁺ = mean(vᵢ, {vⱼ : j ∈ neighbors})\n\nImplement `consensus_step(vals, i, neighbors)`.",
 "def consensus_step(vals, i, neighbors):\n    pass\n",consensus_step,
 "def consensus_step(vals, i, neighbors):\n    grp = [vals[i]] + [vals[j] for j in neighbors]\n    return sum(grp)/len(grp)\n",
 [[[1,2,3,4],0,[1,2]],[[10,0,0],1,[0]]])

C('ch06','ch06-avg',"M-Player Average",'Easy','player_average',['cooperative'],'6.4',
 "A simple cooperative target is the mean of all players' proposals.\n\nImplement `player_average(vals)`.",
 "def player_average(vals):\n    pass\n",player_average,
 "def player_average(vals):\n    return sum(vals)/len(vals)\n",
 [[[1,2,3]],[[4,4,4,4]]])

C('ch06','ch06-couple',"Coupled Subsystem Dynamics",'Medium','coupled_dynamics',['coupling'],'6.5',
 "Interconnected subsystems couple through A: (Ax)ᵢ = Σⱼ Aᵢⱼ xⱼ.\n\nImplement `coupled_dynamics(A, x)` (matrix-vector product).",
 "def coupled_dynamics(A, x):\n    pass\n",coupled_dynamics,
 "def coupled_dynamics(A, x):\n    n = len(x)\n    return [sum(A[i][j]*x[j] for j in range(n))\n            for i in range(n)]\n",
 [[[[1,0.1],[0.2,1]],[1,2]],[[[0.9,0],[0.1,0.8]],[2,-1]]])

C('ch06','ch06-conv',"Convergence Check (∞-norm)",'Easy','max_diff',['convergence'],'6.5',
 "Distributed iterations stop when max|aᵢ − bᵢ| falls below a tolerance.\n\nImplement `max_diff(a, b)`.",
 "def max_diff(a, b):\n    pass\n",max_diff,
 "def max_diff(a, b):\n    return max(abs(a[i]-b[i]) for i in range(len(a)))\n",
 [[[1,2,3],[1,2,3]],[[0,0],[0.1,-0.2]]])

# ------------------------------------------------------------------ Ch7
C('ch07','ch07-findregion',"Which Critical Region?",'Medium','find_region',['parametric'],'7.2',
 "Explicit MPC partitions the state into regions. Given ordered bounds [lo, hi), return the index of the region containing x, or −1.\n\nImplement `find_region(bounds, x)`.",
 "def find_region(bounds, x):\n    pass\n",find_region,
 "def find_region(bounds, x):\n    for i, (lo, hi) in enumerate(bounds):\n        if lo <= x < hi:\n            return i\n    return -1\n",
 [[[[-10,0],[0,10]],3],[[[-10,0],[0,10]],-5],[[[-1,1],[1,3]],5]])

C('ch07','ch07-qp',"Scalar QP with Bounds",'Medium','qp_scalar',['parametric-qp'],'7.3',
 "The parametric QP min ½ q u² + c u s.t. u_min ≤ u ≤ u_max has unconstrained optimum u* = −c/q, then clipped to the bounds (q > 0).\n\nImplement `qp_scalar(q, c, umin, umax)`.",
 "def qp_scalar(q, c, umin, umax):\n    pass\n",qp_scalar,
 "def qp_scalar(q, c, umin, umax):\n    u = -c/q\n    return max(umin, min(umax, u))\n",
 [[2,-4,-1,1],[1,1,-5,5],[1,-10,-2,2]])

C('ch07','ch07-explicit',"Explicit LQR with Saturation",'Easy','explicit_lqr',['constrained-lq'],'7.4',
 "Inside the unconstrained region the explicit law is u = −Kx, then clipped to the input limits.\n\nImplement `explicit_lqr(k, x, umin, umax)`.",
 "def explicit_lqr(k, x, umin, umax):\n    pass\n",explicit_lqr,
 "def explicit_lqr(k, x, umin, umax):\n    u = -k*x\n    return max(umin, min(umax, u))\n",
 [[0.5,2,-1,1],[2,3,-1,1],[1,-0.5,-1,1]])

C('ch07','ch07-pwa',"Evaluate a PWA Control Law",'Medium','eval_pwa',['pwa'],'7.5',
 "The explicit solution is piecewise affine. Each region is (lo, hi, gain, offset); on lo ≤ x < hi, u = gain·x + offset.\n\nImplement `eval_pwa(regions, x)`.",
 "def eval_pwa(regions, x):\n    pass\n",eval_pwa,
 "def eval_pwa(regions, x):\n    for lo, hi, gain, off in regions:\n        if lo <= x < hi:\n            return gain*x + off\n    return None\n",
 [[[[-10,0,1,0],[0,10,-2,1]],3],[[[-10,0,1,0],[0,10,-2,1]],-4]])

C('ch07','ch07-pwq',"Piecewise-Quadratic Value Function",'Medium','eval_pwq',['pwq'],'7.5',
 "The optimal value function is piecewise quadratic. Each region is (lo, hi, a, b, c); on lo ≤ x < hi, V = a x² + b x + c.\n\nImplement `eval_pwq(regions, x)`.",
 "def eval_pwq(regions, x):\n    pass\n",eval_pwq,
 "def eval_pwq(regions, x):\n    for lo, hi, a, b, c in regions:\n        if lo <= x < hi:\n            return a*x*x + b*x + c\n    return None\n",
 [[[[-10,0,1,0,0],[0,10,2,0,1]],3],[[[-10,0,1,0,0],[0,10,2,0,1]],-2]])

C('ch07','ch07-region',"Point in a Polyhedral Region",'Medium','in_region',['polyhedra'],'7.7',
 "Each critical region is {x : H x ≤ g}. x lies in it iff every row satisfies Hᵢ·x ≤ gᵢ.\n\nImplement `in_region(H, g, x)` → bool.",
 "def in_region(H, g, x):\n    pass\n",in_region,
 "def in_region(H, g, x):\n    return all(sum(H[i][j]*x[j] for j in range(len(x)))\n              <= g[i] + 1e-9 for i in range(len(g)))\n",
 [[[[1,0],[-1,0],[0,1],[0,-1]],[1,1,1,1],[0.5,0.5]],
  [[[1,0],[-1,0],[0,1],[0,-1]],[1,1,1,1],[2,0]]])

C('ch07','ch07-sat',"Saturate the Explicit Control",'Easy','saturate',['constraints'],'7.8',
 "The explicit law must respect input limits: clamp u into [umin, umax].\n\nImplement `saturate(u, umin, umax)`.",
 "def saturate(u, umin, umax):\n    pass\n",saturate,
 "def saturate(u, umin, umax):\n    return max(umin, min(umax, u))\n",
 [[5,-1,1],[-3,-1,1],[0.5,-1,1]])

# ------------------------------------------------------------------ Ch8
C('ch08','ch08-euler',"Explicit Euler Step",'Medium','euler_step',['integration','shooting'],'8.2.1',
 "Direct methods discretize the dynamics. For ẋ = a x + b u the explicit-Euler step over dt is\n\n    x⁺ = x + dt·(a x + b u)\n\nImplement `euler_step(x, u, a, b, dt)`.",
 "def euler_step(x, u, a, b, dt):\n    pass\n",euler_step,
 "def euler_step(x, u, a, b, dt):\n    return x + dt*(a*x + b*u)\n",
 [[1,0,-1,1,0.1],[2,1,0,1,0.5],[1,-1,0.5,2,0.2]])

C('ch08','ch08-rk2',"Midpoint (RK2) Step",'Medium','rk2_step',['integration'],'8.2.1',
 "The explicit midpoint method for ẋ = a·x is\n\n    k₁ = a·x,   x⁺ = x + dt·a·(x + dt/2·k₁)\n\nImplement `rk2_step(x, a, dt)`.",
 "def rk2_step(x, a, dt):\n    pass\n",rk2_step,
 "def rk2_step(x, a, dt):\n    k1 = a*x\n    return x + dt*a*(x + dt/2*k1)\n",
 [[1,-1,0.1],[1,1,0.5],[2,-0.5,0.2]])

C('ch08','ch08-rk4',"Runge-Kutta 4 Step",'Hard','rk4_step',['integration'],'8.2.1',
 "RK4 for ẋ = a·x over dt:\n\n    k₁=f(x), k₂=f(x+dt/2·k₁), k₃=f(x+dt/2·k₂), k₄=f(x+dt·k₃)\n    x⁺ = x + dt/6·(k₁ + 2k₂ + 2k₃ + k₄),   f(s)=a·s\n\nImplement `rk4_step(x, a, dt)`.",
 "def rk4_step(x, a, dt):\n    pass\n",rk4_step,
 "def rk4_step(x, a, dt):\n    f = lambda s: a*s\n    k1 = f(x)\n    k2 = f(x + dt/2*k1)\n    k3 = f(x + dt/2*k2)\n    k4 = f(x + dt*k3)\n    return x + dt/6*(k1 + 2*k2 + 2*k3 + k4)\n",
 [[1,-1,0.1],[1,1,0.5],[2,-0.5,0.2]])

C('ch08','ch08-implicit',"Implicit Euler Step (Stiff)",'Medium','implicit_euler',['integration','stiff'],'8.2.2',
 "For stiff systems the implicit (backward) Euler step for ẋ = a·x solves x⁺ = x + dt·a·x⁺, i.e.\n\n    x⁺ = x / (1 − dt·a)\n\nImplement `implicit_euler(x, a, dt)`.",
 "def implicit_euler(x, a, dt):\n    pass\n",implicit_euler,
 "def implicit_euler(x, a, dt):\n    return x/(1 - dt*a)\n",
 [[1,-10,0.1],[1,-1,0.5],[2,-100,0.01]])

C('ch08','ch08-newton',"Newton Step",'Easy','newton_step',['newton'],'8.3',
 "Newton's method for solving f(x) = 0 (the optimality conditions) updates x⁺ = x − f(x)/f′(x).\n\nImplement `newton_step(x, fx, dfx)`.",
 "def newton_step(x, fx, dfx):\n    pass\n",newton_step,
 "def newton_step(x, fx, dfx):\n    return x - fx/dfx\n",
 [[2,1,4],[1,-2,2],[0,3,1]])

C('ch08','ch08-newtsqrt',"Newton Iteration for √s",'Medium','newton_sqrt',['newton'],'8.3',
 "Applying Newton's method to x² − s = 0 gives the iteration x ← ½(x + s/x). Run it n times from x₀ = s.\n\nImplement `newton_sqrt(s, n)`.",
 "def newton_sqrt(s, n):\n    pass\n",newton_sqrt,
 "def newton_sqrt(s, n):\n    x = s if s > 0 else 1.0\n    for _ in range(n):\n        x = 0.5*(x + s/x)\n    return x\n",
 [[2,5],[9,10],[100,15]])

C('ch08','ch08-fdiff',"Forward Finite Difference",'Easy','forward_diff',['derivatives'],'8.4.1',
 "A one-sided derivative estimate is f′(x) ≈ (f(x+dx) − f(x))/dx.\n\nGiven f0 = f(x), f1 = f(x+dx), implement `forward_diff(f0, f1, dx)`.",
 "def forward_diff(f0, f1, dx):\n    pass\n",forward_diff,
 "def forward_diff(f0, f1, dx):\n    return (f1 - f0)/dx\n",
 [[1,3,1],[2,2,0.5],[0,1,0.1]])

C('ch08','ch08-cdiff',"Central Finite Difference",'Easy','central_diff',['derivatives'],'8.4.1',
 "The more accurate central difference is f′(x) ≈ (f(x+dx) − f(x−dx))/(2dx).\n\nGiven fm = f(x−dx), fp = f(x+dx), implement `central_diff(fm, fp, dx)`.",
 "def central_diff(fm, fp, dx):\n    pass\n",central_diff,
 "def central_diff(fm, fp, dx):\n    return (fp - fm)/(2*dx)\n",
 [[1,3,1],[4,4,0.5],[0,2,0.1]])

C('ch08','ch08-shooting',"Single-Shooting Rollout",'Hard','single_shooting',['shooting'],'8.5.1',
 "Sequential (single-shooting) methods simulate the whole trajectory from x0 and an input sequence (explicit Euler on ẋ = a x + b u), then optimize. Return the final state.\n\nImplement `single_shooting(x0, us, a, b, dt)`.",
 "def single_shooting(x0, us, a, b, dt):\n    pass\n",single_shooting,
 "def single_shooting(x0, us, a, b, dt):\n    x = x0\n    for u in us:\n        x = x + dt*(a*x + b*u)\n    return x\n",
 [[1,[0,0,0],-1,1,0.1],[0,[1,1,1],0,1,0.5],[2,[-1,0,1],0.5,2,0.2]])

C('ch08','ch08-defect',"Multiple-Shooting Defect",'Easy','defect',['shooting'],'8.5.2',
 "Multiple shooting enforces continuity between segments by driving the defect to zero: the gap between the previous segment's end state and the next segment's start state.\n\nImplement `defect(xa, xb)` = xa − xb.",
 "def defect(xa, xb):\n    pass\n",defect,
 "def defect(xa, xb):\n    return xa - xb\n",
 [[1.2,1.0],[3,3],[0.5,0.8]])

C('ch08','ch08-gn',"Gauss-Newton Normal Matrix",'Medium','normal_matrix',['sqp'],'8.6.3',
 "The Gauss-Newton Hessian approximation is JᵀJ. For a gradient vector J (one residual), the normal matrix entry (i,j) is Jᵢ·Jⱼ.\n\nImplement `normal_matrix(J)` returning the n×n outer product.",
 "def normal_matrix(J):\n    pass\n",normal_matrix,
 "def normal_matrix(J):\n    return [[J[i]*J[j] for j in range(len(J))]\n            for i in range(len(J))]\n",
 [[[1,2]],[[3,0,1]]])

# ============================ emit ============================
def jnorm(x):
    if isinstance(x, bool): return x
    if isinstance(x, float): return round(x, 9)
    if isinstance(x, (list, tuple)): return [jnorm(i) for i in x]
    return x

out = {}
for chap, items in CH.items():
    arr = []
    for it in items:
        tests = [{'args': a, 'expected': jnorm(it['sol'](*a))} for a in it['args']]
        rec = {k: it[k] for k in ('id','title','difficulty','func','tags','section','prompt','starter')}
        rec['solution'] = it['ref']
        rec['tests'] = tests
        arr.append(rec)
    out[chap] = arr

here = os.path.dirname(os.path.abspath(__file__))
dest = os.path.join(here, '..', 'src', 'lib', 'data', 'challenges.json')
with open(dest, 'w') as f: json.dump(out, f, indent=2)
print(f"wrote {sum(len(v) for v in out.values())} challenges across {len(out)} chapters")
