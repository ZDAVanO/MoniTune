import os
import sys
import logging

logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
# logging.disable(logging.CRITICAL + 1) # disable all logging
logging.disable(logging.CRITICAL)


# Formats for logs
file_log_format = "[%(asctime)s,%(msecs)03d] [%(levelname)s] [%(name)s] [%(funcName)s]: %(message)s"
console_log_format = "[%(asctime)s] [%(levelname)s] [%(funcName)s]: %(message)s"


# # Handler for file (saves logs to file)
# try:
#     # Get the directory of the current script
#     log_dir = r"C:\Program Files\MoniTune"  # os.path.dirname(os.path.abspath(sys.argv[0]))
#     main_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
#     log_file_path = os.path.join(main_dir, "MoniTune.log")
#     print(f"Log file path: {log_file_path}")

#     file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
#     # file_handler = logging.FileHandler("MoniTune.log", mode="w", encoding="utf-8")  # Overwrite log file on each run
#     file_handler.setLevel(logging.DEBUG)  # all logs will be saved to file
#     file_handler.setFormatter(logging.Formatter(file_log_format, datefmt="%H:%M:%S"))
#     logger.addHandler(file_handler)
# except Exception as e:
#     logger.warning(f"Could not create log file: {e}")

# Handler for console (prints logs to console)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # only INFO and above will be printed to console
console_handler.setFormatter(logging.Formatter(console_log_format, datefmt="%H:%M:%S"))
logger.addHandler(console_handler)


###########################################################################
# DEBUG, INFO, WARNING, ERROR, CRITICAL

# logging.getLogger("screen_brightness_control").setLevel(logging.WARNING)
logging.getLogger("screen_brightness_control").setLevel(logging.ERROR)

logging.getLogger("urllib3").setLevel(logging.WARNING)


###########################################################################


# Function to get a logger with a specific name
def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


# # Decorator
# def log_function_call(func):
#     def wrapper(*args, **kwargs):
#         logger.debug(f"Виклик {func.__name__} з args={args}, kwargs={kwargs}")
#         result = func(*args, **kwargs)
#         logger.debug(f"{func.__name__} повернув {result}")
#         return result
#     return wrapper

