
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "outputs" / "context_memory.db"

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_memory():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS project_memory (
                id TEXT PRIMARY KEY,
                project_name TEXT NOT NULL,
                prompt TEXT NOT NULL,
                requirements TEXT,
                plan TEXT,
                outcome TEXT,
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_embeddings (
                project_id TEXT PRIMARY KEY,
                embedding TEXT NOT NULL,
                FOREIGN KEY(project_id)
                    REFERENCES project_memory(id)
                    ON DELETE CASCADE
            )
        """)


def _project_text(project_name, prompt, requirements, plan):
    return " ".join([
        str(project_name),
        str(prompt),
        json.dumps(requirements, ensure_ascii=False),
        json.dumps(plan, ensure_ascii=False),
    ])


def save_project_memory(prompt, requirements, plan, outcome):
    initialize_memory()

    project_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    project_name = str(
        requirements.get("project_name", "Untitled Project")
    )

    searchable_text = _project_text(
        project_name, prompt, requirements, plan
    )

    embedding = _get_model().encode(
        searchable_text,
        normalize_embeddings=True
    ).tolist()

    with _connect() as conn:
        conn.execute("""
            INSERT INTO project_memory
            (id, project_name, prompt, requirements, plan, outcome, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            project_name,
            prompt[:4000],
            json.dumps(requirements, ensure_ascii=False),
            json.dumps(plan, ensure_ascii=False),
            json.dumps(outcome, ensure_ascii=False),
            created_at,
        ))

        conn.execute("""
            INSERT INTO memory_embeddings (project_id, embedding)
            VALUES (?, ?)
        """, (project_id, json.dumps(embedding)))

    return project_id


def retrieve_relevant_memory(query, limit=5):
    initialize_memory()

    query_embedding = _get_model().encode(
        str(query),
        normalize_embeddings=True
    )

    with _connect() as conn:
        rows = conn.execute("""
            SELECT p.id, p.project_name, p.prompt, p.requirements,
                   p.plan, p.outcome, p.created_at, e.embedding
            FROM project_memory p
            LEFT JOIN memory_embeddings e ON p.id = e.project_id
            ORDER BY p.created_at DESC
            LIMIT 100
        """).fetchall()

    results = []

    for row in rows:
        if not row["embedding"]:
            continue

        stored_embedding = np.array(
            json.loads(row["embedding"]),
            dtype=np.float32
        )

        score = float(np.dot(query_embedding, stored_embedding))

        results.append({
            "id": row["id"],
            "project_name": row["project_name"],
            "prompt": row["prompt"],
            "requirements": json.loads(row["requirements"] or "{}"),
            "plan": json.loads(row["plan"] or "{}"),
            "outcome": json.loads(row["outcome"] or "{}"),
            "created_at": row["created_at"],
            "relevance_score": round(score, 4),
        })

    results.sort(
        key=lambda item: (
            item["relevance_score"],
            item["created_at"]
        ),
        reverse=True,
    )

    return results[:max(1, min(limit, 10))]


def get_recent_projects(limit=10):
    initialize_memory()

    with _connect() as conn:
        rows = conn.execute("""
            SELECT id, project_name, outcome, created_at
            FROM project_memory
            ORDER BY created_at DESC
            LIMIT ?
        """, (max(1, min(limit, 50)),)).fetchall()

    return [
        {
            "id": row["id"],
            "project_name": row["project_name"],
            "outcome": json.loads(row["outcome"] or "{}"),
            "created_at": row["created_at"],
        }
        for row in rows
    ]

def backfill_missing_embeddings():
    initialize_memory()

    with _connect() as conn:
        rows = conn.execute("""
            SELECT p.id, p.project_name, p.prompt,
                   p.requirements, p.plan
            FROM project_memory p
            LEFT JOIN memory_embeddings e ON p.id = e.project_id
            WHERE e.project_id IS NULL
        """).fetchall()

    if not rows:
        print("All projects already have embeddings.")
        return 0

    model = _get_model()
    saved = 0

    for row in rows:
        requirements = json.loads(row["requirements"] or "{}")
        plan = json.loads(row["plan"] or "{}")

        searchable_text = _project_text(
            row["project_name"],
            row["prompt"],
            requirements,
            plan
        )

        embedding = model.encode(
            searchable_text,
            normalize_embeddings=True
        ).tolist()

        with _connect() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO memory_embeddings
                (project_id, embedding)
                VALUES (?, ?)
            """, (row["id"], json.dumps(embedding)))

        saved += 1

    print(f"Backfill complete: {saved} projects updated.")
    return saved
