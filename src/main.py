import sys
import os

def menu():
    print()
    print("========================================")
    print("   SIH - MID-DAY MEAL MONITORING SYSTEM ")
    print("   Team: NextGen | MIET                ")
    print("========================================")
    print("1. Run Meal Detection Pipeline")
    print("2. View Local Dashboard Summary")
    print("3. Sync Records to Cloud (Render)")
    print("4. Exit")
    print("========================================")

def main():
    while True:
        menu()
        choice = input("Select an option (1-4): ").strip()

        if choice == "1":
            print("\n>>> Running Detection Pipeline...")
            os.system("python src/detect.py")
        elif choice == "2":
            print("\n>>> Fetching Local Records...")
            os.system("python src/dashboard.py")
        elif choice == "3":
            print("\n>>> Syncing to Cloud...")
            os.system("python src/sync.py")
        elif choice == "4":
            print("\nExiting. Good luck for SIH!")
            sys.exit(0)
        else:
            print("\nInvalid choice, please select 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()
