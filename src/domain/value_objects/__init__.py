"""Value objects for domain layer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaxId:
    """Mã số thuế Vietnamese tax ID."""

    value: str

    def __post_init__(self):
        object.__setattr__(self, "value", self.value.replace("-", "").strip())

    def __str__(self) -> str:
        return self.value
