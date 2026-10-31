
from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np
import io
import streamlit as st
import librosa
from src.database.db import get_all_students


@st.cache_resource
def load_voice_encoder():
    return VoiceEncoder()


def get_voice_embedding(audio_bytes):
    """
    Computes a 256-d voice embedding from audio_bytes (WAV, MP3, etc.).
    Returns a list of floats.
    """
    try:
        encoder = load_voice_encoder()
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
        wav = preprocess_wav(audio)
        embedding = encoder.embed_utterance(wav)
        return embedding.tolist()
    except Exception as e:
        print(f"Voice embedding error: {e}")
        return None


def identify_speaker(new_embedding, candidates_dict, threshold=0.65):
    """
    Identifies speaker by comparing new_embedding with candidates_dict.
    candidates_dict: {student_id: [embedding_floats] or np.array}
    Returns: (best_sid, best_score)
    """
    if new_embedding is None or not candidates_dict:
        return None, 0.0

    new_emb = np.asarray(new_embedding, dtype=np.float32)
    norm = np.linalg.norm(new_emb)
    if norm > 0:
        new_emb = new_emb / norm

    best_sid = None
    best_score = -1.0

    for sid, stored_embedding in candidates_dict.items():
        if stored_embedding:
            cand_emb = np.asarray(stored_embedding, dtype=np.float32)
            c_norm = np.linalg.norm(cand_emb)
            if c_norm > 0:
                cand_emb = cand_emb / c_norm

            similarity = float(np.dot(new_emb, cand_emb))
            if similarity > best_score:
                best_score = similarity
                best_sid = sid

    if best_score >= threshold:
        return best_sid, best_score

    return None, best_score


def process_bulk_audio(audio_bytes, candidates_dict, threshold=0.65):
    """
    Segments long audio and identifies all active speakers.
    """
    try:
        encoder = load_voice_encoder()
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
        segments = librosa.effects.split(audio, top_db=30)

        identified_results = {}

        # If audio is short, process whole audio directly
        if len(segments) == 0:
            wav = preprocess_wav(audio)
            emb = encoder.embed_utterance(wav)
            sid, score = identify_speaker(emb, candidates_dict, threshold)
            if sid:
                identified_results[sid] = score
            return identified_results

        for start, end in segments:
            if (end - start) < sr * 0.4:  # skip segments shorter than 0.4s
                continue
            segment_audio = audio[start:end]
            wav = preprocess_wav(segment_audio)
            embedding = encoder.embed_utterance(wav)

            sid, score = identify_speaker(embedding, candidates_dict, threshold)
            if sid:
                if sid not in identified_results or score > identified_results[sid]:
                    identified_results[sid] = score

        return identified_results
    except Exception as e:
        print(f"Bulk voice process error: {e}")
        return {}


def recognize_voices_in_audio(audio_bytes, candidate_students=None, threshold=0.65):
    """
    Comprehensive voice recognition for teacher attendance and student verification.
    candidate_students: list of student dicts [{'student_id': ..., 'name': ..., 'voice_embedding': [...]}]
    """
    if candidate_students is None:
        candidate_students = get_all_students() or []

    candidates_dict = {}
    names_dict = {}

    for c in candidate_students:
        sid = c.get("student_id")
        v_emb = c.get("voice_embedding")
        name = c.get("name", "Student")
        if sid and v_emb:
            candidates_dict[sid] = v_emb
            names_dict[sid] = name

    if not candidates_dict:
        return {
            "matches": {},
            "total_candidates": 0,
            "message": "No students in this list have enrolled their voice yet."
        }

    raw_matches = process_bulk_audio(audio_bytes, candidates_dict, threshold=threshold)

    results = {}
    for sid, score in raw_matches.items():
        conf = max(10, min(99, int(round((score - threshold) / (1.0 - threshold) * 40 + 60))))
        results[sid] = {
            "student_id": sid,
            "name": names_dict.get(sid, f"Student {sid}"),
            "similarity": round(float(score), 3),
            "confidence": conf
        }

    return {
        "matches": results,
        "total_candidates": len(candidates_dict),
        "message": f"Identified {len(results)} student voice(s)."
    }
