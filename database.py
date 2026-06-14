"""
Database module for Moodie Foodie.
Auto-detects MySQL — falls back to SQLite if MySQL is unavailable.
All queries use %s placeholders (MySQL style); the SQLite wrapper translates them.
"""
import os
import sqlite3
import sys

# ─── Try MySQL first ────────────────────────────────────────────
USE_MYSQL = False
try:
    import mysql.connector
    from mysql.connector import pooling

    MYSQL_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '',           # ← Change to your MySQL root password
        'database': 'moodie_foodie',
        'port': 3306,
    }
    # Quick connectivity test
    _test = mysql.connector.connect(
        host=MYSQL_CONFIG['host'],
        user=MYSQL_CONFIG['user'],
        password=MYSQL_CONFIG['password'],
        port=MYSQL_CONFIG['port'],
    )
    _test.close()
    USE_MYSQL = True
    print("[OK] MySQL detected - using MySQL backend.")
except Exception:
    print("[WARN] MySQL not available - using SQLite fallback.")

# ─── MySQL pool (lazy) ──────────────────────────────────────────
_pool = None

def _get_mysql_pool():
    global _pool
    if _pool is None:
        # Ensure database exists
        cfg = {k: v for k, v in MYSQL_CONFIG.items() if k != 'database'}
        conn = mysql.connector.connect(**cfg)
        cur = conn.cursor()
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{MYSQL_CONFIG['database']}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        cur.close()
        conn.close()
        _pool = pooling.MySQLConnectionPool(
            pool_name="moodie_pool", pool_size=5,
            pool_reset_session=True, **MYSQL_CONFIG
        )
    return _pool

# ─── SQLite path ────────────────────────────────────────────────
def get_sqlite_path():
    """Ensure the database lives next to the .exe for persistence."""
    filename = 'moodie_foodie.db'
    if getattr(sys, 'frozen', False):
        # Directory where the .exe is located
        base_dir = os.path.dirname(sys.executable)
        local_path = os.path.join(base_dir, filename)
        
        # If the DB doesn't exist in the exe folder, check if we bundled a default one
        if not os.path.exists(local_path):
            meipass_path = os.path.join(sys._MEIPASS, filename)
            if os.path.exists(meipass_path):
                import shutil
                try:
                    shutil.copy(meipass_path, local_path)
                except Exception:
                    return meipass_path # Fallback to temp if copy fails
        return local_path
    else:
        return os.path.abspath(filename)

SQLITE_PATH = get_sqlite_path()


# ─── Unified connection wrapper ─────────────────────────────────
class _SQLiteWrapper:
    """Wraps a SQLite connection so it behaves like mysql.connector."""

    def __init__(self):
        self.conn = sqlite3.connect(SQLITE_PATH)
        self.conn.row_factory = sqlite3.Row  # dict-like rows

    def cursor(self):
        return _SQLiteCursorWrapper(self.conn.cursor())

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


class _SQLiteCursorWrapper:
    """Translates %s → ? and exposes .description / .lastrowid."""

    def __init__(self, cursor):
        self._cur = cursor
        self.description = None
        self.lastrowid = None

    def execute(self, query, params=None):
        import re
        # Translate MySQL-style %s to SQLite ?
        query = query.replace('%s', '?')
        # Translate MySQL 'INT AUTO_INCREMENT PRIMARY KEY' →
        #   SQLite 'INTEGER PRIMARY KEY AUTOINCREMENT'
        query = re.sub(
            r'INT\s+AUTO_INCREMENT\s+PRIMARY\s+KEY',
            'INTEGER PRIMARY KEY AUTOINCREMENT',
            query,
            flags=re.IGNORECASE
        )
        query = query.replace('ENGINE=InnoDB', '')
        query = query.replace('TINYINT(1)', 'INTEGER')
        query = query.replace('VARCHAR(100)', 'TEXT')
        query = query.replace('VARCHAR(255)', 'TEXT')
        query = query.replace('VARCHAR(200)', 'TEXT')
        query = query.replace('VARCHAR(50)', 'TEXT')
        query = query.replace('VARCHAR(20)', 'TEXT')
        query = query.replace('CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci', '')
        # Remove FOREIGN KEY constraints for SQLite simplicity
        if 'FOREIGN KEY' in query:
            lines = query.split('\n')
            lines = [l for l in lines if 'FOREIGN KEY' not in l]
            query = '\n'.join(lines)
            # Clean trailing comma before closing paren (handles whitespace/newlines)
            query = re.sub(r',\s*\)', '\n)', query)

        if params:
            self._cur.execute(query, params)
        else:
            self._cur.execute(query)

        self.description = self._cur.description
        self.lastrowid = self._cur.lastrowid

    def fetchone(self):
        row = self._cur.fetchone()
        if row and self.description:
            # Return as tuple (like mysql.connector default)
            return tuple(row)
        return row

    def fetchall(self):
        rows = self._cur.fetchall()
        if rows and self.description:
            return [tuple(r) for r in rows]
        return rows

    def close(self):
        self._cur.close()


