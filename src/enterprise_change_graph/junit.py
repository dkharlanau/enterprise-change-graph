from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .evidence import ObservedChange
from .model import GraphValidationError


def _slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return value.lower() or "unknown"


@dataclass(frozen=True)
class JUnitCase:
    test_id: str
    classname: str
    name: str
    status: str
    duration_seconds: float

    def to_dict(self) -> dict:
        return {
            "test_id": self.test_id,
            "classname": self.classname,
            "name": self.name,
            "status": self.status,
            "duration_seconds": self.duration_seconds,
        }


@dataclass(frozen=True)
class JUnitEvidence:
    cases: tuple[JUnitCase, ...]

    @property
    def failed_test_ids(self) -> tuple[str, ...]:
        return tuple(sorted(case.test_id for case in self.cases if case.status in {"failed", "error"}))

    @property
    def skipped_test_ids(self) -> tuple[str, ...]:
        return tuple(sorted(case.test_id for case in self.cases if case.status == "skipped"))

    @property
    def duration_seconds(self) -> float:
        return sum(case.duration_seconds for case in self.cases)

    def to_dict(self) -> dict:
        counts = {status: sum(1 for case in self.cases if case.status == status) for status in ("passed", "failed", "error", "skipped")}
        return {
            "summary": {
                "tests": len(self.cases),
                **counts,
                "duration_seconds": round(self.duration_seconds, 6),
                "failed_test_ids": list(self.failed_test_ids),
            },
            "cases": [case.to_dict() for case in self.cases],
        }

    def observed_change(self, change_id: str, affected_nodes: Iterable[str] = ()) -> ObservedChange:
        return ObservedChange(
            change_id=change_id,
            affected_nodes=tuple(sorted(set(affected_nodes))),
            failed_tests=self.failed_test_ids,
            outcome="failed-tests" if self.failed_test_ids else "tests-passed",
            metadata={"junit_tests": len(self.cases), "junit_duration_seconds": round(self.duration_seconds, 6)},
        )


def _test_id(case: ET.Element) -> str:
    properties = case.find("properties")
    if properties is not None:
        for prop in properties.findall("property"):
            if prop.get("name") == "ecg.test_id" and prop.get("value"):
                return str(prop.get("value"))
    classname = case.get("classname", "")
    name = case.get("name", "unnamed")
    return f"test.junit.{_slug('.'.join(part for part in (classname, name) if part))}"


def load_junit(path: str | Path) -> JUnitEvidence:
    source = Path(path)
    if not source.exists():
        raise GraphValidationError([f"JUnit file does not exist: {source}"])
    try:
        root = ET.parse(source).getroot()
    except (ET.ParseError, OSError) as exc:
        raise GraphValidationError([f"cannot parse JUnit XML {source}: {exc}"]) from exc
    cases: list[JUnitCase] = []
    for case in root.iter("testcase"):
        status = "passed"
        if case.find("failure") is not None:
            status = "failed"
        elif case.find("error") is not None:
            status = "error"
        elif case.find("skipped") is not None:
            status = "skipped"
        raw_time = case.get("time", "0")
        try:
            duration = float(raw_time or 0)
        except ValueError:
            duration = 0.0
        cases.append(
            JUnitCase(
                test_id=_test_id(case),
                classname=case.get("classname", ""),
                name=case.get("name", "unnamed"),
                status=status,
                duration_seconds=duration,
            )
        )
    if not cases:
        raise GraphValidationError([f"JUnit XML contains no testcase elements: {source}"])
    cases.sort(key=lambda item: (item.test_id, item.classname, item.name))
    return JUnitEvidence(tuple(cases))
