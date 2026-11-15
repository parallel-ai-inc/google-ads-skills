"""The statistics behind the experiments skill. Standard library only.

Every formula here is written out, with its source, in
references/test-math.md. The scripts import this module; it is never run
on its own.
"""
import math
from statistics import NormalDist

NORMAL = NormalDist()


def z_two_sided(confidence):
    """1.96 for 95%: the normal quantile that leaves (1 - confidence) / 2 in each tail."""
    return NORMAL.inv_cdf(1 - (1 - confidence) / 2)


def z_power(power):
    """0.84 for 80% power."""
    return NORMAL.inv_cdf(power)


def t_quantile(p, df):
    """Student t quantile by the Cornish-Fisher expansion (Hill 1970). Good to about 0.01 from 3 degrees of freedom."""
    x = NORMAL.inv_cdf(p)
    if df is None or df < 1:
        return None
    g1 = (x ** 3 + x) / 4
    g2 = (5 * x ** 5 + 16 * x ** 3 + 3 * x) / 96
    g3 = (3 * x ** 7 + 19 * x ** 5 + 17 * x ** 3 - 15 * x) / 384
    g4 = (79 * x ** 9 + 776 * x ** 7 + 1482 * x ** 5 - 1920 * x ** 3 - 945 * x) / 92160
    return x + g1 / df + g2 / df ** 2 + g3 / df ** 3 + g4 / df ** 4


def t_two_sided_p(t, df):
    """Two sided p value for a t statistic (Abramowitz and Stegun 26.7.8)."""
    if t is None or df is None or df < 1:
        return None
    z = abs(t) * (1 - 1 / (4.0 * df)) / math.sqrt(1 + t * t / (2.0 * df))
    return 2 * (1 - NORMAL.cdf(z))


def mean(values):
    return sum(values) / len(values) if values else None


def variance(values):
    """Sample variance, n - 1 in the denominator."""
    if len(values) < 2:
        return None
    m = mean(values)
    return sum((v - m) ** 2 for v in values) / (len(values) - 1)


def _invert(matrix):
    """Gauss-Jordan inverse of a small square matrix, or None when it is singular."""
    n = len(matrix)
    work = [list(row) + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(work[r][col]))
        if abs(work[pivot][col]) < 1e-12:
            return None
        work[col], work[pivot] = work[pivot], work[col]
        lead = work[col][col]
        work[col] = [v / lead for v in work[col]]
        for r in range(n):
            if r != col and work[r][col]:
                factor = work[r][col]
                work[r] = [a - factor * b for a, b in zip(work[r], work[col])]
    return [row[n:] for row in work]


def ols(X, y):
    """Ordinary least squares. X is a list of rows of predictors (include a 1 for the intercept).

    Returns coef, the unscaled covariance (X'X)^-1, sigma2 (residual variance),
    df, residuals and r2, or None when the fit is impossible.
    """
    n, k = len(X), len(X[0]) if X else 0
    if n <= k:
        return None
    xtx = [[sum(X[r][i] * X[r][j] for r in range(n)) for j in range(k)] for i in range(k)]
    inv = _invert(xtx)
    if inv is None:
        return None
    xty = [sum(X[r][i] * y[r] for r in range(n)) for i in range(k)]
    coef = [sum(inv[i][j] * xty[j] for j in range(k)) for i in range(k)]
    fitted = [sum(c * x for c, x in zip(coef, row)) for row in X]
    residuals = [a - b for a, b in zip(y, fitted)]
    sse = sum(r * r for r in residuals)
    my = mean(y)
    sst = sum((v - my) ** 2 for v in y)
    df = n - k
    return {"coef": coef, "inv": inv, "sigma2": sse / df, "df": df, "residuals": residuals,
            "r2": 1 - sse / sst if sst > 0 else None}


def weekday_pattern(days, values, alpha=0.05):
    """One way analysis of daily values by weekday.

    Returns the weekday index (weekday mean / overall mean), the raw and the
    within-weekday variance, the F statistic and its p value (Paulson's normal
    approximation), and whether the pattern is present at the given level.
    Needs at least two days of every weekday.
    """
    groups = {}
    for day, value in zip(days, values):
        groups.setdefault(day.weekday(), []).append(value)
    n = len(values)
    overall = mean(values)
    result = {"days": n, "raw_variance": variance(values), "checked": False, "present": False,
              "index": {}, "within_variance": None, "f": None, "p": None}
    if len(groups) < 7 or min(len(g) for g in groups.values()) < 2 or not overall:
        return result
    ssb = sum(len(g) * (mean(g) - overall) ** 2 for g in groups.values())
    ssw = sum(sum((v - mean(g)) ** 2 for v in g) for g in groups.values())
    d1, d2 = 6, n - 7
    within = ssw / d2
    result.update({"checked": True, "within_variance": within,
                   "index": {wd: mean(groups[wd]) / overall for wd in sorted(groups)}})
    if within <= 0:
        return result
    f = (ssb / d1) / within
    a, b = 2.0 / (9 * d1), 2.0 / (9 * d2)
    zf = ((1 - b) * f ** (1.0 / 3) - (1 - a)) / math.sqrt(b * f ** (2.0 / 3) + a)
    p = 1 - NORMAL.cdf(zf)
    result.update({"f": f, "p": p, "present": p < alpha})
    return result


