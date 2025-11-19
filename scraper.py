#!/usr/bin/env python3
"""
Physiomatch website scraper
Scrapes job listings from https://physioswiss.ch/
"""

from playwright.sync_api import sync_playwright
from datetime import datetime
import re
import sqlite3


def parse_job_number(number_text):
    """Extract job number from text like 'Nr. J-502200'"""
    match = re.search(r'J-(\d+)', number_text)
    return match.group(1) if match else "N/A"


def parse_german_date(date_text):
    """Parse German date format like '5. Oktober 2025'"""
    month_map = {
        'Januar': 1, 'Februar': 2, 'März': 3, 'April': 4,
        'Mai': 5, 'Juni': 6, 'Juli': 7, 'August': 8,
        'September': 9, 'Oktober': 10, 'November': 11, 'Dezember': 12
    }
    match = re.match(r'(\d+)\.\s+(\w+)\s+(\d{4})', date_text)
    if match:
        day, month_name, year = match.groups()
        month = month_map.get(month_name)
        if month:
            return datetime(int(year), month, int(day)).date()
    return "N/A"


def main():
    """Main entry point for the scraper"""
    # Set up database
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    # Create table with job_number as primary key
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_number TEXT PRIMARY KEY,
            date TEXT,
            employer TEXT,
            title TEXT,
            url TEXT
        )
    """)

    # Add employer column if it doesn't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN employer TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass

    # Get existing employers before scraping
    cursor.execute("SELECT DISTINCT employer FROM jobs WHERE employer IS NOT NULL AND employer != 'N/A'")
    existing_employers = {row[0] for row in cursor.fetchall()}

    new_jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the jobs page
        page.goto("https://physioswiss.ch/stelleninserate/?_per_page=5000")

        print("Scraper is ready!")

        # Wait for job listings to load
        page.wait_for_selector("article.tease-jobad")

        # Extract all job listings
        jobs = page.query_selector_all("article.tease-jobad")

        for job in jobs:
            # Extract employer
            employer_element = job.query_selector("p.tease-jobad__company")
            employer = employer_element.inner_text().strip() if employer_element else "N/A"

            # Extract title
            title_element = job.query_selector("h2.tease-jobad__title")
            title = title_element.inner_text() if title_element else "N/A"

            # Extract URL
            link_element = job.query_selector("a.tease-jobad__link")
            url = link_element.get_attribute("href") if link_element else "N/A"

            # Extract job number
            number_element = job.query_selector("p.tease-jobad__number")
            job_number = parse_job_number(number_element.inner_text()) if number_element else "N/A"

            # Extract and parse date
            date_element = job.query_selector("p.tease-jobad__date time")
            parsed_date = parse_german_date(date_element.inner_text()) if date_element else "N/A"

            # Check if job already exists in database
            cursor.execute("SELECT job_number FROM jobs WHERE job_number = ?", (job_number,))
            exists = cursor.fetchone()

            if not exists:
                # New job found!
                new_jobs.append({
                    'job_number': job_number,
                    'date': parsed_date,
                    'employer': employer,
                    'title': title,
                    'url': url
                })
                print(f"\n🆕 NEW JOB FOUND!")
                print(f"Job Number: {job_number}")
                print(f"Date: {parsed_date}")
                print(f"Employer: {employer}")
                print(f"Title: {title}")
                print(f"URL: {url}")
                print("-" * 80)

                # Insert new job into database
                cursor.execute("""
                    INSERT INTO jobs (job_number, date, employer, title, url)
                    VALUES (?, ?, ?, ?, ?)
                """, (job_number, str(parsed_date), employer, title, url))

        browser.close()

    # Commit and close database
    conn.commit()

    # Find new employers
    new_employers = set()
    if new_jobs:
        # Get employers from new jobs
        new_job_employers = {job['employer'] for job in new_jobs if job['employer'] != "N/A"}

        # Find employers that weren't in the database before scraping
        new_employers = new_job_employers - existing_employers

    conn.close()

    # Summary
    if new_jobs:
        print(f"\n✅ Found {len(new_jobs)} new job(s)!")
        for job in new_jobs:
            print(f"  - {job['job_number']}: {job['title']}")
    else:
        print(f"\n✅ No new jobs found. Database is up to date.")

    # New employers report
    if new_employers:
        print(f"\n🏢 Found {len(new_employers)} new employer(s)!")
        for employer in sorted(new_employers):
            print(f"  - {employer}")


if __name__ == "__main__":
    main()
