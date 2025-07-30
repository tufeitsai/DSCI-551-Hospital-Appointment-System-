import json
import sys
import requests
import datetime

DATABASE_URLS = {0: "https://hospital1-850e0-default-rtdb.firebaseio.com",
                 1: "https://hospital-2-f901a-default-rtdb.firebaseio.com"}

# 定义哈希函数：分成两个数据库
def hash_userId(userId): # based on the ASCII
    hash_value = sum(ord(char) for char in userId)
    return hash_value % 2


# 辅助函数1：验证date格式
def validate_date_format(date_string):
    try:
        datetime.datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False


# 辅助函数2：验证time格式
def validate_time_format(time_string):
    try:
        datetime.datetime.strptime(time_string, '%H:%M')
        return True
    except ValueError:
        return False


# 辅助函数3：验证userId是否存在
def check_user_exists(user_id):
    hash_value = hash_userId(user_id)
    database_url = DATABASE_URLS[hash_value]

    response = requests.get(database_url + "/users.json")

    if response.status_code == 200:
        users = response.json()

        if users:  # Check if users is not empty
            return user_id in users
        else:
            return False
    else:
        print("Failed to fetch users from the database.")
        return False


# 辅助函数4: 查找已预约的时间，输出剩余可预约时间
def find_reserved_times_by_date(date):
    # Define all available appointment times
    available_times = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00']

    # Get the reserved appointment times
    reserved_times = []
    for hash_value, database_url in DATABASE_URLS.items():
        response = requests.get(database_url + "/appointments.json")
        if response.status_code == 200:
            appointments = response.json()
            if appointments is None:
                print("All available times can be reserved:")
                print(available_times)
                return available_times
            for appointment_data in appointments.values():
                if "date" in appointment_data:
                    if appointment_data["date"] == date:
                        time = appointment_data.get("time")
                        if time is None:
                            print("All available times can be reserved:")
                            print(available_times)
                            return available_times  # If appointment time is null, return all available times
                        else:
                            reserved_times.append(time)

    # Calculate remaining available times
    curr_available_times = [time for time in available_times if time not in reserved_times]
    print("Remaining available appointment times:")
    print(curr_available_times)
    return curr_available_times


# 1：根据userId查找预约记录
def find_appointments_by_user(user_id):
    hash_value = hash_userId(user_id)
    database_url = DATABASE_URLS[hash_value]
    response = requests.get(database_url + "/appointments.json")
    if response.status_code == 200:
        appointments = response.json()
        found_appointments = {}
        print(f"Appointments for user {user_id}:")
        # 使用sorted函数对预约按照日期和时间排序
        sorted_appointments = sorted(appointments.items(), key=lambda x: (x[1]["date"], x[1]["time"]))
        for key, appointment in sorted_appointments:
            if appointment["userId"] == user_id:
                print(f"{appointment['date']} -- {appointment['time']} -- {appointment['reason']}")
                found_appointments[key] = appointment
        if not found_appointments:
            print("UserId not found.")
        return found_appointments
    else:
        print("Failed to fetch appointments.")
        return {}


# 2：根据date查找预约记录
def find_appointments_by_date():
    while True:
        date = input("Enter date (YYYY-MM-DD): ")
        if validate_date_format(date):
            break
        else:
            print("Date error: Date format should be 'YYYY-MM-DD'. Please enter again.")

    found_appointments = False  # 初始化 found_appointments 变量
    for hash_value, database_url in DATABASE_URLS.items():
        response = requests.get(database_url + "/appointments.json")
        if response.status_code == 200:
            appointments = response.json()
            for key, appointment in appointments.items():
                if appointment["date"] == date:
                    print(f"{appointment['time']} -- {appointment['userId']} -- {appointment['reason']}")
                    found_appointments = True  # 如果找到预约，则将 found_appointments 设置为 True
    if not found_appointments:
        print("No appointments found for this date.")


