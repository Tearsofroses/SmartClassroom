import re
import os

filepath = r"d:\Projects\DoAnDN\backend\migrations\data.sql"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update the loop for devices
old_loop_start = """    FOR v_room IN
        SELECT r.id, r.room_code
        FROM rooms r
        ORDER BY r.room_code
        LIMIT 80
    LOOP"""

new_loop_start = """    FOR v_room IN
        SELECT r.id, r.room_code, SUBSTRING(r.room_code FROM '^[A-Z0-9]+') AS building_code
        FROM rooms r
        ORDER BY r.room_code
        LIMIT 80
    LOOP"""

content = content.replace(old_loop_start, new_loop_start)

# 2. Replace the INSERT INTO room_devices block
# It starts at DELETE FROM room_devices WHERE room_id = v_room.id;
# And goes until the UPDATE rooms SET devices = ...

device_insert_regex = re.compile(
    r"        DELETE FROM room_devices WHERE room_id = v_room.id;.*?UPDATE rooms",
    re.DOTALL
)

new_device_logic = """        DELETE FROM room_devices WHERE room_id = v_room.id;

        DECLARE
            v_num_lights INT := 4;
            v_num_fans INT := 2;
            v_num_acs INT := 1;
            v_i INT;
        BEGIN
            IF v_room.building_code = 'A1' THEN
                v_num_lights := 4;
                v_num_fans := 4;
                v_num_acs := 2;
            ELSIF v_room.building_code = 'A2' THEN
                v_num_lights := 6;
                v_num_fans := 4;
                v_num_acs := 1;
            ELSIF v_room.building_code = 'B1' THEN
                v_num_lights := 4;
                v_num_fans := 2;
                v_num_acs := 2;
            END IF;

            FOR v_i IN 1..v_num_lights LOOP
                INSERT INTO room_devices (id, room_id, device_id, device_type, device_index, location_front_back, location_left_right, x_percent, y_percent, power_consumption_watts, is_active, source, created_at, updated_at)
                VALUES (uuid_generate_v4(), v_room.id, REPLACE(v_room.room_code, ' ', '') || '-LIGHT-0' || v_i, 'LIGHT', v_i, CASE WHEN v_i % 2 = 1 THEN 'FRONT' ELSE 'BACK' END, CASE WHEN v_i <= v_num_lights/2 THEN 'LEFT' ELSE 'RIGHT' END, 20 + (v_i * 10), 20, 48, TRUE, 'IMPORT', NOW(), NOW());
            END LOOP;

            FOR v_i IN 1..v_num_fans LOOP
                INSERT INTO room_devices (id, room_id, device_id, device_type, device_index, location_front_back, location_left_right, x_percent, y_percent, power_consumption_watts, is_active, source, created_at, updated_at)
                VALUES (uuid_generate_v4(), v_room.id, REPLACE(v_room.room_code, ' ', '') || '-FAN-0' || v_i, 'FAN', v_i, CASE WHEN v_i % 2 = 1 THEN 'FRONT' ELSE 'BACK' END, CASE WHEN v_i <= v_num_fans/2 THEN 'LEFT' ELSE 'RIGHT' END, 30 + (v_i * 10), 30, 120, TRUE, 'IMPORT', NOW(), NOW());
            END LOOP;

            FOR v_i IN 1..v_num_acs LOOP
                INSERT INTO room_devices (id, room_id, device_id, device_type, device_index, location_front_back, location_left_right, x_percent, y_percent, power_consumption_watts, is_active, source, created_at, updated_at)
                VALUES (uuid_generate_v4(), v_room.id, REPLACE(v_room.room_code, ' ', '') || '-AC-0' || v_i, 'AC', v_i, 'BACK', CASE WHEN v_i = 1 THEN 'RIGHT' ELSE 'LEFT' END, 80, 20 + (v_i * 10), 1500, TRUE, 'IMPORT', NOW(), NOW());
            END LOOP;
        END;

        UPDATE rooms"""

content = device_insert_regex.sub(new_device_logic, content)

# 3. Update the devices JSON to include device_index
json_update_old = """                        'device_type', rd.device_type,
                        'location_front_back', rd.location_front_back,"""
json_update_new = """                        'device_type', rd.device_type,
                        'device_index', rd.device_index,
                        'location_front_back', rd.location_front_back,"""
content = content.replace(json_update_old, json_update_new)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated devices logic in data.sql")
