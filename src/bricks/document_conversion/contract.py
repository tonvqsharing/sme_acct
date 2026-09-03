"""Public port — document_conversion brick (MarkItDown)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversionResult:
    """Result of a single document conversion."""

    success: bool
    markdown: str = ""
    title: str | None = None
    file_name: str = ""
    file_type: str = ""
    warnings: list[str] = field(default_factory=list)
    error: str = ""


class DocumentConversionPort(ABC):
    """Port for converting office documents to Markdown."""

    @abstractmethod
    def convert_bytes(
        self,
        *,
        data: bytes,
        file_name: str,
        file_type: str | None = None,
    ) -> ConversionResult: ...

    @abstractmethod
    def convert_stream(self, stream: Any, file_name: str) -> ConversionResult: ...
