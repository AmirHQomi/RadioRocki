import logging
from colorama import Fore, Style, init
from datetime import datetime

init(autoreset=True)

class ColorFormatter(logging.Formatter):
    def format(self, record):
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        levelname = record.levelname
        msg = record.getMessage()
        if levelname == 'INFO':
            return f"{Fore.GREEN}[{time}] [INFO] {msg}{Style.RESET_ALL}"
        elif levelname == 'WARNING':
            return f"{Fore.YELLOW}[{time}] [WARNING] {msg}{Style.RESET_ALL}"
        elif levelname == 'ERROR':
            return f"{Fore.RED}[{time}] [ERROR] {msg}{Style.RESET_ALL}"
        else:
            return f"[{time}] [{levelname}] {msg}"

def get_logger(name='RadioLogger'):
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColorFormatter())
        logger.addHandler(console_handler)
    return logger