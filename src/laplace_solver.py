"""
ICS2 Week 6 - 2D Laplace Equation Solver for Thin Film Electrolyte

Solves:  div(kappa * grad(phi)) = 0  in 2D
with nonlinear Butler-Volmer boundary conditions at metal surfaces
and zero-flux conditions at insulator boundaries.

Numerical method: Finite difference on the 5-point stencil, with the nonlinear
Butler-Volmer boundary rows solved by step-limited Newton on the whole grid.

Domain: USB-C receptacle cross-section (8.34 mm x 2.56 mm).
"""

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
from .config import (NX, NY, DX, DY, METALS, ELECTROLYTE,
                     SIM_PARAMS, T_DEFAULT, F_CONST, R_GAS)
from .butler_volmer import butler_volmer_current, butler_volmer_derivative, effective_j0
from .config import build_metal_zone_map

NEWTON_MAX_STEP = 0.1  # Largest potential change per Newton iteration [V]


def solve_laplace_2d(zone_map=None, kappa=None, phi_metals=None,
                     R_oxides=None, T=T_DEFAULT, j0_overrides=None,
                     charging_bias=0.0, tol=None, max_iter=None):
    """
    Solve 2D Laplace equation in the electrolyte domain with
    Butler-Volmer boundary conditions.

    Parameters
    ----------
    zone_map : ndarray of str, shape (NY, NX)
        Material zone labels. If None, builds default.
    kappa : float
        Electrolyte conductivity [S/m]. If None, uses default.
    phi_metals : dict
        Fixed metal potentials {metal_key: potential_V}. If None, uses E_eq.
    R_oxides : dict
        Oxide film resistances {metal_key: R_Ohm_m2}. If None, uses initial.
    T : float
        Temperature [K].
    j0_overrides : dict
        Override exchange current densities {metal_key: j0_value}.
    charging_bias : float
        Additional voltage applied to Au contact pins during charging [V].
    tol : float
        Convergence tolerance: largest full Newton step [V].
    max_iter : int
        Maximum Newton iterations.

    Returns
    -------
    phi : ndarray, shape (NY, NX)
        Electrolyte potential field [V].
    j_field : ndarray, shape (NY, NX)
        Current density magnitude at each point [A/m^2].
    converged : bool
        True only if a full Newton step fell below tol.
    n_iter : int
        Number of Newton iterations.
    """
    if zone_map is None:
        zone_map = build_metal_zone_map()
    if kappa is None:
        kappa = ELECTROLYTE["conductivity"]
    if phi_metals is None:
        phi_metals = {k: METALS[k]["E_eq"] for k in METALS}
    if R_oxides is None:
        R_oxides = {k: METALS[k]["R_oxide_0"] for k in METALS}
    if j0_overrides is None:
        j0_overrides = {}
    if tol is None:
        tol = SIM_PARAMS["laplace_tol"]
    if max_iter is None:
        max_iter = SIM_PARAMS["laplace_max_iter"]

    # Apply charging bias to Au pins
    if charging_bias != 0.0:
        phi_metals = dict(phi_metals)
        phi_metals["Au"] = phi_metals.get("Au", METALS["Au"]["E_eq"]) + charging_bias

    # Each boundary cell closes against the mean of its electrolyte neighbours.
    # Insulator cell:  phi_b - phi_e = 0                         (zero flux)
    # Metal cell:      kappa * (phi_s - phi_e) / dn = j_BV(eta)  (anodic j > 0
    #                  leaves the metal, so phi falls away from the surface)
    is_electrolyte = (zone_map == "electrolyte")
    dn = min(DX, DY)
    cx, cy = 1.0 / (DX * DX), 1.0 / (DY * DY)
    n_cells = NY * NX
    rows, cols, vals = [], [], []
    rhs = np.zeros(n_cells)
    phi = np.full(n_cells, np.mean(list(phi_metals.values())))
    bv_cells, bv_phi_m, bv_E, bv_j0, bv_aa, bv_ac = [], [], [], [], [], []

    for r in range(NY):
        for c in range(NX):
            k = r * NX + c
            zone = zone_map[r, c]
            neighbours = [(r + dr, c + dc, w) for dr, dc, w in
                          ((-1, 0, cy), (1, 0, cy), (0, -1, cx), (0, 1, cx))
                          if 0 <= r + dr < NY and 0 <= c + dc < NX]

            if zone == "electrolyte":
                for nr, nc, w in neighbours:
                    rows += [k, k]
                    cols += [nr * NX + nc, k]
                    vals += [w, -w]
                continue

            wet = [nr * NX + nc for nr, nc, _ in neighbours if is_electrolyte[nr, nc]]
            if zone in METALS:
                metal = METALS[zone]
                phi_m = phi_metals.get(zone, metal["E_eq"])
                phi[k] = phi_m
            if not wet:
                rows.append(k)
                cols.append(k)
                vals.append(1.0)
                rhs[k] = phi[k]
                continue

            g = kappa / dn
            rows.append(k)
            cols.append(k)
            vals.append(g)
            for m in wet:
                rows.append(k)
                cols.append(m)
                vals.append(-g / len(wet))
            if zone in METALS:
                bv_cells.append(k)
                bv_phi_m.append(phi_m)
                bv_E.append(metal["E_eq"])
                bv_j0.append(effective_j0(j0_overrides.get(zone, metal["j0"]),
                                          R_oxides.get(zone, metal["R_oxide_0"]), T))
                bv_aa.append(metal["alpha_a"])
                bv_ac.append(metal["alpha_c"])

    A = sparse.csc_matrix((vals, (rows, cols)), shape=(n_cells, n_cells))
    bv_cells = np.array(bv_cells, dtype=int)
    eta_0 = np.array(bv_phi_m) - np.array(bv_E)
    bv_j0, bv_aa, bv_ac = np.array(bv_j0), np.array(bv_aa), np.array(bv_ac)

    # Newton on the whole grid. The problem is monotone, so one solution exists;
    # the step limit keeps the exponentials in range. Converged means a full,
    # undamped Newton step smaller than tol.
    converged = False
    n_iter = 0
    for n_iter in range(1, max_iter + 1):
        eta = eta_0 - phi[bv_cells]
        residual = A @ phi - rhs
        residual[bv_cells] -= butler_volmer_current(eta, bv_j0, bv_aa, bv_ac, T)
        slope = np.zeros(n_cells)
        slope[bv_cells] = butler_volmer_derivative(eta, bv_j0, bv_aa, bv_ac, T)
        step = spsolve((A + sparse.diags(slope, format="csc")).tocsc(), -residual)
        size = np.max(np.abs(step))
        phi += step * min(1.0, NEWTON_MAX_STEP / size) if size > 0 else 0.0
        if size < tol:
            converged = True
            break

    phi = phi.reshape(NY, NX)

    # Compute current density field from potential gradient
    j_field = np.zeros((NY, NX))
    for j_idx in range(1, NY - 1):
        for i_idx in range(1, NX - 1):
            if is_electrolyte[j_idx, i_idx]:
                dphidx = (phi[j_idx, i_idx + 1] - phi[j_idx, i_idx - 1]) / (2.0 * DX)
                dphidy = (phi[j_idx + 1, i_idx] - phi[j_idx - 1, i_idx]) / (2.0 * DY)
                j_field[j_idx, i_idx] = kappa * np.sqrt(dphidx**2 + dphidy**2)

    return phi, j_field, converged, n_iter


