"""Database seeding script for buildings, floors, rooms, and demo runtime data."""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import (
    BehaviorLog,
    Building,
    ClassSession,
    DeviceState,
    Floor,
    RiskIncident,
    Room,
    Student,
    Subject,
    Teacher,
)

logger = logging.getLogger(__name__)

# Building configurations
A_BUILDINGS = ["A1", "A2", "A3", "A4", "A5"]
B_BUILDINGS = [f"B{i}" for i in range(1, 12)]  # B1-B11
C_BUILDINGS = ["C4", "C5", "C6"]

LAB_BUILDINGS = [
    "Science and Technology Incubators",
    "Research Center for Technology and Industrial Equipment (RECTIE)",
    "National Key Lab for Digital Control and System Engineering (DCSELAB)",
    "National Key Lab for Polymer and Composite Materials",
    "Research and Application Center for Construction Technology (REACTEC)",
    "Industrial Maintenance Training Center",
    "Business Research and Training Center",
    "Polymer Research Center",
    "Center for Developing Information Technology and Geographic Information System (Ditagis)",
    "Refinery and Petrochemical Technology Research Center (RPTC)",
]

# Building structure: (floors, rooms_per_floor)
BUILDING_CONFIGS = {
    "A": (3, 15),   # A buildings: 3 floors, 15 rooms/floor
    "B": (6, 5),    # B buildings: 6 floors, 5 rooms/floor
    "C": (2, 5),    # C buildings: 2 floors, 5 rooms/floor
    "LAB": (2, 5),  # Lab buildings: 2 floors, 5 rooms/floor
}

DEVICE_TYPES = ["LIGHT", "AC", "FAN"]
DEVICE_LOCATIONS = [
    ("FRONT", "LEFT"),
    ("BACK", "RIGHT"),
    ("FRONT", "RIGHT"),
    ("FRONT", "LEFT"),
]

DEMO_TEACHER = {
    "name": "Le Minh Hoang",
    "email": "le.minh.hoang@smartcampus.local",
    "department": "School of Computer Science and Engineering",
    "phone": "0908000001",
}

DEMO_SUBJECT = {
    "name": "Computer Vision Applications",
    "code": "AI3307",
    "description": "Applied computer vision for smart classroom analytics.",
}

DEMO_STUDENTS = [
    ("Nguyen Gia Bao", "22110001", "22110001@student.smartcampus.local", "SE-2022"),
    ("Tran Minh Khoa", "22110005", "22110005@student.smartcampus.local", "SE-2022"),
    ("Le Quoc Anh", "22110008", "22110008@student.smartcampus.local", "SE-2022"),
    ("Pham Thu Trang", "22110012", "22110012@student.smartcampus.local", "SE-2022"),
    ("Vo Thanh Dat", "22110016", "22110016@student.smartcampus.local", "SE-2022"),
    ("Nguyen Hoang Mai", "22110021", "22110021@student.smartcampus.local", "AI-2022"),
    ("Bui Khanh Linh", "22110025", "22110025@student.smartcampus.local", "AI-2022"),
    ("Do Duc Huy", "22110029", "22110029@student.smartcampus.local", "AI-2022"),
    ("Phan Thu Uyen", "22110033", "22110033@student.smartcampus.local", "EE-2022"),
    ("Trinh Gia Han", "22110037", "22110037@student.smartcampus.local", "EE-2022"),
    ("Dang Tuan Kiet", "22110041", "22110041@student.smartcampus.local", "EE-2022"),
    ("Hoang Bao Chau", "22110045", "22110045@student.smartcampus.local", "EE-2022"),
]

DEMO_ROOM_CODES = ("A1-F2-R03", "LAB9-F1-R02", "B1-F1-R02")


