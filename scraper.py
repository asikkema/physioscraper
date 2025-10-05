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
            title TEXT,
            url TEXT
        )
    """)
    conn.commit()

    new_jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Navigate to the jobs page
        page.goto("https://physioswiss.ch/stelleninserate/?_per_page=5000")

        print("Scraper is ready!")

        # Wait for job listings to load
        page.wait_for_selector("article.tease-jobad")

        # Extract all job listings
        jobs = page.query_selector_all("article.tease-jobad")

        for job in jobs:
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
                    'title': title,
                    'url': url
                })
                print(f"\n🆕 NEW JOB FOUND!")
                print(f"Job Number: {job_number}")
                print(f"Date: {parsed_date}")
                print(f"Title: {title}")
                print(f"URL: {url}")
                print("-" * 80)

                # Insert new job into database
                cursor.execute("""
                    INSERT INTO jobs (job_number, date, title, url)
                    VALUES (?, ?, ?, ?)
                """, (job_number, str(parsed_date), title, url))

        browser.close()

    # Commit and close database
    conn.commit()
    conn.close()

    # Summary
    if new_jobs:
        print(f"\n✅ Found {len(new_jobs)} new job(s)!")
        for job in new_jobs:
            print(f"  - {job['job_number']}: {job['title']}")
    else:
        print(f"\n✅ No new jobs found. Database is up to date.")


if __name__ == "__main__":
    main()