# 3: 新增预约
def make_appointment():
    while True:
        user_id = input("Enter user ID: ")
        hash_value = hash_userId(user_id)
        database_url = DATABASE_URLS[hash_value]

        # 检查用户是否存在
        if not check_user_exists(user_id):
            print("User not found.")
            # Ask if the user wants to re-enter the user ID
            retry = input("Do you want to re-enter user ID? (yes/no): ")
            if retry.lower() != "yes":
                return

            continue

        # 获取当前日期和时间
        current_datetime = datetime.datetime.now()
        current_date = current_datetime.date()
        current_time = current_datetime.time()

        # 输入预约日期
        while True:
            appointment_date_str = input("Enter date (YYYY-MM-DD): ")
            # 检查日期格式是否正确
            if not validate_date_format(appointment_date_str):
                print("Date format is incorrect. Please use the format YYYY-MM-DD.")
                continue
            # 检查预约日期是否在当前日期之后
            appointment_date = datetime.datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
            if current_date > appointment_date:
                print("You can only make appointments for future dates.")
                continue

            # 获取预约时间列表
            now_available_times = find_reserved_times_by_date(appointment_date_str)

            # Check if there are available times for today
            if not now_available_times:
                break  # 直接跳出日期输入循环
            else:
                # Determine the latest available time dynamically
                current_max_available_time = max(now_available_times, default=datetime.time(16, 0))
                # Convert current_max_available_time to datetime.time object
                current_max_available_time = datetime.datetime.strptime(str(current_max_available_time),
                                                                         '%H:%M').time()

                # Check if current time is past the available appointment time for today
                if current_date == appointment_date:
                    if current_time >= current_max_available_time:
                        print("It's past the available appointment time for today.")
                        continue
                break

        # 输入预约时间
        while True:
            appointment_time = input("Enter time (HH:MM): ")
            if appointment_time not in now_available_times:
                print("Invalid appointment time. Available times for today are: ", now_available_times)
                continue
            break

        # 输入预约原因
        reason = input("Enter reason: ")

        # 发送预约信息到数据库
        appointment = {
            "date": appointment_date_str,
            "time": appointment_time,
            "reason": reason,
            "userId": user_id
        }

        response = requests.post(database_url + "/appointments.json", json=appointment)
        if response.status_code == 200:
            print("Appointment made successfully.")
        else:
            print("Failed to make appointment. Please try again.")
        break


# 4: 取消预约
def cancel_appointment():
    user_id = input("Enter user ID: ")
    appointments = find_appointments_by_user(user_id)
    if appointments:
        while True:  # 循环持续直到用户选择退出
            date = input("Enter date (YYYY-MM-DD) of the appointment you want to cancel (or 'q' to quit): ")
            if date.lower() == 'q':
                break  # 如果用户输入 'q'，退出循环
            time = input("Enter time (HH:MM) of the appointment you want to cancel: ")

            # 检查日期和时间格式是否有效
            if not validate_date_format(date) or not validate_time_format(time):
                print("Invalid date or time format. Please try again.")  # 格式错误提示消息
                continue  # 重新开始循环，让用户重新输入

            found = False
            for appointment_id, appointment_data in appointments.items():
                if appointment_data["date"] == date and appointment_data["time"] == time:
                    found = True
                    cancel_confirmation = input(
                        f"Do you want to cancel the appointment on {date} at {time}? (yes/no): ")
                    if cancel_confirmation.lower() == 'yes':
                        # 删除预约记录
                        hash_value = hash_userId(user_id)
                        database_url = DATABASE_URLS[hash_value]
                        delete_url = f"{database_url}/appointments/{appointment_id}.json"

                        response = requests.delete(delete_url)
                        if response.status_code == 200:
                            print("Appointment canceled successfully.")
                            del appointments[appointment_id]  # 从本地字典中删除取消的预约记录
                        else:
                            print("Failed to cancel appointment. Please try again.")
                    else:
                        print("Appointment not canceled.")
                    break

            if not found:
                print("No matching appointment found for the provided date and time.")
    else:
        print(f"No appointments found for user {user_id}.")


