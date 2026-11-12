
import dlib
import streamlit as st
import numpy as np

from PIL import Image, ImageDraw
import face_recognition_models

from src.database.db import get_all_students


@st.cache_resource
def load_dlib_models():
    detector = dlib.get_frontal_face_detector()

    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()
    )

    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )

    return detector, sp, facerec


def get_face_embeddings(image_np):
    detector, sp, facerec = load_dlib_models()

    image_np = np.ascontiguousarray(
        image_np,
        dtype=np.uint8
    )

    faces = detector(image_np, 2)
    encodings = []

    for face in faces:
        shape = sp(image_np, face)

        face_descriptor = facerec.compute_face_descriptor(
            image_np,
            shape,
            3
        )

        encoding = np.asarray(
            face_descriptor,
            dtype=np.float64
        )

        if (
            encoding.shape == (128,)
            and np.all(np.isfinite(encoding))
        ):
            encodings.append(encoding)

    return encodings


def get_faces_with_boxes(image_np):
    detector, sp, facerec = load_dlib_models()

    image_np = np.ascontiguousarray(
        image_np,
        dtype=np.uint8
    )

    faces = detector(image_np, 2)
    results = []

    for face in faces:
        shape = sp(image_np, face)

        face_descriptor = facerec.compute_face_descriptor(
            image_np,
            shape,
            2
        )

        encoding = np.asarray(
            face_descriptor,
            dtype=np.float64
        )

        if (
            encoding.shape != (128,)
            or not np.all(np.isfinite(encoding))
        ):
            continue

        results.append({
            "box": (
                face.left(),
                face.top(),
                face.right(),
                face.bottom()
            ),
            "encoding": encoding
        })

    return results


@st.cache_resource
def get_trained_model():
    X = []
    Y = []

    student_db = get_all_students() or []

    for student in student_db:
        embedding = student.get("face_embedding")
        student_id = student.get("student_id")

        if embedding is None or student_id is None:
            continue

        try:
            embedding = np.asarray(
                embedding,
                dtype=np.float64
            )

            if (
                embedding.shape == (128,)
                and np.all(np.isfinite(embedding))
            ):
                X.append(embedding)
                Y.append(student_id)

        except (ValueError, TypeError):
            continue

    return {
        "clf": None,
        "X": X,
        "Y": Y
    }


def train_classifier():
    get_trained_model.clear()
    model_data = get_trained_model()

    return bool(model_data and model_data["X"])


def predict_attendance(class_image_np, threshold=0.58):
    detected_student = {}

    if threshold <= 0:
        raise ValueError("Threshold must be greater than 0.")

    model_data = get_trained_model()

    X_train = model_data.get("X", [])
    y_train = model_data.get("Y", [])

    all_students = sorted(set(y_train), key=str)

    encodings = get_face_embeddings(class_image_np)

    if not encodings or not X_train:
        return {}, all_students, len(encodings)

    X_train = np.asarray(X_train, dtype=np.float64)

    for encoding in encodings:
        distances = np.linalg.norm(
            X_train - encoding,
            axis=1
        )

        best_index = int(np.argmin(distances))
        best_dist = float(distances[best_index])
        best_id = y_train[best_index]

        if best_dist <= threshold:
            detected_student[best_id] = True

    return detected_student, all_students, len(encodings)


def recognize_faces_in_image(
    image_np,
    candidate_students=None,
    threshold=0.58
):
    if threshold <= 0:
        raise ValueError("Threshold must be greater than 0.")

    if candidate_students is None:
        candidate_students = get_all_students() or []

    valid_candidates = []

    for student in candidate_students:
        embedding = student.get("face_embedding")
        student_id = student.get("student_id")

        if embedding is None or student_id is None:
            continue

        try:
            arr = np.asarray(
                embedding,
                dtype=np.float64
            )

            if (
                arr.shape == (128,)
                and np.all(np.isfinite(arr))
            ):
                valid_candidates.append({
                    "student_id": student_id,
                    "name": student.get("name", "Unknown"),
                    "embedding": arr
                })

        except (ValueError, TypeError):
            continue

    detections = get_faces_with_boxes(image_np)

    matches = {}
    detection_items = []
    unknown_count = 0

    for detection in detections:
        box = detection["box"]
        encoding = detection["encoding"]

        best_student = None
        best_distance = float("inf")

        for candidate in valid_candidates:
            dist = float(
                np.linalg.norm(
                    candidate["embedding"] - encoding
                )
            )

            if dist < best_distance:
                best_distance = dist
                best_student = candidate

        if (
            best_student is not None
            and best_distance <= threshold
        ):
            student_id = best_student["student_id"]

            confidence = max(
                10,
                min(
                    99,
                    int(
                        round(
                            (1.0 - best_distance / threshold) * 40 + 60
                        )
                    )
                )
            )

            item = {
                "student_id": student_id,
                "name": best_student["name"],
                "distance": round(best_distance, 3),
                "confidence": confidence,
                "box": box,
                "is_recognized": True
            }

            if (
                student_id not in matches
                or confidence > matches[student_id]["confidence"]
            ):
                matches[student_id] = item

            detection_items.append(item)

        else:
            unknown_count += 1

            detection_items.append({
                "student_id": None,
                "name": "Unknown",
                "distance": (
                    round(best_distance, 3)
                    if best_student is not None
                    else None
                ),
                "confidence": 0,
                "box": box,
                "is_recognized": False
            })

    return {
        "matches": matches,
        "unknown_count": unknown_count,
        "total_detected": len(detections),
        "detections": detection_items
    }


def draw_detection_boxes(image_np, detection_items):
    image_np = np.ascontiguousarray(
        image_np,
        dtype=np.uint8
    )

    pil_img = Image.fromarray(image_np).copy()
    draw = ImageDraw.Draw(pil_img)

    for item in detection_items:
        left, top, right, bottom = item["box"]

        is_recognized = item.get(
            "is_recognized",
            False
        )

        box_color = (
            (22, 163, 74)
            if is_recognized
            else (220, 38, 38)
        )

        for thickness in range(3):
            draw.rectangle(
                [
                    left - thickness,
                    top - thickness,
                    right + thickness,
                    bottom + thickness
                ],
                outline=box_color
            )

        name = item.get("name", "Unknown")
        confidence = item.get("confidence", 0)

        label = (
            f"{name} ({confidence}% match score)"
            if is_recognized
            else "Unknown Face"
        )

        label_height = 22
        label_width = len(label) * 8 + 12
        label_top = max(0, top - label_height)

        draw.rectangle(
            [
                left,
                label_top,
                left + label_width,
                top
            ],
            fill=box_color
        )

        draw.text(
            (
                left + 6,
                max(2, label_top + 3)
            ),
            label,
            fill=(255, 255, 255)
        )

    return pil_img
