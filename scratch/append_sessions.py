import re
import os

filepath = r"d:\Projects\DoAnDN\backend\migrations\data.sql"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

new_sessions_logic = """
    -- Injecting additional active sessions across multiple buildings
    INSERT INTO class_sessions (
        id, room_id, teacher_id, subject_id, mode, start_time, students_present, status, created_at, updated_at
    )
    SELECT
        uuid_generate_v4(),
        r.id,
        v_lecturer_teacher_id,
        v_ai_subject_id,
        'NORMAL',
        NOW() - (random() * interval '45 minutes'),
        '[]'::jsonb,
        'ACTIVE',
        NOW(),
        NOW()
    FROM rooms r
    WHERE r.room_code IN ('A1-102', 'A2-204', 'A2-301', 'B1-205', 'B2-101', 'C1-103', 'LAB1-101')
    ON CONFLICT DO NOTHING;

END $$;
"""

content = content.replace("END $$;", new_sessions_logic)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Appended more active sessions to data.sql")
