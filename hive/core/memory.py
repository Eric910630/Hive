# hive/core/memory.py

import sqlite3
import os
from datetime import datetime
import json
import logging

# --- Configuration ---
DB_FILE = "hive_memory.db"
# For now, let's place the DB in the root of the project.
# We will make this path more robust later.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', DB_FILE)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CoreMemory:
    """
    The Core Memory component of Hive (v1.0).
    This initial version focuses on "Factual Memory" using SQLite.
    It is responsible for durable, structured data storage like logs,
    configurations, and agent invocation history.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CoreMemory, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_path=DB_PATH):
        """
        Initializes the CoreMemory, creating a connection to the SQLite database.
        The singleton pattern ensures only one connection is active.
        """
        if not hasattr(self, 'connection'): # Prevent re-initialization
            try:
                self.connection = sqlite3.connect(db_path, check_same_thread=False)
                self.connection.row_factory = sqlite3.Row # Access columns by name
                self.cursor = self.connection.cursor()
                logging.info(f"CoreMemory: Successfully connected to database at {db_path}")
                self._initialize_db()
            except sqlite3.Error as e:
                logging.error(f"CoreMemory: Database connection failed: {e}")
                raise

    def _initialize_db(self):
        """
        Ensures the necessary tables exist in the database.
        This is the schema for our 'Factual Memory'.
        """
        try:
            # Table for logging every agent invocation
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_invocations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                input_data TEXT,
                output_data TEXT,
                status TEXT NOT NULL CHECK(status IN ('SUCCESS', 'FAILURE')),
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration_ms INTEGER,
                error_message TEXT
            )
            ''')
            self.connection.commit()
            logging.info("CoreMemory: Database tables initialized successfully.")
        except sqlite3.Error as e:
            logging.error(f"CoreMemory: Failed to initialize tables: {e}")
            raise

    def close(self):
        """Closes the database connection."""
        if self.connection:
            self.connection.close()
            logging.info("CoreMemory: Database connection closed.")

    # --- Example method for future use ---
    def log_agent_invocation(self, session_id, agent_name, input_data, output_data, status, start_time, end_time, error_message=None):
        """
        Logs a record of an agent being called.
        """
        duration = int((end_time - start_time).total_seconds() * 1000)
        try:
            # 使用新的cursor避免递归问题
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute('''
                INSERT INTO agent_invocations (session_id, agent_name, input_data, output_data, status, start_time, end_time, duration_ms, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    agent_name,
                    json.dumps(input_data),
                    json.dumps(output_data),
                    status,
                    start_time,
                    end_time,
                    duration,
                    error_message
                ))
            self.connection.commit()
            logging.info(f"Logged invocation for agent: {agent_name}")
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            logging.error(f"Failed to log agent invocation for {agent_name}: {e}")
            return None

if __name__ == '__main__':
    # A simple self-test to verify functionality when run directly
    print("Running CoreMemory self-test...")
    try:
        memory = CoreMemory()
        print("Initialization successful.")

        # Test logging
        session = "test_session_123"
        agent = "TestAgent"
        inp = {"task": "hello"}
        out = {"result": "world"}
        start = datetime.now()
        end = datetime.now()
        
        print(f"Attempting to log a test invocation for '{agent}'...")
        log_id = memory.log_agent_invocation(session, agent, inp, out, "SUCCESS", start, end)

        if log_id:
            print(f"Successfully logged invocation with ID: {log_id}")
            # Verify insertion
            res = memory.cursor.execute("SELECT * FROM agent_invocations WHERE id = ?", (log_id,)).fetchone()
            print("Verified Record:")
            for key in res.keys():
                print(f"  {key}: {res[key]}")
        else:
            print("Failed to log invocation.")

        memory.close()
        print("Self-test completed and connection closed.")
    except Exception as e:
        print(f"An error occurred during self-test: {e}") 