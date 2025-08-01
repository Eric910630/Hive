# main.py

from hive.core.memory import CoreMemory

def main():
    """
    Main entry point for the Hive application.
    For v1.0, this script will initialize the core components and
    start the main application loop.
    """
    print("🚀 Initializing Hive v1.0...")
    
    try:
        # Initialize the central memory core
        memory = CoreMemory()
        print("✅ CoreMemory initialized successfully.")
        
        # --- Future application logic will go here ---
        
        # Cleanly close the connection on exit
        memory.close()
        print("👋 Hive application finished.")

    except Exception as e:
        print(f"🔥 An error occurred during Hive initialization: {e}")

if __name__ == "__main__":
    main() 