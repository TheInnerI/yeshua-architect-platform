"""SQLite database for Yeshua Architect Platform."""

import aiosqlite
import hashlib
import time
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "platform.db"


async def get_db() -> aiosqlite.Connection:
    """Get async SQLite connection."""
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    """Initialize database tables."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await get_db()

    await db.executescript("""
        CREATE TABLE IF NOT EXISTS agent_requests (
            id TEXT PRIMARY KEY,
            agent_name TEXT NOT NULL,
            purpose TEXT NOT NULL,
            audience TEXT,
            problem_solved TEXT,
            boundaries TEXT,
            desired_fruit TEXT,
            monetization_model TEXT,
            jesus_anchor TEXT,
            tools_requested TEXT,
            tone TEXT,
            tier TEXT DEFAULT 'free',
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS agent_audits (
            id TEXT PRIMARY KEY,
            agent_request_id TEXT REFERENCES agent_requests(id),
            truth_score REAL,
            neighbor_score REAL,
            fruit_score REAL,
            mammon_score REAL,
            service_score REAL,
            composite_five REAL,
            life_score REAL,
            agency_score REAL,
            dignity_score REAL,
            coherence_score REAL,
            boundary_score REAL,
            receipt_score REAL,
            composite_seven REAL,
            grade TEXT,
            verdict TEXT,
            correction_notes TEXT,
            poa_receipt_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            agent_request_id TEXT REFERENCES agent_requests(id),
            name TEXT NOT NULL,
            system_prompt TEXT,
            boundaries TEXT,
            example_interactions TEXT,
            deployment_notes TEXT,
            tier TEXT,
            delivery_path TEXT,
            policy_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS receipts (
            id TEXT PRIMARY KEY,
            agent_request_id TEXT,
            agent_id TEXT,
            receipt_type TEXT,
            coherence_score REAL,
            hmac_signature TEXT,
            chain_index INTEGER,
            arweave_tx TEXT,
            raw_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS payments (
            id TEXT PRIMARY KEY,
            agent_request_id TEXT,
            gumroad_product_id TEXT,
            amount INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS observer_events (
            id TEXT PRIMARY KEY,
            agent_request_id TEXT,
            event_type TEXT,
            payload TEXT,
            mio_observation_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    await db.commit()
    await db.close()


def make_id(prefix: str = "") -> str:
    """Generate a unique ID from timestamp + random."""
    raw = f"{prefix}{time.time()}{id(object())}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
