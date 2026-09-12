import sys
import os

def menu():
    print()
    print("========================================")
    print("   SIH - MID-DAY MEAL MONITORING SYSTEM ")
    print("   Team: NextGen | MIET                ")
    print("========================================")
    print("1. Run Pipeline (Default: images/midday.png)")
    print("2. Run Pipeline (Plate Test: images/plate_test.jpg)")
    print("3. Run Pipeline (Custom Image Path)")
    print("4. View Local Dashboard Summary")
    print("5. Sync Records to Cloud (Render)")
    print("6. Exit")
    print("========================================")

def main():
    while True:
        menu()
        choice = input("Select an option (1-6): ").strip()

        if choice == "1":
            print("\n>>> Running Pipeline on images/midday.png...")
            os.system("python src/detect.py images/midday.png")
        elif choice == "2":
            print("\n>>> Running Pipeline on images/plate_test.jpg...")
            os.system("python src/detect.py images/plate_test.jpg")
        elif choice == "3":
            custom_path = input("Enter image path: ").strip()
            if os.path.exists(custom_path):
                os.system(f"python src/detect.py {custom_path}")
            else:
                print(f"Error: File not found -> {custom_path}")
        elif choice == "4":
            print("\n>>> Fetching Local Records...")
            os.system("python src/dashboard.py")
        elif choice == "5":
            print("\n>>> Syncing to Cloud...")
            os.system("python src/sync.py")
        elif choice == "6":
            print("\nExiting. System ready for SIH presentation!")
            sys.exit(0)
        else:
            print("\nInvalid choice, please select 1 to 6.")

if __name__ == "__main__":
    main()
