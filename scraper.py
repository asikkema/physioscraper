#!/usr/bin/env python3
"""
Physiomatch website scraper
Scrapes job listings from https://physioswiss.ch/
"""

from playwright.sync_api import sync_playwright
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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


def setup_database():
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_number TEXT PRIMARY KEY,
            date TEXT,
            employer TEXT,
            title TEXT,
            url TEXT
        )
    """)

    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN employer TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    cursor.execute("SELECT DISTINCT employer FROM jobs WHERE employer IS NOT NULL AND employer != 'N/A'")
    existing_employers = {row[0] for row in cursor.fetchall()}
    return conn, cursor, existing_employers


def scrape_new_jobs(cursor):
    new_jobs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://physioswiss.ch/stelleninserate/?_per_page=5000")
        print("Scraper is ready!")
        page.wait_for_selector("article.tease-jobad")
        jobs = page.query_selector_all("article.tease-jobad")

        for job in jobs:
            employer_element = job.query_selector("p.tease-jobad__company")
            employer = employer_element.inner_text().strip() if employer_element else "N/A"
            title_element = job.query_selector("h2.tease-jobad__title")
            title = title_element.inner_text() if title_element else "N/A"
            link_element = job.query_selector("a.tease-jobad__link")
            url = link_element.get_attribute("href") if link_element else "N/A"
            number_element = job.query_selector("p.tease-jobad__number")
            job_number = parse_job_number(number_element.inner_text()) if number_element else "N/A"
            date_element = job.query_selector("p.tease-jobad__date time")
            parsed_date = parse_german_date(date_element.inner_text()) if date_element else "N/A"

            cursor.execute("SELECT job_number FROM jobs WHERE job_number = ?", (job_number,))
            exists = cursor.fetchone()

            if not exists:
                new_job = {
                    'job_number': job_number,
                    'date': parsed_date,
                    'employer': employer,
                    'title': title,
                    'url': url
                }
                new_jobs.append(new_job)
                print(f"\n🆕 NEW JOB FOUND!")
                print(f"Job Number: {job_number}")
                print(f"Date: {parsed_date}")
                print(f"Employer: {employer}")
                print(f"Title: {title}")
                print(f"URL: {url}")
                print("-" * 80)

                cursor.execute("""
                    INSERT INTO jobs (job_number, date, employer, title, url)
                    VALUES (?, ?, ?, ?, ?)
                """, (job_number, str(parsed_date), employer, title, url))

        browser.close()

    return new_jobs


def find_new_employers(new_jobs, existing_employers):
    if not new_jobs:
        return set()
    new_job_employers = {job['employer'] for job in new_jobs if job['employer'] != "N/A"}
    return new_job_employers - existing_employers


def report_results(new_jobs, new_employers):
    if new_jobs:
        print(f"\n✅ Found {len(new_jobs)} new job(s)!")
        for job in new_jobs:
            print(f"  - {job['job_number']}: {job['title']}")
    else:
        print(f"\n✅ No new jobs found. Database is up to date.")

    if new_employers:
        print(f"\n🏢 Found {len(new_employers)} new employer(s)!")
        for employer in sorted(new_employers):
            print(f"  - {employer}")

def build_report_text(new_jobs, new_employers):
    """Return report text instead of printing it."""

    lines = []

    if new_jobs:
        lines.append(f"Found {len(new_jobs)} new job(s):")
        for job in new_jobs:
            lines.append(f"- {job['job_number']}: {job['title']} ({job['employer']})")
            lines.append(f"  {job['url']}")
        lines.append("")  # spacing
    else:
        lines.append("No new jobs found. Database is up to date.\n")

    if new_employers:
        lines.append(f"Found {len(new_employers)} new employer(s):")
        for employer in sorted(new_employers):
            lines.append(f"- {employer}")
        lines.append("")

    return "\n".join(lines)

def send_email(subject: str, body: str):
    import smtplib
    from email.mime.text import MIMEText
    import os

    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))
    recipients = os.getenv("EMAIL_TO")

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = recipients

    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, recipients, msg.as_string())



def main():
    """Main entry point for the scraper"""
    conn, cursor, existing_employers = setup_database()
    
    new_jobs = scrape_new_jobs(cursor)
    
    conn.commit()
    conn.close()
    
    new_employers = find_new_employers(new_jobs, existing_employers)    
    
    report_results(new_jobs, new_employers)
    email_body = build_report_text(new_jobs, new_employers)     
    send_email("PhysioScraper Report", email_body)


if __name__ == "__main__":
    main()
