from __future__ import annotations


def normalize_confidence(raw_value: float) -> float:
    """Clamp the confidence value to [0.0, 1.0]."""
    return max(0.0, min(1.0, raw_value))


def compute_combined_confidence(
    capa1_confianza: float,
    capa2_is_null: bool,
) -> float:
    """
    Compute a combined confidence score after both layers.

    If capa2 returns NULL, the confidence drops significantly.
    If capa2 returns a valid classification, confidence gets a boost.
    """
    base = normalize_confidence(capa1_confianza)

    if capa2_is_null:
        return base * 0.3

    return min(1.0, base * 1.2)
