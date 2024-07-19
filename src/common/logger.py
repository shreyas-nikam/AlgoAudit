# Import the required libraries
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import streamlit as st

class Logger:
    """
    This class is used to create a logger object for the Streamlit app.
    """
    _logger = None

    @staticmethod
    def get_logger():
        """
        This function is used to get the logger object for the Streamlit app.
        """
        if Logger._logger is None:
            # Logger configuration
            Path('logs').mkdir(parents=True, exist_ok=True)
            log_filename = "logs/qu-skillbridge-app.log"
            log_format = "%(asctime)s - %(levelname)s - %(message)s"
            date_format = "%Y-%m-%d %H:%M:%S"
            max_log_size = 5 * 1024 * 1024  # 5 MB
            backup_count = 10  # keep at most 3 log files

            # Create a logger
            Logger._logger = logging.getLogger("AlgoAudit-App-Logger")
            Logger._logger.setLevel(logging.INFO)  # Set minimum log level to INFO

            # Ensure the logger only has one handler to avoid duplicate logs
            if not Logger._logger.handlers:
                # Create a file handler that logs messages to a file, with log rotation
                file_handler = RotatingFileHandler(log_filename, maxBytes=max_log_size, backupCount=backup_count)
                file_handler.setLevel(logging.INFO)  # Set minimum log level for the file handler

                # Create a formatter and set it for the handler
                formatter = logging.Formatter(log_format, datefmt=date_format)
                file_handler.setFormatter(formatter)

                # Add the handler to the logger
                Logger._logger.addHandler(file_handler)

        return Logger._logger
