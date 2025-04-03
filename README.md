# Job Application Bot

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

1. Configure the target job application URL in `config/settings.py`
2. Run the bot:

```bash
python main.py
```

## Configuration

You can customize the bot behavior in `config/settings.py`:

- Set different proxies
- Change timeout values
- Configure browser settings
- Set target URLs
- Update resume path

## Logging

Logs are stored in the `logs/` directory with timestamps. Check these logs for detailed information about the bot's operations and any errors encountered.

## Disclaimer

This tool is for educational purposes only. Use responsibly and in accordance with the terms of service of the websites you interact with.