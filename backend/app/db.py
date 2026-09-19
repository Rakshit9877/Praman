import sqlite3
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = os.getenv("DB_PATH", "backend/praman.db")

def _get_conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _get_conn()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS docs (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            data JSON NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_doc(doc_id: str, doc_type: str, data: Dict[str, Any]):
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO docs (id, type, data) VALUES (?, ?, ?)",
        (doc_id, doc_type, json.dumps(data))
    )
    conn.commit()
    conn.close()

def get_doc(doc_id: str) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.execute("SELECT data FROM docs WHERE id = ?", (doc_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return json.loads(row["data"])
    return None

def get_docs_by_type(doc_type: str) -> List[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.execute("SELECT data FROM docs WHERE type = ?", (doc_type,))
    rows = cur.fetchall()
    conn.close()
    return [json.loads(row["data"]) for row in rows]

def delete_all():
    conn = _get_conn()
    conn.execute("DELETE FROM docs")
    conn.commit()
    conn.close()

# Initialize DB on import
init_db()
