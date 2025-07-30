# 导入子菜单文件
from admin_user_info import admin_user_info_menu
from admin_appointments import admin_appointments_menu
import sys

def main_menu():
    while True:
        print("1. Admin User Information")
        print("2. Admin Appointment")
        print("3. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            admin_user_info_menu()  # 调用 admin_user_info.py 中的菜单函数
        elif choice == "2":
            admin_appointments_menu()  # 调用 admin_appointment.py 中的菜单函数
        elif choice == "3":
            print("Exiting the program...")
            sys.exit()  # 跳出循环，结束程序
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()