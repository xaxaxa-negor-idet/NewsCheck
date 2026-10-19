from publication.formatter import ClaimLine, EventPost, format_post


def test_format_post_contains_blocks():
    post = EventPost(
        event_id=1,
        original_text="В Москве произошло ДТП",
        status="ЧАСТИЧНО ПОДТВЕРЖДЕНО",
        reason="факт подтверждён, число пострадавших нет",
        claims=[ClaimLine("ДТП произошло", "CONFIRMED", ["https://example.com"])],
        source_links=["https://example.com"],
        source_channel="topor",
        original_url="https://t.me/topor/100",
        tags=["news", "москва"],
    )
    text = format_post(post)
    assert "─── NewsCheck ───" in text
    assert "Статус: 🟡 ЧАСТИЧНО ПОДТВЕРЖДЕНО" in text
    assert "ДТП произошло" in text
    assert "#news #москва" in text
    assert "https://t.me/topor/100" in text


def test_updated_line():
    post = EventPost(1, "текст", "НЕ ПОДТВЕРЖДЕНО", "нет данных", [], [], "topor", "https://t.me/topor/1", [])
    assert "Обновлено 12.10, 14:30" in format_post(post, "12.10, 14:30")