# 5: 更改预约
def change_appointment():
    while True:
        user_id = input("Enter user ID: ")

        # 验证用户是否存在，如果不存在则询问是否重新输入用户ID
        while not check_user_exists(user_id):
            reenter = input("User does not exist. Do you want to re-enter user ID? (yes/no): ")
            if reenter.lower() == "yes":
                user_id = input("Enter user ID: ")
            else:
                return

        # 查找指定用户的预约并列出
        appointments = find_appointments_by_user(user_id)
        if not appointments:
            print("No appointments found for this user.")
            return

        try:
            # 让用户选择要修改的预约日期和时间
            date_to_change = input("Enter the date you want to change (YYYY-MM-DD): ")
            time_to_change = input("Enter the time you want to change (HH:MM): ")
            selected_key = None
            for key, appointment in appointments.items():
                if appointment['date'] == date_to_change and appointment['time'] == time_to_change:
                    selected_key = key
                    selected_appointment = appointment
                    break

            if selected_key is None:
                raise ValueError("Appointment not found.")

        except ValueError as e:
            print(str(e))
            continue

        # 将日期和时间转换为 datetime 对象
        try:
            change_date = datetime.datetime.strptime(date_to_change, '%Y-%m-%d')
            change_time = datetime.datetime.strptime(time_to_change, '%H:%M').time()
        except ValueError:
            print("Date or time format is incorrect. Please use the format YYYY-MM-DD for date and HH:MM for time.")
            continue

        # 验证需要修改的日期和时间是否早于当前时间
        change_datetime = datetime.datetime.combine(change_date.date(), change_time)
        if change_datetime < datetime.datetime.now():
            print("The appointment date and time you changed cannot be earlier than the current date and time.")
            continue

        new_date = input("Enter new date (YYYY-MM-DD): ")

        # 尝试将输入的日期转换为 datetime 对象
        try:
            new_date = datetime.datetime.strptime(new_date, '%Y-%m-%d')
        except ValueError:
            print("Date format is incorrect. Please use the format YYYY-MM-DD.")
            continue  # 继续循环，重新输入

        new_time = input("Enter new time (HH:MM): ")

        # 尝试将输入的时间转换为 datetime 对象
        try:
            new_time = datetime.datetime.strptime(new_time, '%H:%M').time()
        except ValueError:
            print("Time format is incorrect. Please use the format HH:MM.")
            continue  # 继续循环，重新输入

        new_reason = input("Enter new reason: ")

        # 将日期和时间合并为一个 datetime 对象
        new_datetime = datetime.datetime.combine(new_date.date(), new_time)

        # 验证新日期和时间是否早于当前时间
        if new_datetime < datetime.datetime.now():
            print("New appointment date and time cannot be earlier than the current date and time.")
            rebook = input("Do you want to rebook? (yes/no): ")
            if rebook.lower() == "yes":
                continue  # 继续循环，重新输入
            else:
                return

        hash_value = hash_userId(user_id)
        database_url = DATABASE_URLS[hash_value]
        response = requests.get(database_url + "/appointments.json")
        if response.status_code == 200:
            appointments_data = response.json()
            for key, appointment in appointments_data.items():
                if key == selected_key:
                    appointment["date"] = new_date.strftime('%Y-%m-%d')
                    appointment["time"] = new_time.strftime('%H:%M')
                    appointment["reason"] = new_reason
                    requests.put(database_url + f"/appointments/{key}.json", json=appointment)
                    print("Appointment changed successfully.")
                    return
        print("Appointment not found.")


# 主函数
def admin_appointments_menu():
    while True:
        print("1. Find all appointments based on user ID")
        print("2. Find all appointments in a certain date")
        print("3. Make an appointment")
        print("4. Cancel an appointment")
        print("5. Change an appointment")
        print("6. Back to Main Menu")
        choice = input("Enter your choice: ")

        if choice == "1":
            user_id = input("Enter user ID: ")
            find_appointments_by_user(user_id)
        elif choice == "2":
            find_appointments_by_date()
        elif choice == "3":
            make_appointment()
        elif choice == "4":
            cancel_appointment()
        elif choice == "5":
            change_appointment()
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    admin_appointments_menu()
