"""Utility helpers for optional Seaborn integration.

This module centralises all Seaborn usages so the rest of the codebase can
gracefully operate even when the optional dependency is not installed.  When
Seaborn is available we delegate calls directly to it, otherwise we provide
light‑weight matplotlib fallbacks that cover the behaviours relied on by the
examples and API routes (palette generation, style configuration and heatmaps).
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np


_SEABORN_TRIED = False
_SEABORN_MODULE = None


def _load_seaborn():
    """Lazily import seaborn, caching the result for future calls."""

    global _SEABORN_TRIED, _SEABORN_MODULE
    if not _SEABORN_TRIED:
        try:  # pragma: no cover - optional dependency
            import seaborn as sns  # type: ignore
        except Exception:  # pragma: no cover - importing seaborn failed
            sns = None
        _SEABORN_MODULE = sns
        _SEABORN_TRIED = True
    return _SEABORN_MODULE


def get_seaborn():
    """Return the imported seaborn module or ``None`` when unavailable."""

    return _load_seaborn()


def ensure_matplotlib_style(style: str, fallback: str = "default") -> str:
    """Apply a matplotlib style with a safe fallback.

    Parameters
    ----------
    style:
        Preferred matplotlib style to apply.
    fallback:
        Fallback style name when the preferred one is missing.

    Returns
    -------
    str
        The style that ended up being applied.
    """

    try:
        plt.style.use(style)
        return style
    except (OSError, ValueError):
        if fallback and fallback != style:
            return ensure_matplotlib_style(fallback, fallback="default")
        plt.style.use("default")
        return "default"


def set_style(style: str = "whitegrid", fallback: str = "default") -> None:
    """Configure seaborn/matplotlib plotting style.

    When seaborn is present we rely on ``sns.set_style``.  Otherwise we emulate
    the look by applying the closest ``seaborn-v0_8-*`` matplotlib style if it
    exists, defaulting to the provided fallback.
    """

    sns = get_seaborn()
    if sns is not None:  # pragma: no cover - requires optional dependency
        try:
            sns.set_style(style)
            return
        except Exception:
            pass

    candidate = f"seaborn-v0_8-{style}" if style else None
    if candidate:
        ensure_matplotlib_style(candidate, fallback)
    else:
        ensure_matplotlib_style(fallback or "default")


def _resolve_cmap_name(name: str) -> str:
    if name == "husl":
        # ``husl`` is a seaborn alias; use a perceptually uniform alternative.
        return "hsv"
    return name if name in plt.colormaps() else "tab10"


def color_palette(name: str = "husl", n_colors: Optional[int] = None) -> List:
    """Return a colour palette that mirrors seaborn's API."""

    sns = get_seaborn()
    if sns is not None:  # pragma: no cover - requires optional dependency
        try:
            return list(sns.color_palette(name, n_colors))
        except Exception:
            pass

    if n_colors is None:
        n_colors = 10

    cmap = plt.get_cmap(_resolve_cmap_name(name))
    if n_colors <= 1:
        return [cmap(0.0)]
    return [cmap(i / (n_colors - 1)) for i in range(n_colors)]


def set_palette(name: str = "husl", n_colors: Optional[int] = None) -> Sequence:
    """Set the active plotting palette, returning the colours that were used."""

    colours = color_palette(name, n_colors)
    sns = get_seaborn()
    if sns is not None:  # pragma: no cover - requires optional dependency
        try:
            sns.set_palette(colours)
        except Exception:
            pass

    plt.rcParams['axes.prop_cycle'] = plt.cycler(color=colours)
    return colours


def heatmap(
    data: Iterable,
    ax=None,
    cmap: str = "viridis",
    annot: bool = False,
    fmt: str = ".2f",
    cbar: bool = True,
    center: Optional[float] = None,
    annot_kws: Optional[dict] = None,
    **kwargs,
):
    """Plot a heatmap using seaborn when available, otherwise matplotlib."""

    sns = get_seaborn()
    if sns is not None:  # pragma: no cover - requires optional dependency
        return sns.heatmap(
            data,
            ax=ax,
            cmap=cmap,
            annot=annot,
            fmt=fmt,
            cbar=cbar,
            center=center,
            annot_kws=annot_kws,
            **kwargs,
        )

    if ax is None:
        ax = plt.gca()

    values = np.asarray(data)
    norm = None
    if center is not None:
        from matplotlib.colors import TwoSlopeNorm

        norm = TwoSlopeNorm(vcenter=center, vmin=np.nanmin(values), vmax=np.nanmax(values))

    im = ax.imshow(values, cmap=cmap, aspect="auto", norm=norm)

    if cbar:
        plt.colorbar(im, ax=ax)

    if hasattr(data, "columns"):
        ax.set_xticks(np.arange(values.shape[1]))
        ax.set_xticklabels(list(data.columns), rotation=45, ha="right")
    else:
        ax.set_xticks(np.arange(values.shape[1]))

    if hasattr(data, "index"):
        ax.set_yticks(np.arange(values.shape[0]))
        ax.set_yticklabels(list(data.index))
    else:
        ax.set_yticks(np.arange(values.shape[0]))

    if annot:
        annot_kws = annot_kws or {}
        text_color = annot_kws.get("color", "black")
        for i in range(values.shape[0]):
            for j in range(values.shape[1]):
                ax.text(j, i, format(values[i, j], fmt), ha="center", va="center", color=text_color)

    ax.set_aspect("auto")
    return im


__all__ = [
    "color_palette",
    "ensure_matplotlib_style",
    "get_seaborn",
    "heatmap",
    "set_palette",
    "set_style",
]

