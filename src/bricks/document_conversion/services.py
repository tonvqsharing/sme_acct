"""Document conversion service — wraps MarkItDown with narrow seam."""

from __future__ import annotations

import io
from typing import Any

from src.bricks.document_conversion.contract import ConversionResult
from src.bricks.document_conversion.domain import MAX_MARKDOWN_CHARS, validate_file_name


class DocumentConversionService:
    """Convert office docs → Markdown via MarkItDown. Primitives in/out, no Flask."""

    def __init__(
        self,
        *,
        enable_plugins: bool = False,
        llm_client: Any | None = None,
        llm_model: str | None = None,
    ) -> None:
        self._enable_plugins = enable_plugins
        self._llm_client = llm_client
        self._llm_model = llm_model

    def _md(self) -> Any:
        from markitdown import MarkItDown

        kwargs: dict[str, Any] = {"enable_plugins": self._enable_plugins}
        if self._llm_client is not None:
            kwargs["llm_client"] = self._llm_client
            kwargs["llm_model"] = self._llm_model or "gpt-4o"
        return MarkItDown(**kwargs)

    def convert_bytes(
        self, *, data: bytes, file_name: str, file_type: str | None = None
    ) -> ConversionResult:
        validate_file_name(file_name, len(data))
        try:
            md = self._md()
            stream = io.BytesIO(data)
            # Narrowest API per Security Considerations: convert_stream
            result = md.convert_stream(
                stream,
                file_extension=file_name.rsplit(".", 1)[-1].lower() if "." in file_name else None,
            )
            text = result.text_content or ""
            if len(text) > MAX_MARKDOWN_CHARS:
                text = text[:MAX_MARKDOWN_CHARS]
                return ConversionResult(
                    success=True,
                    markdown=text,
                    title=getattr(result, "title", None),
                    file_name=file_name,
                    file_type=file_type or file_name.rsplit(".", 1)[-1].lower(),
                    warnings=[
                        f"Đã cắt {len(result.text_content or '')} → {MAX_MARKDOWN_CHARS} chars"
                    ],
                )
            return ConversionResult(
                success=True,
                markdown=text,
                title=getattr(result, "title", None),
                file_name=file_name,
                file_type=file_type or file_name.rsplit(".", 1)[-1].lower(),
            )
        except Exception as exc:  # noqa: BLE001 — surface as ConversionResult
            return ConversionResult(
                success=False, file_name=file_name, file_type=file_type or "", error=str(exc)
            )

    def convert_stream(self, stream: Any, file_name: str) -> ConversionResult:
        data = stream.read() if hasattr(stream, "read") else bytes(stream)
        if isinstance(data, str):
            data = data.encode()
        return self.convert_bytes(data=data, file_name=file_name)
