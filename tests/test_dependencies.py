"""Reproducible production and CI dependency manifests."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _package_lines(path):
    return [
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.strip().startswith('#')
    ]


def test_production_dependencies_are_exactly_pinned():
    lines = _package_lines(ROOT / 'requirements.txt')
    assert lines
    assert all('==' in line for line in lines)


def test_ci_dependencies_are_exactly_pinned():
    lines = _package_lines(ROOT / 'requirements-ci.txt')
    assert lines
    assert all('==' in line for line in lines)


def test_vercel_manifest_points_to_pinned_production_manifest():
    source = (ROOT / 'requirements-vercel.txt').read_text()
    assert 'requirements.txt' in source
