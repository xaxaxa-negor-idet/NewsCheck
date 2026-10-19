from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sources.media_fetcher import download_media


class FakeResponse:
    def __init__(self, content):
        self.content = content
    def raise_for_status(self):
        pass


class FakeSession:
    def __init__(self, content):
        self.content = content
    def get(self, url, timeout=30):
        return FakeResponse(self.content)


def test_download_is_idempotent(tmp_path):
    content = b"image-data"
    session = FakeSession(content)
    first = download_media("https://cdn.example/photo.jpg", tmp_path, session)
    second = download_media("https://cdn.example/photo.jpg", tmp_path, session)

    assert first == second
    assert first[0].read_bytes() == content
    assert first[0].suffix == ".jpg"


def test_rejects_non_http(tmp_path):
    try:
        download_media("file:///etc/passwd", tmp_path, FakeSession(b""))
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
