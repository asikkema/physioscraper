#!/usr/bin/env python3

"""
Delete the 10 most recent rows from the 'jobs' table based on the date column.
Useful for testing scraper behaviour with 'new jobs'.
"""

import sqlite3

DB_PATH = "jobs.db"

def delete_last_10_by_date():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Select last 10 jobs by date (descending)
    # Jobs with invalid dates ('N/A') are treated as very old via NULLIF()
    cursor.execute("""
        SELECT job_number, date
        FROM jobs
        ORDER BY 
            CASE 
                WHEN date = 'N/A' THEN 1
                ELSE 0
            END, 
            date DESC
        LIMIT 10
    """)

    rows = cursor.fetchall()

    if not rows:
        print("No rows found. Nothing to delete.")
        conn.close()
        return

    print("Deleting these rows:")
    for job_number, date in rows:
        print(f"  - {job_number} (date={date})")

    job_numbers_to_delete = [(row[0],) for row in rows]

    cursor.executemany("""
        DELETE FROM jobs
        WHERE job_number = ?
    """, job_numbers_to_delete)

    conn.commit()
    conn.close()

    print("Done! Deleted 10 most recent jobs based on date.")


if __name__ == "__main__":
    delete_last_10_by_date()
