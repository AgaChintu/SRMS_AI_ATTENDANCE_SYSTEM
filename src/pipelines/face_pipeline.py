
import dlib
import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
import face_recognition_models
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
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

    image_np = np.ascontiguousarray(image_np, dtype=np.uint8)
    faces = detector(image_np, 2)

    encodings = []

    for face in faces:
        shape = sp(image_np, face)
        face_descriptor = facerec.compute_face_descriptor(
            image_np, shape, 3
        )

        encodings.append(
            np.array(face_descriptor, dtype=np.float64)
        )

    return encodings


def get_faces_with_boxes(image_np):
    detector, sp, facerec = load_dlib_models()

    image_np = np.ascontiguousarray(image_np, dtype=np.uint8)
    faces = detector(image_np, 2)

    results = []

    for face in faces:
        shape = sp(image_np, face)

        face_descriptor = facerec.compute_face_descriptor(
            image_np, shape, 2
        )

        results.append({
            "box": (
                face.left(),
                face.top(),
                face.right(),
                face.bottom()
            ),
            "encoding": np.array(
                face_descriptor,
                dtype=np.float64
            )
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

        if embedding is not None and student_id is not None:
            embedding = np.asarray(
                embedding,
                dtype=np.float64
            )

            if embedding.shape == (128,):
                X.append(embedding)
                Y.append(student_id)

    if not X:
        return None

    unique_students = set(Y)

    if len(unique_students) < 2:
        return {
            "clf": None,
            "X": X,
            "Y": Y
        }

    base_model = SVC(
        kernel="rbf",
        class_weight="balanced"
    )

    clf = CalibratedClassifierCV(
        estimator=base_model,
        method="sigmoid",
        cv=2
    )

    try:
        clf.fit(X, Y)

    except ValueError as e:
        st.error(f"Model training failed: {e}")
        return None

    return {
        "clf": clf,
        "X": X,
        "Y": Y
    }


def train_classifier():
    get_trained_model.clear()
    model_data = get_trained_model()

    return model_data is not None


def predict_attendance(class_image_np, threshold=0.58):
    detected_student = {}

    model_data = get_trained_model()

    if not model_data:
        students = get_all_students() or []

        X_train = []
        y_train = []

        for student in students:
            embedding = student.get("face_embedding")
            student_id = student.get("student_id")

            if embedding is not None and student_id is not None:
                arr = np.asarray(
                    embedding,
                    dtype=np.float64
                )

                if arr.shape == (128,):
                    X_train.append(arr)
                    y_train.append(student_id)

    else:
        X_train = model_data.get("X", [])
        y_train = model_data.get("Y", [])

    all_students = sorted(set(y_train), key=str)

    encodings = get_face_embeddings(class_image_np)

    if not encodings or not X_train:
        return {}, all_students, len(encodings)

    for encoding in encodings:
        best_id = None
        best_dist = float("inf")

        for i, stored_emb in enumerate(X_train):
            dist = np.linalg.norm(
                stored_emb - encoding
            )

            if dist < best_dist:
                best_dist = dist
                best_id = y_train[i]

        if best_dist <= threshold and best_id is not None:
            detected_student[best_id] = True

    return detected_student, all_students, len(encodings)


def recognize_faces_in_image(
    image_np,
    candidate_students=None,
    threshold=0.58
):
    if candidate_students is None:
        candidate_students = get_all_students() or []

    valid_candidates = []

    for student in candidate_students:
        embedding = student.get("face_embedding")

        if embedding is not None:
            arr = np.asarray(
                embedding,
                dtype=np.float64
            )

            if arr.shape == (128,):
                valid_candidates.append({
                    "student_id": student.get("student_id"),
                    "name": student.get("name", "Unknown"),
                    "embedding": arr
                })

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

        if best_student and best_distance <= threshold:
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
                    if best_student else None
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
            f"{name} ({confidence}%)"
            if is_recognized
            else "Unknown Face"
        )

        label_height = 22
        label_width = len(label) * 8 + 12

        draw.rectangle(
            [
                left,
                max(0, top - label_height),
                left + label_width,
                top
            ],
            fill=box_color
        )

        draw.text(
            (
                left + 6,
                max(2, top - label_height + 3)
            ),
            label,
            fill=(255, 255, 255)
        )

    return pil_img
