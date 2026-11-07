"""Small, dependency-free statistics helpers for the sealed synthetic studies.

These functions describe the recorded simulation draws; they do not turn synthetic studies into
physical qualification. Agent-written for the owner's hobby/learning project.
"""
import math
import random


def wilson(successes, n, z=1.96):
    """Wilson score interval, clamped to [0, 1]; None when there are no observations."""
    if n < 0 or not 0 <= successes <= n or z <= 0:
        raise ValueError("require 0 <= successes <= n and z > 0")
    if n == 0:
        return None
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [round(max(0.0, center - half), 4), round(min(1.0, center + half), 4)]


def midranks(values):
    """Zero-based average ranks, assigning every tied value the same rank."""
    values = list(values)
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        rank = (start + end - 1) / 2.0
        for pos in range(start, end):
            out[order[pos]] = rank
        start = end
    return out


def spearman(xs, ys):
    """Spearman correlation using midranks; None for mismatched/constant input."""
    xs, ys = list(xs), list(ys)
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    rx, ry = midranks(xs), midranks(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    sxx = sum((x - mx) ** 2 for x in rx)
    syy = sum((y - my) ** 2 for y in ry)
    if sxx == 0 or syy == 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(rx, ry))
    return sxy / math.sqrt(sxx * syy)


def quantile(values, q):
    """Linear-interpolated quantile of a finite sample (the usual type-7 definition)."""
    if not 0 <= q <= 1:
        raise ValueError("q must be in [0, 1]")
    values = sorted(values)
    if not values:
        return None
    pos = (len(values) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    fraction = pos - lo
    return values[lo] * (1 - fraction) + values[hi] * fraction


def clustered_permutation_p(xs, ys, corr, clusters, strata, shuffles=10000, seed=7):
    """Two-sided permutation p-value preserving repeated rows within independent clusters.

    Each cluster has one invariant `ys` value and one stratum. Whole cluster values are shuffled only
    among clusters in the same stratum, then expanded back to row level. This keeps, for example, all
    scenario outcomes for one pose/seed paired while permuting that seed's unblocked baseline result.
    """
    xs, ys = list(xs), list(ys)
    clusters, strata = list(clusters), list(strata)
    if corr is None:
        return None
    if not (len(xs) == len(ys) == len(clusters) == len(strata)) or not xs:
        raise ValueError("xs, ys, clusters and strata must have the same non-zero length")
    if not isinstance(shuffles, int) or shuffles < 1:
        raise ValueError("shuffles must be a positive integer")
    grouped = {}
    for x, y, cluster, stratum in zip(xs, ys, clusters, strata):
        if cluster not in grouped:
            grouped[cluster] = {"stratum": stratum, "value": y, "indices": []}
        group = grouped[cluster]
        if group["stratum"] != stratum or group["value"] != y:
            raise ValueError("each cluster needs one stratum and one invariant ys value")
        group["indices"].append(len(group["indices"]))
    by_stratum = {}
    for cluster, group in grouped.items():
        by_stratum.setdefault(group["stratum"], []).append(cluster)
    if any(len(keys) < 2 for keys in by_stratum.values()):
        raise ValueError("each stratum needs at least two clusters for permutation")

    rng = random.Random(seed)
    hits = 0
    for _ in range(shuffles):
        assignment = {}
        for keys in by_stratum.values():
            values = [grouped[key]["value"] for key in keys]
            rng.shuffle(values)
            assignment.update(zip(keys, values))
        permuted = [assignment[cluster] for cluster in clusters]
        candidate = spearman(xs, permuted)
        if candidate is not None and abs(candidate) >= abs(corr) - 1e-12:
            hits += 1
    return (hits + 1) / (shuffles + 1)
