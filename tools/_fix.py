# -*- coding: utf-8 -*-
from pathlib import Path

content = Path('core/pipeline.py').read_text(encoding='utf-8-sig')

old = '''            event_data = analysis["event"]

            # Stage 5: Event creation (simplified matcher for now — no existing events yet)'''
new = '''            event_data = analysis["event"]

            # Stage 5: duplicate detection — skip if this event already exists
            existing_event_id = find_existing_event(event_data["title"], message["original_text"], self.db_path)
            if existing_event_id:
                conn.execute("UPDATE messages SET processing_status='IGNORED' WHERE id=?", (message_id,))
                conn.commit()
                return PipelineOutcome(message_id, True, existing_event_id, "IGNORED", "duplicate event")

            fingerprint = compute_fingerprint(event_data["title"] + " " + message["original_text"][:200])
'''
content = content.replace(old, new)

old_vals = '''(event_data["title"], event_data["summary"], event_data["location"],
                 event_data["event_date"], event_data["event_type"], "ТРЕБУЕТ ДОПОЛНИТЕЛЬНОЙ ПРОВЕРКИ")'''
new_vals = '''(event_data["title"], event_data["summary"], event_data["location"],
                 event_data["event_date"], event_data["event_type"], "ТРЕБУЕТ ДОПОЛНИТЕЛЬНОЙ ПРОВЕРКИ", fingerprint)'''
content = content.replace(old_vals, new_vals)

content = content.replace(' (simplified matcher for now — no existing events yet)', '')

Path('core/pipeline.py').write_text(content, encoding='utf-8')
print('fixed')
