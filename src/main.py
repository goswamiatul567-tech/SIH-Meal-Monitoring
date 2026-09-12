import os
import subprocess
import sys
import time

LIVE_IMG_PATH = "images/live.jpg"

def capture_live_frame():
    print("\n>>> Accessing device camera...")
    if os.path.exists(LIVE_IMG_PATH):
        try:
            os.remove(LIVE_IMG_PATH)
        except OSError:
            pass

    cmd = ["termux-camera-photo", "-c", "0", LIVE_IMG_PATH]
    res = subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(1)

    if os.path.exists(LIVE_IMG_PATH) and os.path.getsize(LIVE_IMG_PATH) > 0:
        print(">>> Live snapshot captured successfully!")
        return True
    else:
        print(">>> ERROR: Failed to capture live photo.")
        if res.stderr:
            print(f"Details: {res.stderr}")
        return False

def menu():
    print()
    print("========================================")
    print("   SIH - MID-DAY MEAL MONITORING SYSTEM ")
    print("   Team: NextGen | MIET                ")
    print("========================================")
    print("1. Start Continuous Live Surveillance (Auto Loop)")
    print("2. Capture Single Live Photo & Analyze")
    print("3. Run Pipeline (Default: images/midday.png)")
    print("4. Run Pipeline (Plate Test: images/plate_test.jpg)")
    print("5. Run Pipeline (Custom Image Path)")
    print("6. View Local Dashboard Summary")
    print("7. Sync Records to Cloud (Render)")
    print("8. Exit")
    print("========================================")

def main():
    while True:
        menu()
        choice = input("Select an option (1-8): ").strip()

        if choice == "1":
            print("\n>>> Launching Continuous Surveillance Loop...")
            os.system("python src/live_monitor.py")
        elif choice == "2":
            success = capture_live_frame()
            if success:
                print(f"\n>>> Running AI Detection on Live Capture ({LIVE_IMG_PATH})...")
                os.system(f"python src/detect.py {LIVE_IMG_PATH}")
        elif choice == "3":
            print("\n>>> Running Pipeline on images/midday.png...")
            os.system("python src/detect.py images/midday.png")
        elif choice == "4":
            print("\n>>> Running Pipeline on images/plate_test.jpg...")
            os.system("python src/detect.py images/plate_test.jpg")
        elif choice == "5":
            custom_path = input("Enter image path: ").strip()
            if os.path.exists(custom_path):
                os.system(f"python src/detect.py {custom_path}")
            else:
                print(f"Error: File not found -> {custom_path}")
        elif choice == "6":
            print("\n>>> Fetching Local Records...")
            os.system("python src/dashboard.py")
        elif choice == "7":
            print("\n>>> Syncing to Cloud...")
            os.system("python src/sync.py")
        elif choice == "8":
            print("\nExiting. System ready for SIH presentation!")
            sys.exit(0)
        else:
            print("\nInvalid choice, please select 1 to 8.")

if __name__ == "__main__":
    main()
