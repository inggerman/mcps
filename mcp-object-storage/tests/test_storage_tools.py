from unittest.mock import MagicMock

import pytest
from mcp_object_storage.tools.storage_tools import list_objects, presign_download, upload_text
from mcp_shared.errors import ValidationError


def test_list_and_presign() -> None:
    client = MagicMock()
    client.list_objects_v2.return_value = {
        "Contents": [{"Key": "a.txt", "Size": 4}],
        "IsTruncated": False,
    }
    client.generate_presigned_url.return_value = "https://example.test/signed"
    assert list_objects(client, "bucket")["objects"][0]["key"] == "a.txt"
    assert presign_download(client, "bucket", "a.txt") == "https://example.test/signed"


def test_write_requires_opt_in() -> None:
    with pytest.raises(ValidationError, match="ALLOW_WRITE"):
        upload_text(MagicMock(), "bucket", "a.txt", "data", allow_write=False)
