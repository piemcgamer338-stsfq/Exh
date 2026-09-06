# database.py

import sqlite3

DB = "data.db"


def connect():
    return sqlite3.connect(DB)


def setup():

    db = connect()
    cur = db.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER UNIQUE,
            ticket_number INTEGER,
            user_id INTEGER,
            exchange_type TEXT,
            sending_currency TEXT,
            payment_method TEXT,
            sending_crypto TEXT,
            receiving_crypto TEXT,
            amount REAL,
            claimed_by INTEGER,
            closed INTEGER DEFAULT 0
        )
    """)

    db.commit()
    db.close()


def get_setting(key):

    db = connect()
    cur = db.cursor()

    cur.execute(
        "SELECT value FROM settings WHERE key=?",
        (key,)
    )

    result = cur.fetchone()

    db.close()

    return result[0] if result else None


def set_setting(key, value):

    db = connect()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO settings(key, value)
        VALUES(?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value=excluded.value
    """, (key, str(value)))

    db.commit()
    db.close()


def create_ticket(
    channel_id,
    ticket_number,
    user_id,
    exchange_type,
    sending_currency,
    payment_method,
    sending_crypto,
    receiving_crypto,
    amount
):

    db = connect()
    cur = db.cursor()

    cur.execute("""
        INSERT INTO tickets (
            channel_id,
            ticket_number,
            user_id,
            exchange_type,
            sending_currency,
            payment_method,
            sending_crypto,
            receiving_crypto,
            amount
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        channel_id,
        ticket_number,
        user_id,
        exchange_type,
        sending_currency,
        payment_method,
        sending_crypto,
        receiving_crypto,
        amount
    ))

    db.commit()
    db.close()


def get_ticket(channel_id):

    db = connect()
    cur = db.cursor()

    cur.execute(
        "SELECT * FROM tickets WHERE channel_id=?",
        (channel_id,)
    )

    result = cur.fetchone()

    db.close()

    return result


def claim_ticket(channel_id, staff_id):

    db = connect()
    cur = db.cursor()

    cur.execute("""
        UPDATE tickets
        SET claimed_by=?
        WHERE channel_id=?
    """, (staff_id, channel_id))

    db.commit()
    db.close()


def close_ticket(channel_id):

    db = connect()
    cur = db.cursor()

    cur.execute("""
        UPDATE tickets
        SET closed=1
        WHERE channel_id=?
    """, (channel_id,))

    db.commit()
    db.close()


def reopen_ticket(channel_id):

    db = connect()
    cur = db.cursor()

    cur.execute("""
        UPDATE tickets
        SET closed=0
        WHERE channel_id=?
    """, (channel_id,))

    db.commit()
    db.close()
