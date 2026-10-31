
from src.database.config import supabase
import bcrypt
from datetime import datetime


def hash_pass(pwd):
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()


def check_pass(pwd, hashed):
    return bcrypt.checkpw(pwd.encode(), hashed.encode())


def check_teacher_exits(username):
    response = supabase.table("teachers").select("username").eq("username", username).execute()
    return len(response.data) > 0


def create_teacher(username, password, name):
    data = {
        "username": username,
        "password": hash_pass(password),
        "name": name
    }

    response = supabase.table("teachers").insert(data).execute()
    return response.data


def teacher_login(username, password):
    response = supabase.table("teachers").select("*").eq("username", username).execute()

    if response.data:
        teacher = response.data[0]

        if check_pass(password, teacher['password']):
            return teacher

    return None


def get_all_students():
    response = supabase.table('students').select("*").execute()
    return response.data


def get_student_by_id(student_id):
    response = supabase.table('students').select("*").eq('student_id', student_id).execute()
    if response.data:
        return response.data[0]
    return None


def create_student(new_name, face_embedding=None, voice_embedding=None):
    data = {
        'name': new_name,
        'face_embedding': face_embedding,
        'voice_embedding': voice_embedding
    }

    response = supabase.table('students').insert(data).execute()
    return response.data


def update_student_profile(student_id, name=None, face_embedding=None, voice_embedding=None):
    data = {}
    if name is not None:
        data['name'] = name
    if face_embedding is not None:
        data['face_embedding'] = face_embedding
    if voice_embedding is not None:
        data['voice_embedding'] = voice_embedding

    if not data:
        return None

    response = supabase.table('students').update(data).eq('student_id', student_id).execute()
    return response.data


def create_subject(subject_code, name, section, teacher_id):
    data = {
        "subject_code": subject_code,
        "name": name,
        "section": section,
        "teacher_id": teacher_id
    }

    response = supabase.table("subjects").insert(data).execute()
    return response.data


def get_subject_by_id(subject_id):
    response = supabase.table('subjects').select("*").eq('subject_id', subject_id).execute()
    if response.data:
        return response.data[0]
    return None


def delete_subject(subject_id):
    try:
        # Delete related attendance logs
        supabase.table('attendance_logs').delete().eq('subject_id', subject_id).execute()
        # Delete related enrollments
        supabase.table('subject_students').delete().eq('subject_id', subject_id).execute()
        # Delete subject
        response = supabase.table('subjects').delete().eq('subject_id', subject_id).execute()
        return True, response.data
    except Exception as e:
        return False, str(e)


def get_teacher_subjects(teacher_id):
    try:
        response = supabase.table('subjects').select(
            "*, subject_students(count), attendance_logs(timestamp)"
        ).eq("teacher_id", teacher_id).execute()

        subjects = response.data

        for sub in subjects:
            sub['total_students'] = (
                sub.get("subject_students", [{}])[0].get('count', 0)
                if sub.get('subject_students') else 0
            )

            attendance = sub.get('attendance_logs', [])

            unique_sessions = len(set(
                log['timestamp']
                for log in attendance
                if log.get('timestamp')
            ))

            sub['total_classes'] = unique_sessions

            sub.pop('subject_students', None)
            sub.pop('attendance_logs', None)

        return subjects

    except Exception as e:
        print(f"Error fetching teacher subjects: {e}")
        return []


def enroll_student_to_subject(student_id, subject_id):
    # Check if already enrolled
    existing = supabase.table('subject_students').select('*').eq(
        'student_id', student_id
    ).eq('subject_id', subject_id).execute()

    if existing.data:
        return existing.data

    data = {
        'student_id': student_id,
        'subject_id': subject_id
    }

    response = supabase.table('subject_students').insert(data).execute()
    return response.data


def unenroll_student_to_subject(student_id, subject_id):
    response = supabase.table('subject_students').delete().eq(
        'student_id', student_id
    ).eq(
        'subject_id', subject_id
    ).execute()

    return response.data


def get_enrolled_students(subject_id):
    """Fetch all students enrolled in a specific subject."""
    try:
        response = supabase.table('subject_students').select(
            'student_id, students(student_id, name, face_embedding, voice_embedding)'
        ).eq('subject_id', subject_id).execute()

        students = []
        for item in response.data:
            s = item.get('students')
            if s:
                students.append(s)
        return sorted(students, key=lambda x: x.get('name', '').lower())
    except Exception as e:
        print(f"Error fetching enrolled students: {e}")
        return []


def get_student_subjects(student_id):
    response = supabase.table('subject_students').select(
        '*, subjects(*)'
    ).eq('student_id', student_id).execute()

    return response.data


def get_student_attendance(student_id):
    response = supabase.table('attendance_logs').select(
        '*, subjects(*)'
    ).eq('student_id', student_id).order('timestamp', desc=True).execute()

    return response.data


def record_attendance_session(subject_id, attendance_dict, timestamp=None):
    """
    Records attendance for a classroom session.
    attendance_dict: dict of {student_id: bool (is_present)}
    timestamp: ISO timestamp string (defaults to current UTC time if None)
    """
    if timestamp is None:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Clean existing records for this subject and exact timestamp if re-marking
    try:
        supabase.table('attendance_logs').delete().eq(
            'subject_id', subject_id
        ).eq('timestamp', timestamp).execute()
    except Exception:
        pass

    rows = []
    for sid, is_present in attendance_dict.items():
        rows.append({
            'subject_id': int(subject_id),
            'student_id': int(sid),
            'is_present': bool(is_present),
            'timestamp': timestamp
        })

    if rows:
        response = supabase.table('attendance_logs').insert(rows).execute()
        return response.data
    return []


def get_subject_attendance_logs(subject_id):
    """
    Fetch all attendance logs for a subject, with student details.
    """
    try:
        response = supabase.table('attendance_logs').select(
            '*, students(student_id, name)'
        ).eq('subject_id', subject_id).order('timestamp', desc=True).execute()

        return response.data
    except Exception as e:
        print(f"Error fetching attendance logs: {e}")
        return []


def delete_attendance_session(subject_id, timestamp):
    """
    Deletes all attendance records for a specific subject session timestamp.
    """
    try:
        response = supabase.table('attendance_logs').delete().eq(
            'subject_id', subject_id
        ).eq('timestamp', timestamp).execute()
        return True, response.data
    except Exception as e:
        return False, str(e)


def create_attendance(logs):
    response = supabase.table('attendance_logs').insert(logs).execute()
    return response.data


def get_attendance_for_teacher(teacher_id):
    response = supabase.table('attendance_logs').select("*, subjects!inner(*)").eq('subjects.teacher_id', teacher_id).execute()
    return response.data


check_teacher_exists = check_teacher_exits
