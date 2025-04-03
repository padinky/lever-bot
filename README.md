# Lever Job Application Bot

An automated job application bot using Python and Playwright to fill out and submit job applications on Lever-based job application pages.

## Features

- Automatically detects and fills required form fields
- Uses AI to generate appropriate field values based on user metadata
- Simulates human-like typing and scrolling behavior
- Handles file uploads (resume)
- Can solve hCaptcha using SolveCaptcha service
- Works with proxy support for anonymity
- Detailed logging for monitoring and debugging

## Project Structure

```
job_application_bot/
├── .env                      # Environment variables
├── README.md                 # Project documentation
├── requirements.txt          # Dependencies
├── main.py                   # Entry point
├── config/
│   └── settings.py           # Configuration settings
├── models/
│   ├── __init__.py
│   └── form_models.py        # Data models for form elements
├── services/
│   ├── __init__.py
│   ├── browser_service.py    # Browser and page handling
│   ├── form_service.py       # Form field extraction and filling
│   ├── captcha_service.py    # CAPTCHA solving functionality
│   └── ai_service.py         # OpenAI integration
├── utils/
│   ├── __init__.py
│   ├── logging_utils.py      # Logging configuration
│   └── human_simulation.py   # Human-like behavior simulation
└── user_metadata/
    └── user_metadata.txt     # User information for form filling
```

## Setup

1. Create a virtual environment:

```bash
python -m venv venv
```

2. Activate the virtual environment:

```bash
# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Install browser binaries:

```bash
# Install all browsers
playwright install

# Or install only Chromium (recommended for this application)
playwright install chromium
```

5. If you encounter issues with the browser installation:

```bash
# Update Playwright to the latest version
pip install --upgrade playwright

# Clear the cache and reinstall browsers
rm -rf ~/Library/Caches/ms-playwright
playwright install
```

5. Create a `.env` file with your API keys:

```
OPENAI_API_KEY=your_openai_api_key_here
SOLVECAPTCHA_API_KEY=your_solvecaptcha_api_key_here
```

6. Create your `user_metadata/user_metadata.txt` file with your personal information for job applications.

7. Add your resume at `resume/resume.pdf`

## Usage

Run the application by providing the target Lever job application URL as a required command-line argument:

```bash
python main.py --url "https://jobs.lever.co/company/job-id/apply"
```

For example:

```bash
python main.py --url "https://jobs.lever.co/ippon/528e313e-da2e-4fdd-949b-6c44e2798738/apply"
```

The URL must follow the Lever job application format: `https://jobs.lever.co/company/job-id/apply`.


## Configuration

You can customize the bot behavior in `config/settings.py`:

- Set different proxies
- Change timeout values
- Configure browser settings (headless mode, etc.)
- Update resume path
- Configure OpenAI settings
- Adjust captcha handling parameters

## Logging

Logs are stored in the `logs/` directory with timestamps. Check these logs for detailed information about the bot's operations and any errors encountered.

## Disclaimer

This tool is for educational purposes only. Use responsibly and in accordance with the terms of service of the websites you interact with.