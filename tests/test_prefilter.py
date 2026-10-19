from datetime import date

from matching.prefilter import EventCandidate, cheap_filter


def make_candidate(**overrides):
    values = {
        "event_id": 1,
        "location": "Москва",
        "event_date": date(2026, 10, 10),
        "event_type": "ДТП",
        "entities": {"Москва", "Садовое кольцо"},
    }
    values.update(overrides)
    return EventCandidate(**values)


def test_match_when_all_keys_align():
    assert cheap_filter(make_candidate(), "Москва", date(2026, 10, 10), "дтп", {"Садовое кольцо"})


def test_no_match_outside_window():
    assert not cheap_filter(make_candidate(), "Москва", date(2026, 10, 20), "ДТП", {"Садовое кольцо"})


def test_no_match_without_shared_entity():
    assert not cheap_filter(make_candidate(), "Москва", date(2026, 10, 10), "ДТП", {"Ленинградка"})


def test_no_match_different_location():
    assert not cheap_filter(make_candidate(), "Казань", date(2026, 10, 10), "ДТП", {"Садовое кольцо"})


def test_missing_dates_do_not_match():
    assert not cheap_filter(make_candidate(event_date=None), "Москва", date(2026, 10, 10), "ДТП", {"Садовое кольцо"})
