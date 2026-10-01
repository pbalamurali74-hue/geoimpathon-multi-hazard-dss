"""Multi-Criteria Decision Making (MCDM) methods for multi-hazard susceptibility.

Includes:
- Analytic Hierarchy Process (AHP) with exact eigenvector solver and CR assertion (< 0.10)
- Objective Shannon Entropy Weight Method (EWM)
- Directional Min-Max normalization with robust percentile clipping
- Non-linear Fuzzy Sigmoidal Membership function
- Spearman rank correlation cross-check between AHP and Entropy risk maps
"""

import logging
from typing import Tuple, Dict, List, Optional
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

# Saaty Random Index (RI) table for matrix order n = 1 to 10
SAATY_RI: Dict[int, float] = {
    1: 0.0,
    2: 0.0,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
}


def calculate_ahp_weights(
    matrix: np.ndarray,
    criterion_names: Optional[List[str]] = None,
) -> Tuple[np.ndarray, float, float, float]:
    """Calculate criterion priority weights via the exact principal eigenvector of an AHP matrix.

    Args:
        matrix: Reciprocal pairwise comparison square matrix (n x n)
        criterion_names: Optional list of names for logging

    Returns:
        (weights: np.ndarray, lambda_max: float, ci: float, cr: float)

    Raises:
        AssertionError: if matrix is not reciprocal or if CR >= 0.10
    """
    n = matrix.shape[0]
    assert matrix.shape[0] == matrix.shape[1], "AHP matrix must be square"

    # Verify reciprocity: a_ij * a_ji == 1.0 within numerical precision
    for i in range(n):
        for j in range(n):
            assert np.isclose(matrix[i, j] * matrix[j, i], 1.0, atol=1e-3), (
                f"Reciprocity violated at ({i},{j}): {matrix[i, j]} * {matrix[j, i]} != 1.0"
            )

    # Compute eigenvalues and eigenvectors
    eigvals, eigvecs = np.linalg.eig(matrix)
    max_idx = int(np.argmax(np.real(eigvals)))
    lambda_max = float(np.real(eigvals[max_idx]))

    # Principal eigenvector normalized to sum to 1.0
    w = np.real(eigvecs[:, max_idx])
    w = w / np.sum(w)
    # Ensure positive weights
    w = np.abs(w) / np.sum(np.abs(w))

    # Consistency Index (CI) and Consistency Ratio (CR)
    if n <= 2:
        ci = 0.0
        cr = 0.0
    else:
        ci = (lambda_max - n) / (n - 1)
        ri = SAATY_RI.get(n, 1.49)
        cr = ci / ri

    logger.info("AHP lambda_max=%.4f, CI=%.4f, CR=%.4f", lambda_max, ci, cr)
    if criterion_names and len(criterion_names) == n:
        for name, weight in zip(criterion_names, w):
            logger.info("  %s: weight = %.4f (%.1f%%)", name, weight, weight * 100)

    # Enforce strict academic consistency threshold
    assert cr < 0.10, f"AHP Consistency Ratio {cr:.4f} exceeds strict threshold 0.10!"

    return w, lambda_max, ci, cr


def normalize_minmax(
    arr: np.ndarray,
    cost_direction: bool = True,
    p_low: float = 1.0,
    p_high: float = 99.0,
) -> np.ndarray:
    """Normalize a continuous array to [0, 1] using robust percentile clipping.

    Args:
        arr: 2D or 1D continuous indicator array
        cost_direction: True if higher physical value = higher hazard/risk.
                       False if higher physical value = lower hazard/risk (benefit).
        p_low: Lower percentile for outlier clamping (default 1st percentile)
        p_high: Upper percentile for outlier clamping (default 99th percentile)

    Returns:
        Normalized array bounded to [0.0, 1.0]
    """
    valid_mask = ~np.isnan(arr)
    if not np.any(valid_mask):
        return np.zeros_like(arr, dtype=np.float32)

    val_min = float(np.percentile(arr[valid_mask], p_low))
    val_max = float(np.percentile(arr[valid_mask], p_high))

    if np.isclose(val_max, val_min, atol=1e-7):
        logger.warning("Zero variance detected during normalization; returning zero array.")
        out = np.zeros_like(arr, dtype=np.float32)
        out[~valid_mask] = np.nan
        return out

    # Clamp outliers
    clipped = np.clip(arr, val_min, val_max)

    if cost_direction:
        # Direct risk scaling: min -> 0, max -> 1
        normalized = (clipped - val_min) / (val_max - val_min)
    else:
        # Inverse risk scaling (benefit): max -> 0, min -> 1
        normalized = (val_max - clipped) / (val_max - val_min)

    normalized[~valid_mask] = np.nan
    return normalized.astype(np.float32)


