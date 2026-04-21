import os
import sqlite3
from utils.path_tool import get_project_root

DB_PATH = os.path.join(get_project_root(), "data", "external", "data.db")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS user_info (
            user_id    TEXT PRIMARY KEY,
            password   TEXT NOT NULL,
            city       TEXT NOT NULL,
            email      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS login_records (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    TEXT NOT NULL,
            login_time TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_login_time ON login_records(login_time);

        CREATE TABLE IF NOT EXISTS records (
            user_id    TEXT NOT NULL,
            feature    TEXT,
            efficiency TEXT,
            consumables TEXT,
            comparison TEXT,
            time       TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_records_user_time ON records(user_id, time);

        CREATE TABLE IF NOT EXISTS city (
            areacode   TEXT PRIMARY KEY,
            province   TEXT,
            city       TEXT,
            district   TEXT,
            eng        TEXT,
            pinyin     TEXT,
            lon        REAL,
            lat        REAL,
            exclude    INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_city_district ON city(district);
        CREATE INDEX IF NOT EXISTS idx_city_name ON city(city);

        CREATE TABLE IF NOT EXISTS repairman_info (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT NOT NULL,
            phone     TEXT NOT NULL,
            expertise TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()
