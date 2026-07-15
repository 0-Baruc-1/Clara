import json
import re
from pathlib import Path
from typing import Protocol
from unicodedata import combining, normalize
from app.curriculum.models import CurriculumCatalog, CurriculumEntry

class CurriculumProvider(Protocol):
    def candidates(self, subject: str | None, grade_level: str | None) -> list[CurriculumEntry]: ...
    def cache_context(self) -> str: ...
    def find_by_code(self, code: str) -> CurriculumEntry | None: ...
    def coverage(self) -> dict[str, list[str]]: ...

def normalized(value: str) -> str:
    # Both degree and masculine-ordinal symbols mean "curso" here, never a letter.
    value = value.replace("\u00b0", " ").replace("\u00ba", " ")
    plain = "".join(char for char in normalize("NFKD", value.casefold()) if not combining(char))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", plain.replace("�", " ")).split())

class JsonCurriculumProvider:
    def __init__(self, path: Path | None = None) -> None:
        self.catalog = CurriculumCatalog.model_validate_json((path or Path(__file__).with_name("sample_objectives.json")).read_text(encoding="utf-8"))
    def candidates(self, subject: str | None, grade_level: str | None) -> list[CurriculumEntry]:
        def matches(value: str | None, expected: str) -> bool:
            actual, target = normalized(value or ""), normalized(expected)
            return not actual or actual in target or target in actual
        return [entry for entry in self.catalog.entries if matches(subject, entry.subject) and matches(grade_level, entry.grade_level)]
    def cache_context(self) -> str: return json.dumps(self.catalog.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
    def find_by_code(self, code: str) -> CurriculumEntry | None: return next((entry for entry in self.catalog.entries if entry.objective.code.casefold() == code.casefold()), None)
    def coverage(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for entry in self.catalog.entries:
            result.setdefault(entry.subject, [])
            if entry.grade_level not in result[entry.subject]: result[entry.subject].append(entry.grade_level)
        return result
