"""
Logging configuration for the application.
"""
import logging
import os
from datetime import datetime

def setup_logging(log_level=logging.INFO):
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: The log level to use (default: logging.INFO)
    """
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Generate log filename based on current date and time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/job_application_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    
    # Log startup message
    logging.info(f"Logging initialized. Log file: {log_filename}")