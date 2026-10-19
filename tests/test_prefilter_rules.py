from analysis.prefilter import should_process


def test_short_messages_are_ignored():
    assert not should_process("коротко")


def test_news_is_processed():
    assert should_process("В Москве произошло крупное ДТП с участием трёх автомобилей.")


def test_ads_are_ignored():
    assert not should_process("Лучшие ставки на спорт! Используй промокод NEWS")


def test_custom_marker():
    assert not should_process("Обычный текст с запрещённым словом", ad_markers="запрещённым")
