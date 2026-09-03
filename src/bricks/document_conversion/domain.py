"""Document conversion domain — pure Python, no Flask/SQLAlchemy/MarkItDown imports."""

from __future__ import annotations

from enum import Enum


class DocumentType(Enum):
    """Supported source types (MarkItDown coverage)."""

    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    XLS = "xls"
    HTML = "html"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    TXT = "txt"
    ZIP = "zip"
    IMAGE = "image"
    AUDIO = "audio"
    EPUB = "epub"


# Max upload sizes per operation — prevents LLM token blow-up
MAX_BYTES = 20 * 1024 * 1024  # 20 MB
MAX_MARKDOWN_CHARS = 500_000

# Allowed extensions — sanitized inputs only (Security Considerations per MarkItDown)
ALLOWED_EXTENSIONS = frozenset(
    {
        "pdf",
        "docx",
        "doc",
        "pptx",
        "xlsx",
        "xls",
        "html",
        "htm",
        "csv",
        "json",
        "xml",
        "txt",
        "md",
        "zip",
        "png",
        "jpg",
        "jpeg",
        "gif",
        "bmp",
        "tiff",
        "mp3",
        "wav",
        "m4a",
        "epub",
    }
)


def validate_file_name(file_name: str, max_bytes: int | None = None) -> str:
    """Validate file name & size at domain boundary. Returns sanitized file_name."""
    if not file_name or "/" in file_name or "\\" in file_name or ".." in file_name:
        raise ValueError("Tên file không hợp lệ")
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Định dạng .{ext} chưa hỗ trợ (chỉ: {sorted(ALLOWED_EXTENSIONS)})")
    if max_bytes is not None and max_bytes > MAX_BYTES:
        raise ValueError(f"File quá lớn ({max_bytes} bytes > {MAX_BYTES})")
    return file_name
