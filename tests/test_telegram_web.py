from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sources.telegram_web import parse_public_page


SAMPLE = '''
<div class="tgme_widget_message_wrap js-widget_message_wrap">
 <div class="tgme_widget_message text_not_supported_wrap js-widget_message" data-post="topor/100">
  <div class="tgme_widget_message_bubble">
   <div class="tgme_widget_message_text js-message_text" dir="auto">Первая строка<br/><br/>Вторая &amp; строка</div>
   <a class="tgme_widget_message_photo_wrap" style="background-image:url('https://cdn4.telesco.pe/file/photo1.jpg')"></a>
   <span class="tgme_widget_message_edited">edited</span>
   <div class="tgme_widget_message_footer"><a href="https://t.me/topor/100"><time datetime="2026-10-01T10:00:00+00:00">10:00</time></a></div>
  </div>
 </div>
</div>
<div class="tgme_widget_message_wrap js-widget_message_wrap">
 <div class="tgme_widget_message text_not_supported_wrap js-widget-message" data-post="topor/101">
  <div class="tgme_widget_message_bubble">
   <div class="tgme_widget_message_text js-message_text" dir="auto">Другое сообщение</div>
   <div class="tgme_widget_message_footer"><a href="https://t.me/topor/101"><time datetime="2026-10-02T11:00:00+00:00">11:00</time></a></div>
  </div>
 </div>
</div>
'''


def test_parse_extracts_fields():
    messages = parse_public_page(SAMPLE, 'topor')
    assert len(messages) == 2
    first, second = messages
    assert first.source_message_id == '100'
    assert first.text == 'Первая строка\n\nВторая & строка'
    assert first.media == ['https://cdn4.telesco.pe/file/photo1.jpg']
    assert first.published_at is not None
    assert first.source_url == 'https://t.me/topor/100'
    assert first.edited_at is not None
    assert second.source_message_id == '101'
    assert second.edited_at is None
