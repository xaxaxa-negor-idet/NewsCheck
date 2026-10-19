from datetime import datetime, timedelta

from scheduler.recheck import RecheckSchedule, schedule_recheck, should_archive


def test_recheck_sequence():
    now = datetime(2026, 10, 20, 12, 0)
    results = [schedule_recheck(i, now=now) for i in range(5)]
    delays = [(r.next_recheck_at - now).total_seconds() / 3600 for r in results[:4]]
    assert delays == [1, 2, 6, 12]
    assert results[4].status == "RECHECK_LIMIT_REACHED"
    assert results[4].next_recheck_at is None


def test_archive_after_seven_days():
    now = datetime(2026, 10, 20)
    assert should_archive(now - timedelta(days=7), now)
    assert not should_archive(now - timedelta(days=6), now)
