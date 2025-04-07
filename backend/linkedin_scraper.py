import os
import time
import json
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from cryptography.fernet import Fernet

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class LinkedInJobScraper:
    def __init__(self, task_id, credentials=None, notification_handler=None):
        """
        Initialize the LinkedIn job scraper
        
        Args:
            task_id (str): Unique identifier for this task
            credentials (dict): Dictionary containing email and password
            notification_handler (callable): Function to call for notifications
        """
        self.task_id = task_id
        self._credentials = credentials
        self.notification_handler = notification_handler
        self.driver = None
        self.jobs_data = []
        self.last_run = None
        self.status = "initialized"
        self.progress = 0
        self._setup_encryption()
        
    def _setup_encryption(self):
        """Set up encryption for credentials"""
        # In production, this key should be securely stored and retrieved
        key = Fernet.generate_key() if not os.path.exists('key.key') else self._load_key()
        if not os.path.exists('key.key'):
            with open('key.key', 'wb') as key_file:
                key_file.write(key)
        self.cipher = Fernet(key)
    
    def _load_key(self):
        """Load the encryption key"""
        with open('key.key', 'rb') as key_file:
            return key_file.read()
    
    def set_credentials(self, email, password):
        """Securely set LinkedIn credentials"""
        self._credentials = {
            'email': email,
            'password': password
        }
        
    def _encrypt_credentials(self):
        """Encrypt the credentials for storage"""
        if not self._credentials:
            return None
        
        encrypted_data = {
            'email': self.cipher.encrypt(self._credentials['email'].encode()).decode(),
            'password': self.cipher.encrypt(self._credentials['password'].encode()).decode()
        }
        return encrypted_data
    
    def _decrypt_credentials(self, encrypted_data):
        """Decrypt the credentials from storage"""
        if not encrypted_data:
            return None
            
        decrypted_data = {
            'email': self.cipher.decrypt(encrypted_data['email'].encode()).decode(),
            'password': self.cipher.decrypt(encrypted_data['password'].encode()).decode()
        }
        return decrypted_data
    
    def save_credentials(self, filename=None):
        """Save encrypted credentials to file"""
        if not filename:
            filename = f"credentials_{self.task_id}.json"
            
        encrypted_data = self._encrypt_credentials()
        with open(filename, 'w') as f:
            json.dump(encrypted_data, f)
            
    def load_credentials(self, filename=None):
        """Load encrypted credentials from file"""
        if not filename:
            filename = f"credentials_{self.task_id}.json"
            
        if not os.path.exists(filename):
            return False
            
        with open(filename, 'r') as f:
            encrypted_data = json.load(f)
            
        self._credentials = self._decrypt_credentials(encrypted_data)
        return True
    
    def initialize_driver(self):
        """Initialize the Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.status = "driver_initialized"
        self.progress = 5
        logger.info(f"Task {self.task_id}: WebDriver initialized")
        
    def login(self):
        """Log in to LinkedIn"""
        if not self._credentials:
            self.status = "error"
            logger.error(f"Task {self.task_id}: No credentials provided")
            raise ValueError("No credentials provided")
            
        try:
            self.driver.get("https://www.linkedin.com/login")
            
            # Wait for the login page to load
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            
            # Enter email
            email_field.send_keys(self._credentials['email'])
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self._credentials['password'])
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, ".login__form_action_container button")
            login_button.click()
            
            # Wait for login to complete
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".global-nav__me"))
            )
            
            self.status = "logged_in"
            self.progress = 20
            logger.info(f"Task {self.task_id}: Successfully logged in to LinkedIn")
            
            # Check for security verification
            self._check_security_verification()
            
            return True
            
        except TimeoutException:
            self.status = "login_failed"
            logger.error(f"Task {self.task_id}: Login timed out")
            if self.notification_handler:
                self.notification_handler(f"❌ Login failed: Timeout when logging in to LinkedIn")
            return False
            
        except Exception as e:
            self.status = "login_failed"
            logger.error(f"Task {self.task_id}: Login failed - {str(e)}")
            if self.notification_handler:
                self.notification_handler(f"❌ Login failed: {str(e)}")
            return False
    
    def _check_security_verification(self):
        """Check if LinkedIn is requesting security verification"""
        try:
            # Check for security verification page
            security_check = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".security-check"))
            )
            
            self.status = "security_verification_required"
            logger.warning(f"Task {self.task_id}: Security verification required")
            if self.notification_handler:
                self.notification_handler("⚠️ Security verification required on LinkedIn. Please complete it manually.")
                
        except TimeoutException:
            # No security verification needed
            pass
    
    def navigate_to_jobs(self, job_search_url=None):
        """Navigate to LinkedIn Jobs section with specified filters"""
        if not job_search_url:
            # Default job search URL (software engineering in San Francisco)
            job_search_url = "https://www.linkedin.com/jobs/search/?keywords=software%20engineer&location=San%20Francisco%20Bay%20Area&f_TPR=r86400"
        
        try:
            self.driver.get(job_search_url)
            
            # Wait for job results to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search__results-list"))
            )
            
            self.status = "navigated_to_jobs"
            self.progress = 40
            logger.info(f"Task {self.task_id}: Navigated to jobs page")
            return True
            
        except TimeoutException:
            self.status = "navigation_failed"
            logger.error(f"Task {self.task_id}: Failed to load jobs page")
            if self.notification_handler:
                self.notification_handler("❌ Failed to load LinkedIn jobs page")
            return False
    
    def apply_filters(self, filters=None):
        """Apply job search filters"""
        default_filters = {
            "date_posted": "Past 24 hours",
            "job_type": "Full-time",
            "experience_level": "Entry level"
        }
        
        active_filters = filters if filters else default_filters
        
        try:
            # Click on filter buttons and apply filters
            self._apply_date_filter(active_filters.get("date_posted", "Past 24 hours"))
            self._apply_job_type_filter(active_filters.get("job_type", "Full-time"))
            self._apply_experience_filter(active_filters.get("experience_level", "Entry level"))
            
            # Wait for results to refresh
            time.sleep(2)
            
            self.status = "filters_applied"
            self.progress = 60
            logger.info(f"Task {self.task_id}: Applied job filters")
            return True
            
        except Exception as e:
            logger.error(f"Task {self.task_id}: Failed to apply filters - {str(e)}")
            # Continue anyway
            return False
    
    def _apply_date_filter(self, date_option):
        """Apply date posted filter"""
        try:
            # Click on date posted filter dropdown
            date_filter = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Date posted')]"))
            )
            date_filter.click()
            
            # Select the date option
            date_option_element = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, f"//label[contains(.,'{date_option}')]"))
            )
            date_option_element.click()
            
            # Apply filter
            apply_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Apply')]"))
            )
            apply_button.click()
            
        except (TimeoutException, NoSuchElementException) as e:
            logger.warning(f"Failed to apply date filter: {str(e)}")
    
    def _apply_job_type_filter(self, job_type):
        """Apply job type filter"""
        try:
            # Click on job type filter dropdown
            job_type_filter = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Job type')]"))
            )
            job_type_filter.click()
            
            # Select the job type option
            job_type_option = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, f"//label[contains(.,'{job_type}')]"))
            )
            job_type_option.click()
            
            # Apply filter
            apply_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Apply')]"))
            )
            apply_button.click()
            
        except (TimeoutException, NoSuchElementException) as e:
            logger.warning(f"Failed to apply job type filter: {str(e)}")
    
    def _apply_experience_filter(self, experience_level):
        """Apply experience level filter"""
        try:
            # Click on experience level filter dropdown
            exp_filter = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Experience level')]"))
            )
            exp_filter.click()
            
            # Select the experience level option
            exp_option = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, f"//label[contains(.,'{experience_level}')]"))
            )
            exp_option.click()
            
            # Apply filter
            apply_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Apply')]"))
            )
            apply_button.click()
            
        except (TimeoutException, NoSuchElementException) as e:
            logger.warning(f"Failed to apply experience filter: {str(e)}")
    
    def scrape_jobs(self, max_jobs=25):
        """Scrape job listings"""
        self.jobs_data = []
        
        try:
            # Get job listings
            job_listings = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".jobs-search__results-list li"))
            )
            
            # Limit to maximum number of jobs
            job_listings = job_listings[:min(len(job_listings), max_jobs)]
            
            for i, job_listing in enumerate(job_listings):
                try:
                    # Extract job details
                    title_element = job_listing.find_element(By.CSS_SELECTOR, "h3.base-search-card__title")
                    company_element = job_listing.find_element(By.CSS_SELECTOR, "h4.base-search-card__subtitle")
                    location_element = job_listing.find_element(By.CSS_SELECTOR, ".job-search-card__location")
                    job_link_element = job_listing.find_element(By.CSS_SELECTOR, "a.base-card__full-link")
                    
                    # Get job details
                    job_data = {
                        "id": f"linkedin_job_{int(time.time())}_{i}",
                        "title": title_element.text.strip(),
                        "company": company_element.text.strip(),
                        "location": location_element.text.strip(),
                        "url": job_link_element.get_attribute("href"),
                        "scraped_at": datetime.now().isoformat()
                    }
                    
                    # Try to get posted date
                    try:
                        date_element = job_listing.find_element(By.CSS_SELECTOR, ".job-search-card__listdate")
                        job_data["posted_date"] = date_element.get_attribute("datetime")
                    except:
                        job_data["posted_date"] = "Unknown"
                    
                    self.jobs_data.append(job_data)
                    
                    # Update progress
                    self.progress = 60 + int((i + 1) / len(job_listings) * 30)
                    
                except Exception as e:
                    logger.warning(f"Failed to extract job details: {str(e)}")
                    continue
            
            self.status = "jobs_scraped"
            self.progress = 90
            logger.info(f"Task {self.task_id}: Scraped {len(self.jobs_data)} jobs")
            return self.jobs_data
            
        except Exception as e:
            self.status = "scraping_failed"
            logger.error(f"Task {self.task_id}: Failed to scrape jobs - {str(e)}")
            if self.notification_handler:
                self.notification_handler(f"❌ Failed to scrape jobs: {str(e)}")
            return []
    
    def save_results(self, filename=None):
        """Save job results to a file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"linkedin_jobs_{timestamp}.json"
            
        try:
            with open(filename, 'w') as f:
                json.dump(self.jobs_data, f, indent=2)
                
            self.status = "results_saved"
            self.progress = 95
            logger.info(f"Task {self.task_id}: Saved {len(self.jobs_data)} job results to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Task {self.task_id}: Failed to save results - {str(e)}")
            return False
    
    def send_notifications(self):
        """Send notifications about job results"""
        if not self.notification_handler or not self.jobs_data:
            return
            
        try:
            # Send summary notification
            summary = f"🔍 Found {len(self.jobs_data)} LinkedIn job listings!"
            self.notification_handler(summary)
            
            # Send details for top 5 jobs
            top_jobs = self.jobs_data[:5]
            for job in top_jobs:
                job_details = (
                    f"💼 *{job['title']}*\n"
                    f"🏢 {job['company']}\n"
                    f"📍 {job['location']}\n"
                    f"🔗 [View Job]({job['url']})"
                )
                self.notification_handler(job_details)
                
            self.status = "notifications_sent"
            self.progress = 100
            logger.info(f"Task {self.task_id}: Sent job notifications")
            return True
            
        except Exception as e:
            logger.error(f"Task {self.task_id}: Failed to send notifications - {str(e)}")
            return False
    
    def run(self, job_search_url=None, filters=None, max_jobs=25):
        """Run the complete LinkedIn job scraping task"""
        try:
            self.initialize_driver()
            
            if not self.login():
                self.cleanup()
                return False
                
            if not self.navigate_to_jobs(job_search_url):
                self.cleanup()
                return False
                
            self.apply_filters(filters)
            scraped_jobs = self.scrape_jobs(max_jobs)
            
            if scraped_jobs:
                self.save_results()
                self.send_notifications()
                
            self.cleanup()
            self.last_run = datetime.now().isoformat()
            return True
            
        except Exception as e:
            self.status = "task_failed"
            logger.error(f"Task {self.task_id}: Task failed - {str(e)}")
            if self.notification_handler:
                self.notification_handler(f"❌ Task failed: {str(e)}")
                
            self.cleanup()
            return False
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info(f"Task {self.task_id}: WebDriver closed")
            
    def get_status(self):
        """Get current task status"""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "progress": self.progress,
            "jobs_found": len(self.jobs_data) if self.jobs_data else 0,
            "last_run": self.last_run
        }
