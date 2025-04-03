"""
Configuration settings for the job application bot.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SOLVECAPTCHA_API_KEY = os.getenv("SOLVECAPTCHA_API_KEY")

# Proxy configurations
PROXIES = [
    {
        "server": "170.106.118.114:2333", 
        "username": "uc8c8f311563305c2-zone-custom-region-us", 
        "password": "uc8c8f311563305c2"
    }
    # Add more proxies as needed
]

# Browser and navigation settings
TIMEOUT = int(os.getenv("TIMEOUT", 120000))  # Default: 2 minutes
HEADLESS = os.getenv("HEADLESS", "False").lower() == "true"

# Job application settings
RESUME_PATH = "resume/resume.pdf"
USER_METADATA_PATH = "user_metadata/user_metadata.txt"

# Form selectors
APPLICATION_FORM_SELECTOR = "#application-form"
SUBMIT_BUTTON_SELECTOR = "#btn-submit"

# Captcha related settings
HCAPTCHA_SELECTORS = [
    'div[class*="h-captcha"]',
    'iframe[src*="hcaptcha.com"]',
    'div#h-captcha.h-captcha'
]

# OpenAI settings
OPENAI_MODEL = "gpt-4-turbo"