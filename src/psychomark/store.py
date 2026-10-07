"""Local SQLite persistence with immutable extraction/exam snapshots per copy."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


class Conflict(ValueError):
    pass


class Store:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self.path = root / "psychomark.sqlite3"
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS exams (
                    id TEXT PRIMARY KEY, revision INTEGER NOT NULL, payload TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS copies (
                    id TEXT PRIMARY KEY, exam_id TEXT NOT NULL REFERENCES exams(id),
                    exam_revision INTEGER NOT NULL, exam_snapshot TEXT NOT NULL, layout TEXT NOT NULL,
                    filename TEXT NOT NULL, page INTEGER NOT NULL, extraction TEXT NOT NULL,
                    reviews TEXT NOT NULL, revision INTEGER NOT NULL, created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS copies_exam ON copies(exam_id);
                CREATE TABLE IF NOT EXISTS review_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, copy_id TEXT NOT NULL REFERENCES copies(id),
                    revision INTEGER NOT NULL, section TEXT NOT NULL, question INTEGER NOT NULL,
                    previous TEXT, decision TEXT NOT NULL, created_at TEXT NOT NULL
                );
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def exam_record(row):
        return {
            "id": row["id"],
            "revision": row["revision"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "exam": json.loads(row["payload"]),
        }

    def list_exams(self):
        with self.connection() as db:
            rows = db.execute(
                "SELECT e.*, (SELECT COUNT(*) FROM copies c WHERE c.exam_id=e.id) AS copy_count FROM exams e ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(self.exam_record(row), copy_count=row["copy_count"]) for row in rows]

    def get_exam(self, identifier):
        with self.connection() as db:
            row = db.execute("SELECT * FROM exams WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise KeyError(identifier)
        return self.exam_record(row)

    def create_exam(self, payload):
        identifier, timestamp = uuid.uuid4().hex, now()
        with self.connection() as db:
            db.execute(
                "INSERT INTO exams VALUES (?,1,?,?,?)",
                (identifier, json.dumps(payload), timestamp, timestamp),
            )
        return self.get_exam(identifier)

    def update_exam(self, identifier, payload, expected_revision):
        with self.connection() as db:
            changed = db.execute(
                "UPDATE exams SET payload=?, revision=revision+1, updated_at=? WHERE id=? AND revision=?",
                (json.dumps(payload), now(), identifier, expected_revision),
            ).rowcount
            if not changed:
                raise Conflict("Cet examen a changé. Recharge la page avant de l’enregistrer.")
        return self.get_exam(identifier)

    def create_copy(self, identifier, exam, layout, filename, page, extraction):
        with self.connection() as db:
            db.execute(
                "INSERT INTO copies VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    identifier,
                    exam["id"],
                    exam["revision"],
                    json.dumps(exam["exam"]),
                    json.dumps(layout),
                    filename,
                    page,
                    json.dumps(extraction),
                    "{}",
                    1,
                    now(),
                ),
            )

    def get_copy(self, identifier):
        with self.connection() as db:
            row = db.execute("SELECT * FROM copies WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise KeyError(identifier)
        item = dict(row)
        for field in ["exam_snapshot", "layout", "extraction", "reviews"]:
            item[field] = json.loads(item[field])
        return item

    def copy_ids(self, exam_id):
        with self.connection() as db:
            return [
                row[0]
                for row in db.execute(
                    "SELECT id FROM copies WHERE exam_id=? ORDER BY created_at DESC", (exam_id,)
                )
            ]

    def review(self, identifier, review):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT reviews, revision FROM copies WHERE id=?", (identifier,)
            ).fetchone()
            if row is None:
                raise KeyError(identifier)
            if row["revision"] != review.expected_revision:
                raise Conflict(
                    "Cette copie a changé. Recharge-la avant de poursuivre la vérification."
                )
            reviews = json.loads(row["reviews"])
            key = f"{review.section}:{review.question}"
            previous = reviews.get(key)
            decision = {"decision": review.decision, "answer": review.answer, "reviewed_at": now()}
            if review.decision == "automatic":
                reviews.pop(key, None)
            else:
                reviews[key] = decision
            db.execute(
                "UPDATE copies SET reviews=?, revision=revision+1 WHERE id=?",
                (json.dumps(reviews), identifier),
            )
            db.execute(
                "INSERT INTO review_events(copy_id,revision,section,question,previous,decision,created_at) VALUES(?,?,?,?,?,?,?)",
                (
                    identifier,
                    row["revision"] + 1,
                    review.section,
                    review.question,
                    json.dumps(previous),
                    json.dumps(decision),
                    now(),
                ),
            )

    def history(self, identifier):
        with self.connection() as db:
            rows = db.execute(
                "SELECT revision,section,question,previous,decision,created_at FROM review_events WHERE copy_id=? ORDER BY revision",
                (identifier,),
            ).fetchall()
        return [
            {
                **dict(row),
                "previous": json.loads(row["previous"]),
                "decision": json.loads(row["decision"]),
            }
            for row in rows
        ]