def fuzzy_sigmoidal_membership(
    arr: np.ndarray,
    midpoint: float,
    beta: float = 1.0,
    decreasing: bool = True,
) -> np.ndarray:
    """Non-linear fuzzy sigmoidal membership transformation for continuous risk.

    Args:
        arr: Input physical array (e.g. HAND or elevation in meters)
        midpoint: Inflection point where risk membership equals 0.50
        beta: Slope steepness parameter
        decreasing: True if higher value decreases risk (e.g. elevation/HAND)

    Returns:
        Fuzzy membership array bounded to [0.0, 1.0]
    """
    valid_mask = ~np.isnan(arr)
    out = np.zeros_like(arr, dtype=np.float32)

    sign = 1.0 if decreasing else -1.0
    # Sigmoidal formula: mu = 1 / (1 + exp(sign * beta * (x - midpoint)))
    exponent = np.clip(sign * beta * (arr - midpoint), -50.0, 50.0)
    mu = 1.0 / (1.0 + np.exp(exponent))
    out[valid_mask] = mu[valid_mask]
    out[~valid_mask] = np.nan
    return out.astype(np.float32)


def calculate_entropy_weights(indicators_stack: np.ndarray) -> np.ndarray:
    """Calculate objective criterion weights using Shannon Information Entropy.

    Args:
        indicators_stack: 3D array of shape (k, rows, cols) or 2D array of (k, n_pixels),
                         where k is the number of normalized indicators in [0, 1].

    Returns:
        1D array of weights summing to 1.0
    """
    if indicators_stack.ndim == 3:
        k, r, c = indicators_stack.shape
        flat = indicators_stack.reshape(k, r * c)
    else:
        k, _ = indicators_stack.shape
        flat = indicators_stack.copy()

    # Remove columns with NaNs
    valid_cols = ~np.any(np.isnan(flat), axis=0)
    data = flat[:, valid_cols]
    m = data.shape[1]  # number of evaluation pixels

    if m == 0:
        return np.ones(k, dtype=np.float32) / k

    # Add epsilon to prevent log(0)
    data = np.maximum(data, 1e-12)

    # Probability matrix: p_ij = r_ij / sum_i(r_ij)
    col_sums = np.sum(data, axis=1, keepdims=True)
    col_sums = np.maximum(col_sums, 1e-12)
    p = data / col_sums

    # Information entropy: e_j = -k * sum(p_ij * ln(p_ij)) where k = 1 / ln(m)
    ln_m = np.log(m)
    k_const = 1.0 / ln_m if ln_m > 0 else 1.0
    entropy = -k_const * np.sum(p * np.log(p), axis=1)

    # Information dispersion / utility: d_j = 1 - e_j
    dispersion = np.maximum(1.0 - entropy, 1e-6)

    # Objective weights
    weights = dispersion / np.sum(dispersion)
    return weights.astype(np.float32)


def compare_ahp_and_entropy_maps(
    map_ahp: np.ndarray,
    map_entropy: np.ndarray,
    sample_size: int = 10000,
) -> Tuple[float, float]:
    """Compute Spearman rank correlation between AHP and Entropy risk maps.

    Returns:
        (rho: float, p_value: float)
    """
    valid = (~np.isnan(map_ahp)) & (~np.isnan(map_entropy))
    v1 = map_ahp[valid].ravel()
    v2 = map_entropy[valid].ravel()

    if len(v1) > sample_size:
        idx = np.random.choice(len(v1), size=sample_size, replace=False)
        v1, v2 = v1[idx], v2[idx]

    rho, pval = stats.spearmanr(v1, v2)
    logger.info("Spearman correlation between AHP and Entropy risk: rho=%.4f (p=%.2e)", rho, pval)
    return float(rho), float(pval)
