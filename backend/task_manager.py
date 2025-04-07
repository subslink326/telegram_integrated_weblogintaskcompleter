from datetime import datetime
import json
from typing import Dict, List, Optional
import redis
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import logging
from linkedin_scraper import LinkedInJobScraper
import os

class TaskManager:
    def __init__(self):
        self.redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=int(os.getenv('REDIS_PORT', 6379)), db=0)
        self.tasks = {}
        self.load_tasks()
        self.scrapers = {}

    def load_tasks(self):
        """Load tasks from Redis"""
        tasks_data = self.redis_client.get('tasks')
        if tasks_data:
            self.tasks = json.loads(tasks_data)

    def save_tasks(self):
        """Save tasks to Redis"""
        self.redis_client.set('tasks', json.dumps(self.tasks))

    def create_task(self, task_data: Dict) -> Dict:
        """Create a new task"""
        task_id = str(int(time.time()))
        task_data['id'] = task_id
        task_data['created'] = datetime.now().isoformat()
        task_data['updated'] = datetime.now().isoformat()
        task_data['progress'] = 0
        
        # Add default task type if not specified
        if 'type' not in task_data:
            task_data['type'] = 'generic'
            
        # Initialize task-specific properties
        if task_data['type'] == 'linkedin_scraping':
            task_data['job_search_url'] = task_data.get('job_search_url', '')
            task_data['filters'] = task_data.get('filters', {})
            task_data['max_jobs'] = task_data.get('max_jobs', 25)
            task_data['results'] = []
            
            # Create LinkedIn scraper instance
            if 'credentials' in task_data:
                self._setup_linkedin_scraper(task_id, task_data)
        
        self.tasks[task_id] = task_data
        self.save_tasks()
        return task_data

    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get a task by ID"""
        return self.tasks.get(task_id)
        
    def _setup_linkedin_scraper(self, task_id, task_data):
        """Setup LinkedIn scraper for a task"""
        try:
            # Create notification handler for Telegram updates
            def notification_handler(message):
                # This function will be implemented in telegram_bot.py
                # to send notifications to the user
                print(f"Notification: {message}")
                
            # Initialize LinkedIn scraper
            scraper = LinkedInJobScraper(
                task_id=task_id,
                credentials=task_data.get('credentials'),
                notification_handler=notification_handler
            )
            
            # Store scraper reference
            self.scrapers[task_id] = scraper
            
            return True
        except Exception as e:
            logging.error(f"Failed to setup LinkedIn scraper: {str(e)}")
            return False

    def get_all_tasks(self) -> List[Dict]:
        """Get all tasks"""
        return list(self.tasks.values())

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get status of a specific task"""
        task = self.get_task(task_id)
        if task:
            return {
                'id': task['id'],
                'name': task.get('name', 'Unnamed Task'),
                'status': task.get('status', 'pending'),
                'progress': task.get('progress', 0)
            }
        return None

    def update_task(self, task_id: str, data: Dict) -> Optional[Dict]:
        """Update a task"""
        task = self.get_task(task_id)
        if task:
            task.update(data)
            task['updated'] = datetime.now().isoformat()
            self.save_tasks()
            return task
        return None

    def delete_task(self, task_id: str):
        """Delete a task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.save_tasks()

    def execute_task(self, task_id: str):
        """Execute a web automation task"""
        task = self.get_task(task_id)
        if not task:
            return

        try:
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')

            # Initialize WebDriver
            driver = webdriver.Chrome(options=chrome_options)
            
            # Navigate to URL
            driver.get(task['url'])
            
            # Execute actions
            for action in task['actions']:
                if action['type'] == 'click':
                    element = driver.find_element(By.CSS_SELECTOR, action['selector'])
                    element.click()
                elif action['type'] == 'type':
                    element = driver.find_element(By.CSS_SELECTOR, action['selector'])
                    element.send_keys(action['value'])
                
                # Update progress
                self.update_task(task_id, {
                    'status': 'running',
                    'progress': (task['actions'].index(action) + 1) / len(task['actions']) * 100
                })
                
                # Wait between actions
                time.sleep(1)

            # Mark task as completed
            self.update_task(task_id, {
                'status': 'completed',
                'progress': 100
            })

        except Exception as e:
            self.update_task(task_id, {
                'status': 'error',
                'error_message': str(e)
            })
        finally:
            driver.quit()

    def get_task_by_id(self, task_id: str) -> Optional[Dict]:
        """Get task by ID"""
        for task in self.tasks:
            if task['id'] == task_id:
                return task
        return None