def tbr(pre_x, pre_y, test_x, test_y, confidence):
    """Time-based regression (Kerman, Wang and Vaver, Google Research 2017).

    Fits test = a + b x control on the pre-period, predicts what the test group
    would have done in the test period, and returns the cumulative effect
    (actual minus predicted) with a t interval from the regression's
    prediction error. None when the fit is impossible.
    """
    fit = ols([[1.0, x] for x in pre_x], pre_y)
    if fit is None:
        return None
    a, b = fit["coef"]
    n, m = len(pre_x), len(test_x)
    predicted = [a + b * x for x in test_x]
    effect = sum(test_y) - sum(predicted)
    xbar = mean(pre_x)
    sxx = sum((x - xbar) ** 2 for x in pre_x)
    var = fit["sigma2"] * (m + m * m / float(n) + ((sum(test_x) - m * xbar) ** 2 / sxx if sxx > 0 else 0))
    se = math.sqrt(var)
    tq = t_quantile(1 - (1 - confidence) / 2, fit["df"])
    base = sum(predicted)
    running, cumulative = 0.0, []
    for actual, pred in zip(test_y, predicted):
        running += actual - pred
        cumulative.append(running)
    return {"intercept": a, "slope": b, "r2": fit["r2"], "residual_sd": math.sqrt(fit["sigma2"]), "df": fit["df"],
            "pre_days": n, "test_days": m, "actual": sum(test_y), "predicted": base, "effect": effect, "se": se,
            "low": effect - tq * se, "high": effect + tq * se, "t_quantile": tq,
            "p": t_two_sided_p(effect / se if se > 0 else None, fit["df"]),
            "relative": effect / base if base else None,
            "relative_low": (effect - tq * se) / base if base else None,
            "relative_high": (effect + tq * se) / base if base else None,
            "daily_predicted": predicted, "cumulative": cumulative}


def ratio_lift(pairs, numerator, denominator, adjust, confidence):
    """Lift of the trial arm over the control arm, from both arms day by day.

    pairs: one (trial_day, control_day) tuple of dicts per day.
    The metric is sum(numerator) / sum(denominator) in each arm, or a plain
    sum when denominator is None; adjust multiplies the ratio (it corrects a
    sum for an uneven split). The log of the ratio of ratios gets its variance
    by the delta method from the days' covariance, so a day both arms shared
    cancels out. Returns lift, low, high, p, or None when it cannot be computed.
    """
    n = len(pairs)
    keys = [("t", numerator), ("c", numerator)]
    if denominator:
        keys += [("t", denominator), ("c", denominator)]
    vectors = [[(t if side == "t" else c).get(key) or 0.0 for side, key in keys] for t, c in pairs]
    sums = [sum(v[i] for v in vectors) for i in range(len(keys))]
    if n < 3 or any(s <= 0 for s in sums):
        return None
    signs = [1, -1, -1, 1][:len(keys)]
    grad = [sign / s for sign, s in zip(signs, sums)]
    log_ratio = sum(sign * math.log(s) for sign, s in zip(signs, sums)) + math.log(adjust)
    means = [s / n for s in sums]
    cov = [[sum((v[i] - means[i]) * (v[j] - means[j]) for v in vectors) / (n - 1) for j in range(len(keys))] for i in range(len(keys))]
    var = n * sum(grad[i] * grad[j] * cov[i][j] for i in range(len(keys)) for j in range(len(keys)))
    if var <= 0:
        return None
    se = math.sqrt(var)
    tq = t_quantile(1 - (1 - confidence) / 2, n - 1)
    return {"lift": math.exp(log_ratio) - 1, "low": math.exp(log_ratio - tq * se) - 1, "high": math.exp(log_ratio + tq * se) - 1,
            "p": t_two_sided_p(log_ratio / se, n - 1), "method": "days paired, delta method on the log ratio", "days": n}


def count_lift(trial, control, adjust, confidence, rate_numerators=None):
    """Lift from arm totals alone, treating counts as Poisson (or binomial for a rate).

    For a plain count: var(log total) = 1 / total in each arm. For a rate with
    numerator x out of n: var(log rate) = (1 - x/n) / x. Returns lift, low,
    high, p, or None.
    """
    if rate_numerators:
        (xt, nt), (xc, nc) = rate_numerators
        if not (xt and xc and nt and nc) or xt > nt or xc > nc:
            return None
        log_ratio = math.log((xt / nt) / (xc / nc))
        var = (1 - xt / nt) / xt + (1 - xc / nc) / xc
    else:
        if not trial or not control or trial <= 0 or control <= 0:
            return None
        log_ratio = math.log(trial / control * adjust)
        var = 1.0 / trial + 1.0 / control
    se = math.sqrt(var)
    z = z_two_sided(confidence)
    return {"lift": math.exp(log_ratio) - 1, "low": math.exp(log_ratio - z * se) - 1, "high": math.exp(log_ratio + z * se) - 1,
            "p": 2 * (1 - NORMAL.cdf(abs(log_ratio / se))), "method": "arm totals, counts treated as Poisson"}
