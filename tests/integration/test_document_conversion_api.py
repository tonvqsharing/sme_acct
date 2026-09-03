"""Integration — document_conversion API via MarkItDown."""

from __future__ import annotations

import io


def test_supported_types_requires_auth(app):
    c = app.test_client()
    r = c.get("/api/v1/documents/supported-types")
    assert r.status_code == 401


def test_convert_single_and_batch(admin_client):
    # single
    data = {"file": (io.BytesIO(b"Hello\n- a\n- b"), "note.txt")}
    r = admin_client.post(
        "/api/v1/documents/convert", data=data, content_type="multipart/form-data"
    )
    assert r.status_code == 200
    j = r.get_json()["data"]
    assert j["file_name"] == "note.txt"
    assert "Hello" in j["markdown"]

    # batch
    data2 = {
        "files": [
            (io.BytesIO(b"a,b\n1,2"), "data.csv"),
            (io.BytesIO(b"# T\nx"), "t.md"),
        ]
    }
    r2 = admin_client.post(
        "/api/v1/documents/convert-batch", data=data2, content_type="multipart/form-data"
    )
    assert r2.status_code == 200
    assert len(r2.get_json()["data"]) == 2
    assert r2.get_json()["data"][0]["success"] is True


def test_invalid_extension_rejected(admin_client):
    data = {"file": (io.BytesIO(b"xxx"), "bad.exe")}
    r = admin_client.post(
        "/api/v1/documents/convert", data=data, content_type="multipart/form-data"
    )
    assert r.status_code == 422
    assert r.get_json()["code"] == "INVALID_FILE"
