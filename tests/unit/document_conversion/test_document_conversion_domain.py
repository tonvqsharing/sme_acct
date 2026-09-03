"""Unit — document_conversion domain validation."""

from __future__ import annotations

import pytest

from src.bricks.document_conversion.domain import ALLOWED_EXTENSIONS, MAX_BYTES, validate_file_name


class TestValidateFileName:
    def test_allowed_extensions_pass(self):
        for ext in ("pdf", "docx", "xlsx", "csv", "txt"):
            assert validate_file_name(f"file.{ext}") == f"file.{ext}"

    def test_disallowed_extension_rejected(self):
        with pytest.raises(ValueError, match="chưa hỗ trợ"):
            validate_file_name("file.exe")

    def test_path_traversal_rejected(self):
        for bad in ("../etc/passwd", "a/b.pdf", "a\\b.pdf", ""):
            with pytest.raises(ValueError, match="Tên file"):
                validate_file_name(bad)

    def test_oversize_rejected(self):
        with pytest.raises(ValueError, match="quá lớn"):
            validate_file_name("file.pdf", MAX_BYTES + 1)

    def test_max_bytes_boundary(self):
        validate_file_name("file.pdf", MAX_BYTES)

    def test_allowed_extensions_count(self):
        assert len(ALLOWED_EXTENSIONS) >= 15