def _build_room_devices(room_code: str) -> list[dict]:
    """Generate deterministic device inventory for a room using location enum values."""
    devices = []
    for index, (device_type, (location_fb, location_lr)) in enumerate(zip(DEVICE_TYPES, DEVICE_LOCATIONS), start=1):
        device_id = f"{room_code}-{device_type}-{index:02d}".replace(" ", "")
        devices.append(
            {
                "device_id": device_id,
                "device_type": device_type,
                "location_front_back": location_fb,
                "location_left_right": location_lr,
                "location": f"{location_fb}_{location_lr}",
                "status": "OFF" if device_type == "AC" else "ON",
                "mqtt_topic": f"building/*/floor/*/room/{room_code}/device/{device_id}/state",
                "power_consumption_watts": {
                    "LIGHT": 48,
                    "AC": 1500,
                    "FAN": 120,
                    "CAMERA": 18,
                }[device_type],
            }
        )
    return devices


def _seed_mock_runtime_data(db: Session) -> None:
    """Seed meaningful demo teacher/subject/students/sessions and device states."""
    rooms = db.query(Room).order_by(Room.room_code.asc()).all()
    if not rooms:
        return

    # Seed device inventory and states for a useful subset of rooms.
    rooms_for_devices = rooms[:80]
    for room in rooms_for_devices:
        if not room.devices or not room.devices.get("device_list"):
            device_list = _build_room_devices(room.room_code)
            room.devices = {"device_list": device_list}
        else:
            device_list = room.devices["device_list"]

        for device in device_list:
            existing_state = (
                db.query(DeviceState)
                .filter(DeviceState.room_id == room.id, DeviceState.device_id == device["device_id"])
                .first()
            )
            if existing_state:
                continue

            db.add(
                DeviceState(
                    room_id=room.id,
                    device_id=device["device_id"],
                    device_type=device["device_type"],
                    status=device["status"],
                    manual_override=False,
                    last_updated=datetime.utcnow(),
                )
            )

    demo_active_sessions = (
        db.query(ClassSession)
        .join(Subject, Subject.id == ClassSession.subject_id)
        .filter(
            ClassSession.status == "ACTIVE",
            Subject.code.in_(["AI3307", "EE2305", "SE3315"]),
        )
        .count()
    )
    if demo_active_sessions > 0:
        db.flush()
        return

    teacher = db.query(Teacher).filter(Teacher.email == DEMO_TEACHER["email"]).first()
    if not teacher:
        teacher = Teacher(
            name=DEMO_TEACHER["name"],
            email=DEMO_TEACHER["email"],
            department=DEMO_TEACHER["department"],
            phone=DEMO_TEACHER["phone"],
        )
        db.add(teacher)
        db.flush()

    subject = db.query(Subject).filter(Subject.code == DEMO_SUBJECT["code"]).first()
    if not subject:
        subject = Subject(
            name=DEMO_SUBJECT["name"],
            code=DEMO_SUBJECT["code"],
            description=DEMO_SUBJECT["description"],
        )
        db.add(subject)
        db.flush()

    students: list[Student] = []
    for name, sid, email, class_name in DEMO_STUDENTS:
        existing = db.query(Student).filter(Student.student_id == sid).first()
        if existing:
            students.append(existing)
            continue
        student = Student(
            name=name,
            student_id=sid,
            email=email,
            class_name=class_name,
        )
        db.add(student)
        students.append(student)
    db.flush()

    room_map = {room.room_code: room for room in rooms}
    target_rooms = [room_map[code] for code in DEMO_ROOM_CODES if code in room_map]
    if not target_rooms:
        target_rooms = rooms[:3]

    session_blueprints = [
        {
            "room": target_rooms[0],
            "mode": "NORMAL",
            "start_delta": 35,
            "students_present": students[:7],
            "behavior_entries": [
                (students[0], "hand-raising", 2, 18, 0.94),
                (students[0], "answering", 1, 25, 0.92),
                (students[1], "writing", 4, 210, 0.91),
                (students[2], "reading", 3, 170, 0.89),
                (teacher, "guiding", 5, 420, 0.93),
                (teacher, "blackboard-writing", 4, 360, 0.90),
            ],
            "incidents": [],
        },
        {
            "room": target_rooms[1] if len(target_rooms) > 1 else target_rooms[0],
            "mode": "NORMAL",
            "start_delta": 95,
            "students_present": students[4:10],
            "behavior_entries": [
                (students[4], "using-computer", 4, 540, 0.93),
                (students[5], "discussing", 2, 88, 0.87),
                (students[6], "writing", 3, 165, 0.88),
                (teacher, "guiding", 4, 300, 0.91),
                (teacher, "on-stage-interaction", 3, 180, 0.89),
            ],
            "incidents": [],
        },
        {
            "room": target_rooms[2] if len(target_rooms) > 2 else target_rooms[-1],
            "mode": "TESTING",
            "start_delta": 18,
            "students_present": students[:8],
            "behavior_entries": [
                (students[1], "talking", 1, 18, 0.83),
                (students[2], "bow-head", 3, 74, 0.81),
                (students[6], "using-phone", 1, 42, 0.92),
                (teacher, "guiding", 2, 120, 0.88),
            ],
            "incidents": [
                (students[2], 0.82, "CRITICAL", {"head-turning": 4, "talking": 2}),
                (students[6], 0.68, "HIGH", {"phone-usage": 1, "head-turning": 2}),
            ],
        },
    ]

    for blueprint in session_blueprints:
        room = blueprint["room"]
        existing_active = (
            db.query(ClassSession)
            .filter(
                ClassSession.room_id == room.id,
                ClassSession.teacher_id == teacher.id,
                ClassSession.subject_id == subject.id,
                ClassSession.status == "ACTIVE",
            )
            .first()
        )
        if existing_active:
            continue

        start_time = datetime.utcnow() - timedelta(minutes=blueprint["start_delta"])
        session = ClassSession(
            room_id=room.id,
            teacher_id=teacher.id,
            subject_id=subject.id,
            mode=blueprint["mode"],
            status="ACTIVE",
            start_time=start_time,
            students_present=[str(student.id) for student in blueprint["students_present"]],
        )
        db.add(session)
        db.flush()

        for actor, behavior, count, duration, confidence in blueprint["behavior_entries"]:
            actor_type = "TEACHER" if actor.id == teacher.id else "STUDENT"
            db.add(
                BehaviorLog(
                    session_id=session.id,
                    actor_id=actor.id,
                    actor_type=actor_type,
                    behavior_class=behavior,
                    count=count,
                    duration_seconds=duration,
                    detected_at=start_time + timedelta(minutes=5),
                    yolo_confidence=confidence,
                )
            )

        for student, score, risk_level, behaviors in blueprint["incidents"]:
            db.add(
                RiskIncident(
                    session_id=session.id,
                    student_id=student.id,
                    risk_score=score,
                    risk_level=risk_level,
                    triggered_behaviors=behaviors,
                    flagged_at=start_time + timedelta(minutes=8),
                    reviewed=False,
                )
            )

    db.flush()


