#!/usr/bin/env python3
"""
Physiomatch website scraper
Scrapes job listings from https://physioswiss.ch/
"""

from playwright.sync_api import sync_playwright
from datetime import datetime
import re
import csv


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

        # Open CSV file for writing
        with open("jobs.csv", "w", newline="", encoding="utf-8") as csvfile:
            csv_writer = csv.writer(csvfile)
            # Write header
            csv_writer.writerow(["Job Number", "Date", "Title", "URL"])

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

                # Write to CSV
                csv_writer.writerow([job_number, parsed_date, title, url])

                # Print to console
                print(f"Job Number: {job_number}")
                print(f"Date: {parsed_date}")
                print(f"Title: {title}")
                print(f"URL: {url}")
                print("-" * 80)

        browser.close()


if __name__ == "__main__":
    main()