def get_db_connection():
    """Return a database connection (MySQL or SQLite)."""
    if USE_MYSQL:
        return _get_mysql_pool().get_connection()
    else:
        return _SQLiteWrapper()


def init_db():
    """Create all required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            username        VARCHAR(100) UNIQUE NOT NULL,
            password        VARCHAR(255) NOT NULL,
            age             INT DEFAULT 25,
            personality     VARCHAR(50)  DEFAULT 'Ambivert',
            diet_type       VARCHAR(50)  DEFAULT 'Non-Vegetarian',
            spice_level     INT          DEFAULT 3,
            sweet_tooth     INT          DEFAULT 3,
            cuisine_pref    VARCHAR(50)  DEFAULT 'Indian',
            health_conscious TINYINT(1)  DEFAULT 0,
            allergies       VARCHAR(255) DEFAULT '',
            role            VARCHAR(20)  DEFAULT 'user',
            created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)

    # Ensure columns exist for existing databases
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN allergies VARCHAR(255) DEFAULT ''")
    except Exception: pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'")
    except Exception: pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id                  INT AUTO_INCREMENT PRIMARY KEY,
            user_id             INT NOT NULL,
            mood                VARCHAR(50),
            mood_intensity      INT,
            recommended_primary VARCHAR(200),
            rating              INT DEFAULT 0,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mood_logs (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            user_id         INT NOT NULL,
            mood            VARCHAR(50),
            mood_intensity  INT,
            time_of_day     VARCHAR(20),
            weather         VARCHAR(20),
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questionnaire (
            user_id         INT PRIMARY KEY,
            q1 VARCHAR(255), q2 VARCHAR(255), q3 VARCHAR(255), q4 VARCHAR(255), q5 VARCHAR(255),
            q6 VARCHAR(255), q7 VARCHAR(255), q8 VARCHAR(255), q9 VARCHAR(255), q10 VARCHAR(255),
            q11 VARCHAR(255), q12 VARCHAR(255), q13 VARCHAR(255), q14 VARCHAR(255), q15 VARCHAR(255),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB
    """)

    # Seed default admin user if not exists
    cursor.execute("SELECT id FROM users WHERE username = %s", ("admin",))
    if not cursor.fetchone():
        cursor.execute(
            """INSERT INTO users (username, password, role, age, personality, diet_type, cuisine_pref)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            ("admin", "admin123", "admin", 30, "Adventurous", "Non-Vegetarian", "Continental")
        )
        print("[OK] Default admin user created.")

    conn.commit()
    cursor.close()
    conn.close()
    db_type = "MySQL" if USE_MYSQL else "SQLite"
    print(f"[OK] Database tables created successfully ({db_type}).")
    # Initial export
    export_users_to_csv()


def export_users_to_csv():
    """Automatically export all user data to users_data.csv."""
    try:
        import csv
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get data
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        
        # Get headers
        if USE_MYSQL:
            headers = [desc[0] for desc in cursor.description]
        else:
            # For our SQLite wrapper, description is available after execute
            headers = [desc[0] for desc in cursor.description]

        # Use current directory for the CSV (next to the .exe if frozen)
        if getattr(sys, 'frozen', False):
            csv_dir = os.path.dirname(sys.executable)
        else:
            csv_dir = os.path.abspath(".")
        csv_path = os.path.join(csv_dir, "users_data.csv")
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
            
        cursor.close()
        conn.close()
        print(f"[OK] User data automatically exported to {csv_path}")
    except Exception as e:
        print(f"[ERR] Auto-export failed: {e}")


if __name__ == '__main__':
    init_db()