def extract_boundary_currents(phi, zone_map, kappa=None, R_oxides=None,
                              T=T_DEFAULT, j0_overrides=None):
    """
    Extract current density at each metal boundary from the solved potential field.

    Returns
    -------
    boundary_currents : dict
        {metal_key: {'total_current': float, 'avg_j': float, 'max_j': float,
                     'area': float, 'j_values': list}}
    """
    if kappa is None:
        kappa = ELECTROLYTE["conductivity"]
    if zone_map is None:
        zone_map = build_metal_zone_map()
    if R_oxides is None:
        R_oxides = {k: METALS[k]["R_oxide_0"] for k in METALS}
    if j0_overrides is None:
        j0_overrides = {}

    is_electrolyte = (zone_map == "electrolyte")
    boundary_currents = {}
    cell_area = DX * DY

    for mk in METALS:
        mask = (zone_map == mk)
        if not np.any(mask):
            boundary_currents[mk] = {
                "total_current": 0.0, "avg_j": 0.0, "max_j": 0.0,
                "area": 0.0, "j_values": []
            }
            continue

        metal = METALS[mk]
        j0 = j0_overrides.get(mk, metal["j0"])
        j0_eff = effective_j0(j0, R_oxides.get(mk, metal["R_oxide_0"]), T)

        rows, cols = np.where(mask)
        j_values = []

        for r, c in zip(rows, cols):
            # Normal flux from adjacent electrolyte cell
            neighbors_phi = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < NY and 0 <= nc < NX:
                    if is_electrolyte[nr, nc]:
                        neighbors_phi.append(phi[nr, nc])

            if len(neighbors_phi) > 0:
                phi_elec = np.mean(neighbors_phi)
                # j = -kappa * grad(phi) dot n, n pointing into the electrolyte;
                # positive = anodic, matching butler_volmer_current
                dn = min(DX, DY)
                j_local = kappa * (phi[r, c] - phi_elec) / dn
                j_values.append(j_local)

        j_values = np.array(j_values) if len(j_values) > 0 else np.array([0.0])
        total_area = len(rows) * cell_area

        boundary_currents[mk] = {
            "total_current": np.sum(j_values) * cell_area,
            "avg_j": np.mean(j_values),
            "max_j": np.max(np.abs(j_values)),
            "area": total_area,
            "j_values": j_values.tolist(),
        }

    return boundary_currents
