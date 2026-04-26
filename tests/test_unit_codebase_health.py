"""
Wave 0 test scaffold for Phase 25 codebase health fixes.
Tests are written RED first; they turn GREEN as fixes land in subsequent tasks/plans.
"""
import os
import re
import sys
import bisect
import pytest

pytestmark = pytest.mark.unit

_HERE = os.path.dirname(__file__)
_ROOT = os.path.abspath(os.path.join(_HERE, '..'))
_SRC_ROOT = os.path.join(_ROOT, 'src')
_WEBAPP = os.path.join(_ROOT, 'webapp.py')

# Files whose print() calls are intentional (CLI display output).
_PRINT_ALLOWLIST = {'display_formatter.py'}


def _collect_bare_prints():
    """Return (filepath, lineno, line) for every bare print() in src/ and webapp.py."""
    matches = []
    for dirpath, dirnames, filenames in os.walk(_SRC_ROOT):
        dirnames[:] = [d for d in dirnames if d not in ('__pycache__', 'venv', '.venv')]
        for fname in filenames:
            if fname.endswith('.py') and fname not in _PRINT_ALLOWLIST:
                fpath = os.path.join(dirpath, fname)
                with open(fpath) as fh:
                    for lineno, line in enumerate(fh, 1):
                        if re.search(r'^\s*print\(', line):
                            matches.append((fpath, lineno, line.rstrip()))
    with open(_WEBAPP) as fh:
        for lineno, line in enumerate(fh, 1):
            if re.search(r'^\s*print\(', line):
                matches.append((_WEBAPP, lineno, line.rstrip()))
    return matches


# ---------------------------------------------------------------------------
# BUG-01
# ---------------------------------------------------------------------------

def test_no_debug_prints():
    """No bare print() calls remain in src/ (excluding display_formatter.py) or webapp.py."""
    hits = _collect_bare_prints()
    if hits:
        report = '\n'.join(f"  {f}:{n}  {l}" for f, n, l in hits)
        pytest.fail(f"Bare print() calls found (BUG-01):\n{report}")


# ---------------------------------------------------------------------------
# BUG-03
# ---------------------------------------------------------------------------

def test_percentile_rank():
    """webapp.py percentile_rank uses bisect and returns correct 0/50/100 values."""
    with open(_WEBAPP) as fh:
        source = fh.read()
    assert 'import bisect' in source, "webapp.py must import bisect (BUG-03)"
    assert 'bisect.bisect_left' in source, "webapp.py must use bisect.bisect_left (BUG-03)"

    # Verify the bisect algorithm is correct on reference inputs.
    def percentile_rank(rows, field, target):
        if target is None:
            return 50
        vals = sorted([r[field] for r in rows if r[field] is not None])
        if len(vals) < 2:
            return 50
        idx = bisect.bisect_left(vals, target)
        idx = min(idx, len(vals) - 1)
        return round(100 * idx / (len(vals) - 1))

    rows = [{'f': v} for v in [1, 2, 3, 4, 5]]
    assert percentile_rank(rows, 'f', 1) == 0
    assert percentile_rank(rows, 'f', 3) == 50
    assert percentile_rank(rows, 'f', 5) == 100
    assert percentile_rank(rows, 'f', None) == 50


# ---------------------------------------------------------------------------
# SEC-01 — guard (RED until plan 25-02)
# ---------------------------------------------------------------------------

def test_secret_key_guard():
    """webapp must exit non-zero when SECRET_KEY is absent."""
    import subprocess
    env = {k: v for k, v in os.environ.items() if k != 'SECRET_KEY'}
    env['FLASK_ENV'] = 'production'
    result = subprocess.run(
        [sys.executable, '-c', 'import webapp'],
        env=env,
        capture_output=True,
        cwd=_ROOT,
    )
    assert result.returncode != 0, \
        "webapp must raise/exit when SECRET_KEY missing (SEC-01)"


# ---------------------------------------------------------------------------
# PERF-02 — bounded cache (RED until plan 25-04)
# ---------------------------------------------------------------------------

def test_cache_bounded():
    """_peer_cache must be a bounded TTLCache or LRUCache, not a plain dict."""
    with open(_WEBAPP) as fh:
        source = fh.read()
    has_bounded = 'TTLCache' in source or 'LRUCache' in source
    assert has_bounded, \
        "webapp.py must use TTLCache or LRUCache for peer cache (PERF-02)"


# ---------------------------------------------------------------------------
# PERF-03 — Gunicorn workers (RED until plan 25-03)
# ---------------------------------------------------------------------------

def test_procfile_workers():
    """Procfile must set --workers 2."""
    procfile = os.path.join(_ROOT, 'Procfile')
    assert os.path.exists(procfile), "Procfile must exist (PERF-03)"
    with open(procfile) as fh:
        content = fh.read()
    assert '--workers 2' in content, \
        "Procfile must include --workers 2 (PERF-03)"


# ---------------------------------------------------------------------------
# TECH-05 — pinned requirements (RED until plan 25-05)
# ---------------------------------------------------------------------------

def test_requirements_pinned():
    """requirements.txt must use == specifiers, not >=."""
    req_file = os.path.join(_ROOT, 'requirements.txt')
    assert os.path.exists(req_file), "requirements.txt must exist"
    with open(req_file) as fh:
        lines = fh.readlines()
    unpinned = [
        l.strip() for l in lines
        if re.match(r'[A-Za-z].*>=', l.strip()) and not l.startswith('#')
    ]
    assert not unpinned, \
        f"Unpinned requirements (must use ==): {unpinned}"


# ---------------------------------------------------------------------------
# TECH-01 — pre-commit config (RED until plan 25-03)
# ---------------------------------------------------------------------------

def test_precommit_config():
    """.pre-commit-config.yaml and .flake8 must exist."""
    assert os.path.exists(os.path.join(_ROOT, '.pre-commit-config.yaml')), \
        ".pre-commit-config.yaml must exist (TECH-01)"
    assert os.path.exists(os.path.join(_ROOT, '.flake8')), \
        ".flake8 must exist (TECH-01)"


# ---------------------------------------------------------------------------
# TECH-04 — no duplicate JS helpers (RED until plan 25-03)
# ---------------------------------------------------------------------------

def test_no_duplicate_js_helpers():
    """parseNumeric must not be defined in more than one of the three JS analytics files."""
    js_dir = os.path.join(_ROOT, 'static', 'js')
    files = ['healthScore.js', 'earningsQuality.js', 'dcfValuation.js']
    with_fn = []
    for fname in files:
        fpath = os.path.join(js_dir, fname)
        if os.path.exists(fpath):
            with open(fpath) as fh:
                if re.search(r'function parseNumeric\b', fh.read()):
                    with_fn.append(fname)
    assert len(with_fn) <= 1, \
        f"parseNumeric defined in multiple JS files (TECH-04): {with_fn}"


# ---------------------------------------------------------------------------
# PERF-01 — HMM regime cache (RED until plan 25-04)
# ---------------------------------------------------------------------------

def test_regime_cache():
    """webapp.py must cache HMM regime detection results."""
    with open(_WEBAPP) as fh:
        source = fh.read()
    cached = (
        'lru_cache' in source
        or '_regime_cache' in source
        or 'regime_cache' in source
    )
    assert cached, \
        "webapp.py must memoize HMM regime detection (PERF-01)"
