"""Hand-authored baseline inventories used to resolve evaluation cases.

The inventories intentionally name real artifacts and verified OA codes. The
actual typed TeachingPack factories are added in milestone 2, when the real
Reviewer adapter is introduced.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Baseline:
    id: str
    subject: str
    grade_level: str
    oa_codes: tuple[str, ...]
    activity_ids: tuple[str, ...]
    item_ids: tuple[str, ...]


BASELINES = {
    "cn_water_states_v1": Baseline(
        id="cn_water_states_v1",
        subject="Ciencias Naturales",
        grade_level="6° básico",
        oa_codes=("CN06 OA 13", "CN06 OA 15"),
        activity_ids=("water-observe", "water-record", "water-exit"),
        item_ids=("water-item-1", "water-item-2", "water-item-3"),
    ),
    "cn_energy_v1": Baseline(
        id="cn_energy_v1",
        subject="Ciencias Naturales",
        grade_level="6° básico",
        oa_codes=("CN06 OA 08", "CN06 OA 10"),
        activity_ids=("energy-predict", "energy-test", "energy-exit"),
        item_ids=("energy-item-1", "energy-item-2", "energy-item-3"),
    ),
    "ma_percentages_v1": Baseline(
        id="ma_percentages_v1",
        subject="Matemática",
        grade_level="6° básico",
        oa_codes=("MA06 OA 03", "MA06 OA 04"),
        activity_ids=("percent-model", "percent-problems", "percent-exit"),
        item_ids=("percent-item-1", "percent-item-2", "percent-item-3"),
    ),
    "ma_geometry_v1": Baseline(
        id="ma_geometry_v1",
        subject="Matemática",
        grade_level="6° básico",
        oa_codes=("MA06 OA 15", "MA06 OA 20"),
        activity_ids=("angle-build", "angle-measure", "angle-exit"),
        item_ids=("angle-item-1", "angle-item-2", "angle-item-3"),
    ),
}
