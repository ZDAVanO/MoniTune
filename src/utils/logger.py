import os
import sys
import logging
from typing import Optional

import config as cfg
from utils.reg_utils import reg_read_bool


# Formats for logs
file_log_format = "[%(asctime)s,%(msecs)03d] [%(levelname)s] [%(name)s] [%(funcName)s]: %(message)s"
console_log_format = "[%(asctime)s] [%(levelname)s] [%(funcName)s]: %(message)s"

_file_handler: Optional[logging.FileHandler] = None
_console_handler: Optional[logging.StreamHandler] = None


def get_log_dir() -> str:
    """
    Returns the directory where log files should be stored.
    - If running as a frozen executable (e.g. PyInstaller EXE), returns the executable directory.
    - If running from source/dev, returns the project root directory.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        # logger.py is in src/utils/
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(src_dir)
        return project_root


def get_log_file_path() -> str:
    """Returns the full path to MoniTune.log."""
    return os.path.join(get_log_dir(), "MoniTune.log")


def is_file_logging_enabled() -> bool:
    """Checks if file logging is currently active."""
    return _file_handler is not None


def set_file_logging(enable: bool) -> bool:
    """
    Enables or disables logging to file.
    When enabled: creates FileHandler writing to MoniTune.log.
    When disabled: closes FileHandler, removes it, and completely stops file I/O overhead.
    """
    global _file_handler
    root_logger = logging.getLogger()

    if enable:
        if _file_handler is None:
            log_file_path = get_log_file_path()
            try:
                os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
                _file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
                _file_handler.setLevel(logging.DEBUG)
                _file_handler.setFormatter(logging.Formatter(file_log_format, datefmt="%H:%M:%S"))
                root_logger.addHandler(_file_handler)
                # Re-enable logging in case it was disabled for release build
                logging.disable(logging.NOTSET)
                root_logger.info(f"File logging enabled. Log file: {log_file_path}")
                return True
            except Exception as e:
                root_logger.warning(f"Could not create log file '{log_file_path}': {e}")
                _file_handler = None
                return False
        return True
    else:
        if _file_handler is not None:
            try:
                root_logger.info("File logging disabled.")
                _file_handler.flush()
                _file_handler.close()
            except Exception:
                pass
            root_logger.removeHandler(_file_handler)
            _file_handler = None

        # If running frozen without console and file logging is disabled, disable logging completely
        if getattr(sys, "frozen", False) and sys.stdout is None:
            logging.disable(logging.CRITICAL)
        return False


def init_logging():
    """Initializes root logger, console handler (if available), and reads registry for file logging."""
    global _console_handler
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Console handler (only when stdout is present)
    if sys.stdout is not None and _console_handler is None:
        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(logging.INFO)
        _console_handler.setFormatter(logging.Formatter(console_log_format, datefmt="%H:%M:%S"))
        root_logger.addHandler(_console_handler)

    # 3rd-party noisy loggers
    logging.getLogger("screen_brightness_control").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Check registry preference for file logging
    enabled = reg_read_bool(cfg.REGISTRY_PATH, "EnableLogging", False)
    set_file_logging(enabled)


# Run initialization on import
init_logging()


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

