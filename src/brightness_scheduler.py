from PySide6.QtCore import QTimer, QTime, QDateTime, QThread, QCoreApplication, QObject, Signal, Slot, QMetaObject, Qt
from PySide6.QtWidgets import QApplication

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from MoniTune import MainWindow  # Пізнє визначення типу

from utils.utils import get_idle_time
from utils.lock_detect import LockDetect
import sys

import threading

# MARK: BrightnessScheduler
class BrightnessScheduler(QObject):
    def __init__(self, parent: 'MainWindow'):
        super().__init__()

        self.parent = parent
        self.tasks = {}
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_all_tasks)
        self.last_check_time = QDateTime.currentDateTime()

        self.time_active = 0  # Час активності комп'ютера
        self.saved_time = 0

        self.lock_listener = LockDetect(self.on_lock_state_change)
        threading.Thread(target=self.lock_listener.run, daemon=True).start()

    # MARK: on_lock_state_change()
    @Slot(str)
    def on_lock_state_change(self, state):
        if state == "unlocked":
            print("Screen unlocked at:", QTime.currentTime().toString("HH:mm"))
            print("Starting delayed task")
            threading.Timer(10, self.execute_recent_task).start()  # Виконати через 10 секунд
            # self.start_checking()
            QMetaObject.invokeMethod(self, "start_checking", Qt.QueuedConnection)

        elif state == "locked":
            print("Screen locked at:", QTime.currentTime().toString("HH:mm"))
            # self.stop_checking()
            QMetaObject.invokeMethod(self, "stop_checking", Qt.QueuedConnection)

    # MARK: get_tasks()
    def get_tasks(self):
        return self.tasks

    # MARK: add_task()
    def add_task(self, time_str, callback):
        self.tasks[time_str] = callback
        print(f"Task added at {time_str}")
    
    # MARK: remove_task()
    def remove_task(self, time_str):
        if time_str in self.tasks:
            del self.tasks[time_str]
            print(f"Task at {time_str} removed")
        else:
            print(f"No task found at {time_str}")
    
    # MARK: clear_all_tasks()
    def clear_all_tasks(self):
        self.stop_checking()
        self.tasks.clear()
        print("All tasks cleared")

    # MARK: stop_checking()
    @Slot()
    def stop_checking(self):
        self.timer.stop()
        print("Task checking stopped")

    # MARK: start_checking()
    @Slot()
    def start_checking(self, interval=60000):
        # if self.tasks:
        #     self.timer.start(interval)
        #     print("Task checking started")
        # else:
        #     print("No tasks to check, timer not started")
        print("Task checking started")
        self.last_check_time = QDateTime.currentDateTime()
        self.timer.start(interval)

    # MARK: check_all_tasks()
    def check_all_tasks(self):
        current_time = QTime.currentTime().toString("HH:mm")
        current_datetime = QDateTime.currentDateTime()

        print(f"Checking tasks at: {current_time}")

        if current_time in self.tasks:
            self.tasks[current_time]()  # execute the callback
        else:
            print("No tasks at this time")

        self.last_check_time = current_datetime


        # MARK: Check idle time
        if not self.parent.enable_break_reminders:
            self.time_active = 0
            self.saved_time = 0
        else:
            idle_time = get_idle_time()
            if idle_time is not None:
                print(f"idle_time: {idle_time:.2f}")

                if idle_time > 5 * 60:
                    print("idle 5min, reset time_active")
                    self.time_active = 0
                    self.saved_time = 0
                elif idle_time < 60 * 1.0:
                    self.time_active += 60
                    self.time_active += self.saved_time
                    self.saved_time = 0
                    if self.time_active >= 30 * 60:
                        print("active more 30 min!, show notification")
                        self.parent.break_notification()
                        self.time_active = 0
                else:
                    self.saved_time += 60

                print(f"time_active: {self.time_active / 60} min, saved_time: {self.saved_time / 60} min")
            
        # print()



    # MARK: execute_recent_task()
    def execute_recent_task(self):
        if not self.tasks:
            print("execute_recent_task: No tasks found")
            print("Restoring last change")
            self.parent.brightness_sync_onetime()
            return

        current_time = QTime.currentTime().toString("HH:mm")
        past_tasks = [time for time in self.tasks.keys() if time <= current_time]
        if past_tasks:
            recent_task_time = max(past_tasks)
            print(f"Executing recent task at: {recent_task_time}")
            self.tasks[recent_task_time]()  # execute the callback
        else:
            print("No past tasks to execute for today, checking previous day")
            if self.tasks:
                recent_task_time = max(self.tasks.keys())
                print(f"Executing last task from previous day at: {recent_task_time}")
                self.tasks[recent_task_time]()  # execute the callback



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