def seed_buildings(db: Session) -> None:
    """Seed the database with all buildings, floors, and rooms."""
    logger.info("Starting database seeding...")
    
    # Check if buildings already exist
    existing_count = db.query(Building).count()
    if existing_count > 0:
        logger.info(f"Database already seeded with {existing_count} buildings. Reusing structure and seeding demo runtime data.")
        _seed_mock_runtime_data(db)
        db.commit()
        return
    
    buildings_created = 0
    floors_created = 0
    rooms_created = 0
    
    try:
        # ==============================================================================
        # SEED A BUILDINGS (A1-A5): 3 floors, 15 rooms per floor
        # ==============================================================================
        for building_name in A_BUILDINGS:
            building = Building(name=building_name, code=building_name, location=f"Campus Zone A")
            db.add(building)
            db.flush()
            buildings_created += 1
            
            floors, rooms_per_floor = BUILDING_CONFIGS["A"]
            for floor_num in range(1, floors + 1):
                floor = Floor(building_id=building.id, floor_number=floor_num, name=f"Floor {floor_num}")
                db.add(floor)
                db.flush()
                floors_created += 1
                
                for room_num in range(1, rooms_per_floor + 1):
                    room_code = f"{building_name}-F{floor_num}-R{room_num:02d}"
                    room = Room(
                        floor_id=floor.id,
                        room_code=room_code,
                        name=f"{building_name} Floor {floor_num} Room {room_num}",
                        capacity=30,
                    )
                    db.add(room)
                    rooms_created += 1
        
        # ==============================================================================
        # SEED B BUILDINGS (B1-B11): 6 floors, 5 rooms per floor
        # ==============================================================================
        for building_name in B_BUILDINGS:
            building = Building(name=building_name, code=building_name, location=f"Campus Zone B")
            db.add(building)
            db.flush()
            buildings_created += 1
            
            floors, rooms_per_floor = BUILDING_CONFIGS["B"]
            for floor_num in range(1, floors + 1):
                floor = Floor(building_id=building.id, floor_number=floor_num, name=f"Floor {floor_num}")
                db.add(floor)
                db.flush()
                floors_created += 1
                
                for room_num in range(1, rooms_per_floor + 1):
                    room_code = f"{building_name}-F{floor_num}-R{room_num:02d}"
                    room = Room(
                        floor_id=floor.id,
                        room_code=room_code,
                        name=f"{building_name} Floor {floor_num} Room {room_num}",
                        capacity=30,
                    )
                    db.add(room)
                    rooms_created += 1
        
        # ==============================================================================
        # SEED C BUILDINGS (C4-C6): 2 floors, 5 rooms per floor
        # ==============================================================================
        for building_name in C_BUILDINGS:
            building = Building(name=building_name, code=building_name, location=f"Campus Zone C")
            db.add(building)
            db.flush()
            buildings_created += 1
            
            floors, rooms_per_floor = BUILDING_CONFIGS["C"]
            for floor_num in range(1, floors + 1):
                floor = Floor(building_id=building.id, floor_number=floor_num, name=f"Floor {floor_num}")
                db.add(floor)
                db.flush()
                floors_created += 1
                
                for room_num in range(1, rooms_per_floor + 1):
                    room_code = f"{building_name}-F{floor_num}-R{room_num:02d}"
                    room = Room(
                        floor_id=floor.id,
                        room_code=room_code,
                        name=f"{building_name} Floor {floor_num} Room {room_num}",
                        capacity=30,
                    )
                    db.add(room)
                    rooms_created += 1
        
        # ==============================================================================
        # SEED LAB BUILDINGS (10 specialized labs): 2 floors, 5 rooms per floor
        # ==============================================================================
        for lab_num, lab_name in enumerate(LAB_BUILDINGS, 1):
            building = Building(name=lab_name, code=f"LAB{lab_num}", location=f"Research Campus")
            db.add(building)
            db.flush()
            buildings_created += 1
            
            floors, rooms_per_floor = BUILDING_CONFIGS["LAB"]
            for floor_num in range(1, floors + 1):
                floor = Floor(building_id=building.id, floor_number=floor_num, name=f"Floor {floor_num}")
                db.add(floor)
                db.flush()
                floors_created += 1
                
                for room_num in range(1, rooms_per_floor + 1):
                    room_code = f"LAB{lab_num}-F{floor_num}-R{room_num:02d}"
                    room = Room(
                        floor_id=floor.id,
                        room_code=room_code,
                        name=f"{lab_name} Floor {floor_num} Room {room_num}",
                        capacity=25,
                    )
                    db.add(room)
                    rooms_created += 1
        
        # Commit all changes
        _seed_mock_runtime_data(db)
        db.commit()
        
        logger.info("=" * 80)
        logger.info("DATABASE SEEDING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"✓ Buildings created: {buildings_created}")
        logger.info(f"  - A Buildings (A1-A5): 5 buildings × 3 floors × 15 rooms = 225 rooms")
        logger.info(f"  - B Buildings (B1-B11): 11 buildings × 6 floors × 5 rooms = 330 rooms")
        logger.info(f"  - C Buildings (C4-C6): 3 buildings × 2 floors × 5 rooms = 30 rooms")
        logger.info(f"  - Lab Buildings (10): 10 buildings × 2 floors × 5 rooms = 100 rooms")
        logger.info(f"✓ Floors created: {floors_created}")
        logger.info(f"✓ Rooms created: {rooms_created}")
        logger.info("✓ Demo runtime data seeded: devices, sessions, behavior logs, and incidents")
        logger.info(f"  TOTAL: {buildings_created} buildings, {floors_created} floors, {rooms_created} rooms")
        logger.info("=" * 80)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error during seeding: {e}")
        raise
