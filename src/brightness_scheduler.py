import sys
from PySide6.QtCore import QTimer, QTime
from PySide6.QtWidgets import QApplication



class BrightnessScheduler:
    def __init__(self):
        self.tasks = {}
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_all_tasks)

    def add_task(self, time_str, callback):
        self.tasks[time_str] = callback
        print(f"Task added at {time_str}")

    def remove_task(self, time_str):
        if time_str in self.tasks:
            del self.tasks[time_str]
            print(f"Task at {time_str} removed")
        else:
            print(f"No task found at {time_str}")

    def stop_timer(self):
        self.timer.stop()
        print("Timer stopped")

    def start_checking(self, interval=60000):
        if self.tasks:
            self.timer.start(interval)
            print("Task checking started")
        else:
            print("No tasks to check, timer not started")

    def stop_checking(self):
        self.timer.stop()
        print("Task checking stopped")

    def check_all_tasks(self):
        current_time = QTime.currentTime().toString("HH:mm")
        print(f"Checking tasks at: {current_time}")
        if current_time in self.tasks:
            self.tasks[current_time]() # execute the callback
        else:
            print("No tasks at this time")

    def get_tasks(self):
        return self.tasks

    def clear_all_tasks(self):
        self.tasks.clear()
        print("All tasks cleared")
        self.stop_timer()

    def execute_recent_task(self):

        if not self.tasks:
            print("No tasks found")
            return
        
        current_time = QTime.currentTime().toString("HH:mm")
        past_tasks = [time for time in self.tasks.keys() if time < current_time]
        if past_tasks:
            recent_task_time = max(past_tasks)
            print(f"Executing recent task at: {recent_task_time}")
            self.tasks[recent_task_time]() # execute the callback
        else:
            print("No past tasks to execute for today, checking previous day")
            if self.tasks:
                recent_task_time = max(self.tasks.keys())
                print(f"Executing last task from previous day at: {recent_task_time}")
                self.tasks[recent_task_time]() # execute the callback



# Функції для виклику
def callback1():
    print("Task 1 executed")

def callback2():
    print("Task 2 executed")

def callback3():
    print("Task 3 executed")






if __name__ == "__main__":
    app = QApplication(sys.argv)

    scheduler = BrightnessScheduler()

    # Додаємо завдання
    # scheduler.add_task("23:46", callback1)
    # scheduler.add_task("17:45", callback2)
    # scheduler.add_task("23:50", callback3)

    # scheduler.execute_recent_task()

    # print("Tasks:")
    # for time, callback in scheduler.get_tasks().items():
    #     print(f"Task at {time} with callback: {callback.__name__}")

    # # Clear all tasks
    # scheduler.clear_all_tasks()

    # print("Tasks:")
    # for time, callback in scheduler.get_tasks().items():
    #     print(f"Task at {time} with callback: {callback.__name__}")

    # Запускаємо перевірку
    scheduler.start_checking()
    
    # Execute the most recent past task
    scheduler.execute_recent_task()

    app.exec()

