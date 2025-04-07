from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from task_manager import TaskManager
import logging
import os

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.task_manager = TaskManager()
        self.updater = None
        self.initialize_bot()

    def initialize_bot(self):
        # Directly use the token instead of getting from environment variable
        token = "7659581133:AAEYMsKZKSTai0bIh_PC17RZY2CPXY6ajmc"

        self.updater = Updater(token)
        dp = self.updater.dispatcher
        
        # Add command handlers
        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("help", self.help_command))
        dp.add_handler(CommandHandler("status", self.status))
        dp.add_handler(CommandHandler("create", self.create_task))
        dp.add_handler(CommandHandler("linkedin", self.linkedin_command))
        dp.add_handler(CommandHandler("scrape", self.start_scraping))
        
        # Add preset job search commands
        dp.add_handler(CommandHandler("jobs_arizona", self.preset_jobs_arizona))
        dp.add_handler(CommandHandler("jobs_remote", self.preset_jobs_remote))
        dp.add_handler(CommandHandler("run_all_searches", self.run_all_job_searches))
        
        # Add message handler
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))

    def start(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        update.message.reply_html(
            f"Hi {user.mention_html()}! I'm your web automation assistant.\n"
            "Use /help to see available commands."
        )

    def help_command(self, update: Update, context: CallbackContext) -> None:
        """Send a message when the command /help is issued."""
        help_text = (
            "*Available Commands:*\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/status - Get current task status\n"
            "/create - Create a new web automation task\n"
            "/linkedin - Create custom LinkedIn job scraping task\n"
            "/scrape - Start a LinkedIn job scraping task\n\n"
            
            "*Preset Job Search Commands:*\n"
            "/jobs_arizona - Search for Account Executive jobs in Arizona\n"
            "/jobs_remote - Search for Account Executive jobs with Remote option\n"
            "/run_all_searches - Run all preset job searches\n"
        )
        update.message.reply_markdown(help_text)

    def status(self, update: Update, context: CallbackContext) -> None:
        """Send task status when the command /status is issued."""
        status = self.task_manager.get_all_tasks()
        if not status:
            update.message.reply_text("No tasks available.")
            return
            
        response = "*Current Tasks:*\n\n"
        for task in status:
            response += f"• {task['name']} - {task['status']}\n"
        update.message.reply_markdown(response)

    def create_task(self, update: Update, context: CallbackContext) -> None:
        """Handle task creation command."""
        if len(context.args) < 2:
            update.message.reply_text(
                "Usage: /create <task_name> <url>"
            )
            return

        task_name = context.args[0]
        url = context.args[1]
        
        task = self.task_manager.create_task({
            'name': task_name,
            'url': url,
            'status': 'pending'
        })
        
        update.message.reply_text(f"Task created: {task_name}")

    def handle_message(self, update: Update, context: CallbackContext) -> None:
        """Handle regular messages."""
        text = update.message.text
        update.message.reply_text(f"Received: {text}")
    
    def linkedin_command(self, update: Update, context: CallbackContext) -> None:
        """Handle LinkedIn job scraping setup"""
        if len(context.args) < 3:
            update.message.reply_text(
                "Usage: /linkedin <email> <password> <job_search_keywords> [<location>]\n\n"
                "Example: /linkedin myemail@example.com mypassword 'software engineer' 'San Francisco'\n\n"
                "Note: This command creates a LinkedIn job scraping task but doesn't start it yet."
                "Use /scrape to start the task after creation."
            )
            return

        # Get credentials and job search parameters
        email = context.args[0]
        password = context.args[1]
        keywords = context.args[2]
        location = context.args[3] if len(context.args) > 3 else "United States"
        
        # Build job search URL
        keywords_encoded = keywords.replace(" ", "%20")
        location_encoded = location.replace(" ", "%20")
        job_search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords_encoded}&location={location_encoded}&f_TPR=r86400"
        
        # Create task data
        task_data = {
            'name': f"LinkedIn_Jobs_{keywords}_{location}",
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
        task = self.task_manager.create_task(task_data)
        
        update.message.reply_text(
            f"✅ LinkedIn job scraping task created!\n"
            f"Task ID: {task['id']}\n"
            f"Search: {keywords} in {location}\n\n"
            f"Use /scrape {task['id']} to start scraping jobs."
        )
    
    def start_scraping(self, update: Update, context: CallbackContext) -> None:
        """Start a LinkedIn job scraping task"""
        if not context.args:
            # List tasks that can be scraped
            tasks = [t for t in self.task_manager.get_all_tasks() if t.get('type') == 'linkedin_scraping']
            
            if not tasks:
                update.message.reply_text("No LinkedIn scraping tasks found. Create one with /linkedin command first.")
                return
                
            response = "*Available LinkedIn scraping tasks:*\n\n"
            for task in tasks:
                response += f"• ID: {task['id']} - {task['name']} - {task['status']}\n"
            response += "\nUse /scrape <task_id> to start scraping."
            update.message.reply_markdown(response)
            return
        
        # Get task ID
        task_id = context.args[0]
        task = self.task_manager.get_task(task_id)
        
        if not task:
            update.message.reply_text(f"❌ Task with ID {task_id} not found.")
            return
            
        if task.get('type') != 'linkedin_scraping':
            update.message.reply_text(f"❌ Task with ID {task_id} is not a LinkedIn scraping task.")
            return
            
        # Start the task
        success = self.task_manager.start_task(task_id)
        
        if success:
            update.message.reply_text(
                f"🚀 Started LinkedIn job scraping for '{task['name']}'\n"
                f"This will run in the background. You'll receive notifications when new jobs are found!\n\n"
                f"Check status with /status"
            )
        else:
            update.message.reply_text(f"❌ Failed to start task {task_id}. It might already be running.")

    def preset_jobs_arizona(self, update: Update, context: CallbackContext) -> None:
        """Preset command to search for Account Executive jobs in Arizona"""
        # Predefined parameters
        email = "betacuckgpt@gmail.com"
        password = "Svl7891!"
        keywords = "Account executive b2b mis market sales"
        location = "Arizona"
        
        # Build job search URL
        keywords_encoded = keywords.replace(" ", "%20")
        location_encoded = location.replace(" ", "%20")
        job_search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords_encoded}&location={location_encoded}&f_TPR=r86400"
        
        # Create task data
        task_data = {
            'name': f"LinkedIn_Jobs_AE_B2B_Arizona",
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
        task = self.task_manager.create_task(task_data)
        
        # Automatically start the task
        success = self.task_manager.start_task(task['id'])
        
        if success:
            update.message.reply_text(
                f"🚀 Started LinkedIn job search for Account Executive positions in Arizona!\n"
                f"Task ID: {task['id']}\n\n"
                f"I'll notify you when I find matching jobs."
            )
        else:
            update.message.reply_text(f"❌ Failed to start the job search. Please try again later.")

    def preset_jobs_remote(self, update: Update, context: CallbackContext) -> None:
        """Preset command to search for Account Executive jobs with Remote option"""
        # Predefined parameters
        email = "betacuckgpt@gmail.com"
        password = "Svl7891!"
        keywords = "Account executive b2b mis market sales"
        location = "Remote"
        
        # Build job search URL
        keywords_encoded = keywords.replace(" ", "%20")
        location_encoded = location.replace(" ", "%20")
        job_search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords_encoded}&location={location_encoded}&f_TPR=r86400"
        
        # Create task data
        task_data = {
            'name': f"LinkedIn_Jobs_AE_B2B_Remote",
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
        task = self.task_manager.create_task(task_data)
        
        # Automatically start the task
        success = self.task_manager.start_task(task['id'])
        
        if success:
            update.message.reply_text(
                f"🚀 Started LinkedIn job search for Remote Account Executive positions!\n"
                f"Task ID: {task['id']}\n\n"
                f"I'll notify you when I find matching jobs."
            )
        else:
            update.message.reply_text(f"❌ Failed to start the job search. Please try again later.")
    
    def run_all_job_searches(self, update: Update, context: CallbackContext) -> None:
        """Run all preset job searches at once"""
        update.message.reply_text("Starting all job searches...")
        
        # Run Arizona job search
        self.preset_jobs_arizona(update, context)
        
        # Run Remote job search
        self.preset_jobs_remote(update, context)
        
        update.message.reply_text(
            "✅ All job searches are now running in the background.\n"
            "You'll be notified when results are available.\n\n"
            "Check status anytime with /status"
        )
        
    def run(self):
        """Start the bot."""
        self.updater.start_polling()
        print("Bot started! Press Ctrl+C to stop.")
        self.updater.idle()

if __name__ == '__main__':
    bot = TelegramBot()
    bot.run()
