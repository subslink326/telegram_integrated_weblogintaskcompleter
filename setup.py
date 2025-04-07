import os
import subprocess
import sys
from pathlib import Path

def check_prerequisites():
    """Check if prerequisites are installed"""
    print("Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    
    # Check Redis
    try:
        subprocess.run(['redis-cli', '--version'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Warning: Redis is not installed")
    
    # Check ChromeDriver
    try:
        subprocess.run(['chromedriver', '--version'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Warning: ChromeDriver is not installed")

def create_virtualenv():
    """Create and activate virtual environment"""
    print("\nSetting up virtual environment...")
    
    # Create virtual environment
    subprocess.run(['python', '-m', 'venv', 'venv'])
    
    # Activate virtual environment
    if sys.platform == 'win32':
        activate_script = 'venv\Scripts\activate.bat'
    else:
        activate_script = 'source venv/bin/activate'
    
    print(f"\nActivate virtual environment with: {activate_script}")

def install_dependencies():
    """Install project dependencies"""
    print("\nInstalling dependencies...")
    
    # Install requirements
    subprocess.run(['pip', 'install', '-r', 'requirements.txt'])

def setup_redis():
    """Setup Redis"""
    print("\nSetting up Redis...")
    
    # Check if Redis is running
    try:
        subprocess.run(['redis-cli', 'ping'], check=True, capture_output=True)
        print("Redis is already running")
    except subprocess.CalledProcessError:
        print("Starting Redis...")
        # Start Redis in a separate process
        subprocess.Popen(['redis-server'])

def setup_chromedriver():
    """Setup ChromeDriver"""
    print("\nSetting up ChromeDriver...")
    
    # Check if ChromeDriver exists
    chromedriver_path = Path('chromedriver')
    if not chromedriver_path.exists():
        print("ChromeDriver not found. Please download and place it in the project root directory.")

def main():
    print("Welcome to Telegram Integrated Web Login Task Completer setup!")
    
    check_prerequisites()
    create_virtualenv()
    install_dependencies()
    setup_redis()
    setup_chromedriver()
    
    print("\nSetup completed successfully!")
    print("\nNext steps:")
    print("1. Activate the virtual environment")
    print("2. Create a .env file with your configuration")
    print("3. Start the application")

if __name__ == '__main__':
    main()
