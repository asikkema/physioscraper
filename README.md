# Physiomatch Job Scraper

A web scraper that monitors job listings from [physioswiss.ch](https://physioswiss.ch/stelleninserate/), tracks them in a SQLite database, and notifies you of new job postings and employers.

## What It Does

This script automatically:
- Scrapes all job listings from the physioswiss.ch job board
- Extracts key information: job number, posting date, employer name, job title, and URL
- Stores data in a local SQLite database
- **Detects new job postings** that weren't in the database before
- **Identifies new employers** appearing for the first time
- Shows you a summary report after each run

**Important:** Run this script regularly (e.g., daily or weekly) to stay updated on new job opportunities and track which employers are newly posting positions.

## Installation Instructions

### Windows Installation (From Scratch)

If you're on a fresh Windows business laptop with no development tools:

#### 1. Install Python

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download the latest Python 3.11+ installer for Windows
3. **Important:** During installation, check the box "Add Python to PATH"
4. Click "Install Now"
5. Verify installation by opening Command Prompt (search "cmd" in Start menu) and typing:
   ```cmd
   python --version
   ```
   You should see something like `Python 3.11.x`

#### 2. Install uv (Package Manager)

Open Command Prompt and run:
```cmd
pip install uv
```

#### 3. Install Git (Optional but Recommended)

Git allows you to easily download and update the project.

1. Go to [git-scm.com/downloads](https://git-scm.com/downloads)
2. Download the Git installer for Windows
3. Run the installer with default settings
4. Verify installation by opening a new Command Prompt and typing:
   ```cmd
   git --version
   ```

#### 4. Download This Project

**Option A: Using Git (Recommended)**
```cmd
git clone <repository-url>
cd classic-scaper
```

**Option B: Without Git**
- Download the project as a ZIP file
- Extract it to a folder like `C:\Users\YourName\physiomatch-scraper`
- Navigate into the `classic-scaper` folder

#### 5. Install Project Dependencies

Navigate to the project folder in Command Prompt:
```cmd
cd C:\Users\YourName\physiomatch-scraper\classic-scaper
```

Then run:
```cmd
uv sync
```

This will install all required dependencies (Playwright, etc.)

#### 6. Install Browser for Playwright

Run:
```cmd
uv run playwright install chromium
```

This downloads the Chromium browser needed for web scraping.

### macOS/Linux Installation

1. Install Python 3.11+ (usually pre-installed on macOS/Linux)
2. Install uv:
   ```bash
   pip install uv
   ```
3. Navigate to project directory:
   ```bash
   cd classic-scaper
   ```
4. Install dependencies:
   ```bash
   uv sync
   ```
5. Install Playwright browser:
   ```bash
   uv run playwright install chromium
   ```

## How to Run

### Windows

1. Open Command Prompt
2. Navigate to the project folder:
   ```cmd
   cd C:\Users\YourName\physiomatch-scraper\classic-scaper
   ```
3. Run the scraper:
   ```cmd
   uv run scraper.py
   ```

### macOS/Linux

```bash
cd classic-scaper
uv run scraper.py
```

### What You'll See

The script will:
1. Open a browser window (you'll see it navigating to physioswiss.ch)
2. Scrape all job listings
3. Show notifications for any **new jobs** found (with full details)
4. Display a summary at the end:
   - Number of new jobs found
   - List of new job postings
   - **New employers** appearing for the first time

Example output:
```
Scraper is ready!

🆕 NEW JOB FOUND!
Job Number: 502362
Date: 2025-10-05
Employer: Bfit2
Title: Dipl. Physiotherapeut:in 60-100%
URL: https://physioswiss.ch/stelleninserate/119996/...
--------------------------------------------------------------------------------

✅ Found 1 new job(s)!
  - 502362: Dipl. Physiotherapeut:in 60-100%

🏢 Found 1 new employer(s)!
  - Bfit2
```

## Database

All job data is stored in `jobs.db` (SQLite database) in the project folder. This file:
- Keeps track of all jobs you've seen
- Enables detection of new postings
- Persists between runs

**Don't delete this file** unless you want to reset and re-discover all jobs as "new".

## Recommended Usage

Run the scraper regularly to monitor for new opportunities:
- **Daily:** For active job hunting
- **Weekly:** For passive monitoring
- **Whenever needed:** To check for updates

Each run only reports jobs and employers that are truly new since the last run.

## Tech Stack

- Python 3.11+
- Playwright (web automation)
- SQLite (database)
- uv (package manager)

## Troubleshooting

**"python is not recognized"**: Python wasn't added to PATH during installation. Reinstall Python and check "Add Python to PATH".

**"uv: command not found"**: Run `pip install uv` again.

**Browser doesn't open**: Run `uv run playwright install chromium` to install the browser.

**Permission errors on Windows**: Run Command Prompt as Administrator (right-click → "Run as administrator").
