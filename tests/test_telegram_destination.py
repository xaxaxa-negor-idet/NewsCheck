from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from publication.telegram import TelegramChannelDestination
from publication.console import RenderedPost


def test_requires_credentials():
    for token, channel in (("", "@channel"), ("token", "")):
        try:
            TelegramChannelDestination(token, channel)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")
