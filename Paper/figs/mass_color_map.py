#!/usr/bin/env python3
"""Shared mass-dependent colors for recoil figures."""

from __future__ import annotations

from typing import Dict

import ROOT


# Baseline colors aligned with Analysis_Programs/Histograms.py signal palette.
BASELINE_MASS_COLORS = {
    1200: ROOT.kRed + 1,
    1600: ROOT.kAzure - 3,
    2000: ROOT.kGreen + 2,
    2400: ROOT.kMagenta + 2,
}


def baseline_color_for_mass(mass: int) -> int:
    """Return the baseline color for a given mass."""
    return BASELINE_MASS_COLORS.get(mass, ROOT.kAzure + 2)


def scenario_colors_for_mass(mass: int) -> Dict[str, int]:
    """
    Return colors for baseline and polarized overlays, keyed by scenario:
    - base
    - plus80
    - minus80
    """
    base = baseline_color_for_mass(mass)
    # Polarised colors as nearby shades of the same base color family.
    # Requested convention: +80 is always base - 3.
    plus80 = base - 3
    if mass == 1200:
        return {"base": base, "plus80": plus80, "minus80": ROOT.kRed + 4}
    if mass == 1600:
        return {"base": base, "plus80": plus80, "minus80": ROOT.kAzure + 1}
    if mass == 2000:
        return {"base": base, "plus80": plus80, "minus80": ROOT.kGreen + 4}
    if mass == 2400:
        return {"base": base, "plus80": plus80, "minus80": ROOT.kMagenta + 4}
    return {"base": base, "plus80": plus80, "minus80": base + 3}
