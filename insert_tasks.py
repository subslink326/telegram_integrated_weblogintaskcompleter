#!/usr/bin/env python
import os
import sys
import time
import json
from datetime import datetime

# Add the backend directory to the path so we can import the task manager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from task_manager import TaskManager

def create_linkedin_task(name, email, password, keywords, location):
    """Create a LinkedIn job scraping task"""
    # Build job search URL
    keywords_encoded = keywords.replace(" ", "%20")
    location_encoded = location.replace(" ", "%20")
    job_search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords_encoded}&location={location_encoded}&f_TPR=r86400"
    
    # Create task data
    task_data = {
        'name': name,
        'type': 'linkedin_scraping',
        'status': 'pending',
        'credentials': {
            'email': email,
            'password': password
        },
        'job_search_url': job_search_url,
        'filters': {
            'date_posted': 'Past 24 hours',
            'job_type': 'Full-time',
            'experience_level': 'Entry level'
        },
        'max_jobs': 25
    }
    
    # Create the task
    task_manager = TaskManager()
    task = task_manager.create_task(task_data)
    return task

if __name__ == "__main__":
    # Create Arizona task
    az_task = create_linkedin_task(
        name="LinkedIn_Jobs_AE_B2B_Arizona",
        email="betacuckgpt@gmail.com",
        password="Svl7891!",
        keywords="Account executive b2b mis market sales",
        location="Arizona"
    )
    
    # Create Remote task
    remote_task = create_linkedin_task(
        name="LinkedIn_Jobs_AE_B2B_Remote",
        email="betacuckgpt@gmail.com",
        password="Svl7891!",
        keywords="Account executive b2b mis market sales",
        location="Remote"
    )
    
    print("Created LinkedIn job scraping tasks:")
    print(f"Arizona task ID: {az_task['id']}")
    print(f"Remote task ID: {remote_task['id']}")
    print("\nUse these IDs with the /scrape command in Telegram.")
    print("Example: /scrape " + az_task['id'])
