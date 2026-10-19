from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from publication.console import ConsoleDestination, RenderedPost


def test_publish_and_edit(capsys):
    destination = ConsoleDestination()
    post = RenderedPost(event_id=1, text="Статус: НЕ ПОДТВЕРЖДЕНО")

    result = destination.publish(post)
    assert result.destination == "console"
    assert "НЕ ПОДТВЕРЖДЕНО" in capsys.readouterr().out

    edited = destination.edit(result.external_id, RenderedPost(1, "Статус: ПОДТВЕРЖДЕНО"))
    assert edited.external_id == result.external_id
    assert "ПОДТВЕРЖДЕНО" in capsys.readouterr().out

    destination.delete(result.external_id)
    assert "deleted" in capsys.readouterr().out
