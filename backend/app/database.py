import sqlite3
import os

# Path to the database file
DB_PATH = os.path.abspath("C:\\netsecflow\\database\\netsecflow.db")

def init_db():
    """
    Initialize the settings and flows tables in the database if they do not exist.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Create the settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                key VARCHAR(50) UNIQUE NOT NULL,
                value VARCHAR(255) NOT NULL
            );
        ''')
        # Create the flows table with additional fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flows (
                id TEXT PRIMARY KEY,
                source_ip TEXT,
                destination_ip TEXT,
                protocol TEXT,
                bandwidth INTEGER,
                flow_duration INTEGER,
                priority INTEGER,
                app_id TEXT,
                device_id TEXT
            );
        ''')
        # Create the events table to store webhook data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                event TEXT NOT NULL,
                score INTEGER NOT NULL,
                source_ip TEXT NOT NULL,
                destination_ip TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        # Create the actions table to record actions taken
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actions (
                action_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                action_type TEXT NOT NULL,
                reason TEXT NOT NULL,
                source_ip TEXT NOT NULL,
                admin_or_automated TEXT NOT NULL
            );
        ''')
        conn.commit()

def delete_event_entry(source_ip):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events WHERE source_ip = ?", (source_ip,))
            conn.commit()
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")

def record_action(action_type, reason, source_ip, admin_or_automated):
    """
    Record an action taken to the actions table.

    Args:
        action_type (str): The type of action (e.g., block, redirect).
        reason (str): The reason for the action.
        source_ip (str): The source IP address related to the action.
        admin_or_automated (str): Whether the action was admin-initiated or automated.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO actions (action_type, reason, source_ip, admin_or_automated)
                VALUES (?, ?, ?, ?);
            ''', (
                action_type,
                reason,
                source_ip,
                admin_or_automated
            ))
            conn.commit()
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")
    
def get_actions():
    """
    Retrieve all actions from the actions table.

    Returns:
        list of dict: A list of dictionaries containing action data.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, action_type, reason, source_ip, admin_or_automated
                FROM actions
                ORDER BY timestamp DESC;
            ''')
            rows = cursor.fetchall()
            return [
                {
                    "timestamp": row[0],
                    "action_type": row[1],
                    "reason": row[2],
                    "source_ip": row[3],
                    "admin_or_automated": row[4]
                }
                for row in rows
            ]
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")

def save_event(data):
    """
    Save an event received from the webhook to the database.

    Args:
        data (dict): The event data to save.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO events (source, event, score, source_ip, destination_ip)
                VALUES (?, ?, ?, ?, ?);
            ''', (
                data.get("Source"),
                data.get("Event"),
                int(data.get("Score", 0)),
                data.get("SourceIP"),
                data.get("DestinationIP")
            ))
            conn.commit()
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")
    
def get_anomalies():
    """
    Retrieve recent anomalies from the events table.

    Returns:
        list of dict: A list of dictionaries containing anomaly data.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, source_ip, event, score
                FROM events
                ORDER BY timestamp DESC;
            ''')
            rows = cursor.fetchall()
            return [
                {
                    "timestamp": row[0],
                    "source_ip": row[1],
                    "event": row[2],
                    "score": row[3]
                }
                for row in rows
            ]
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")


def save_settings(settings):
    """
    Save or update settings in the database.

    Args:
        settings (dict): A dictionary of key-value pairs to be stored.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            for key, value in settings.items():
                cursor.execute('''
                    INSERT INTO settings (key, value)
                    VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value;
                ''', (key, value))
            conn.commit()
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")


def get_settings():
    """
    Retrieve all settings as a dictionary from the database.

    Returns:
        dict: A dictionary containing key-value pairs of settings.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings;")
            rows = cursor.fetchall()
            return {key: value for key, value in rows}
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")

def get_setting_value(key):
    """
    Retrieve a specific setting value by key from the database.

    Args:
        key (str): The key of the setting to retrieve.

    Returns:
        str: The value of the specified setting, or None if not found.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?;", (key,))
            row = cursor.fetchone()
            return row[0] if row else None
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")

def save_flows(flows):
    """
    Save or update flows data in the database.

    This function first clears the existing data in the flows table
    to ensure only current flow data is stored.

    Args:
        flows (list of dict): A list of dictionaries where each dictionary represents a flow.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Clear the existing flows data
            cursor.execute("DELETE FROM flows")

            # Insert the new flows data
            for flow in flows:
                cursor.execute('''
                    INSERT INTO flows (id, source_ip, destination_ip, protocol, bandwidth, flow_duration, priority, app_id, device_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    flow['id'],
                    flow.get('source_ip', 'Unknown'),
                    flow.get('destination_ip', 'Unknown'),
                    flow.get('protocol', 'Unknown'),
                    flow.get('bandwidth', 0),
                    flow.get('flow_duration', 0),
                    flow.get('priority', 0),
                    flow.get('app_id', 'Unknown'),
                    flow.get('device_id', 'Unknown')
                ))
            conn.commit()
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")

def get_flows():
    """
    Retrieve all flow data from the database.

    Returns:
        list of dict: A list of dictionaries containing flow data.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, source_ip, destination_ip, protocol, bandwidth, flow_duration, priority, app_id, device_id
                FROM flows;
            ''')
            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "source_ip": row[1],
                    "destination_ip": row[2],
                    "protocol": row[3],
                    "bandwidth": row[4],
                    "flow_duration": row[5],
                    "priority": row[6],
                    "app_id": row[7],
                    "device_id": row[8]
                }
                for row in rows
            ]
    except sqlite3.Error as e:
        raise Exception(f"Database error: {e}")
    

