# Telegram Integrated Web Login Task Completer

An automated web login task management system integrated with Telegram for remote control and monitoring of web automation tasks.

## Features

- Task management with creation, monitoring, and control
- Telegram bot integration for remote control
- Web automation capabilities
- Real-time task status updates
- Modern, responsive UI

## Prerequisites

- Python 3.8+
- Redis server
- Google Chrome browser
- ChromeDriver (compatible with Chrome version)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/telegram_integrated_weblogintaskcompleter.git
cd telegram_integrated_weblogintaskcompleter
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Redis:
```bash
# Install Redis (if not already installed)
brew install redis  # On macOS
redis-server  # Start Redis server
```

5. Configure environment:
- Copy `.env.example` to `.env`
- Update `.env` with your Telegram bot token
- Update ChromeDriver path if needed

## Running the Application

1. Start Redis server:
```bash
redis-server
```

2. Start the Flask application:
```bash
flask run
```

3. Start the Telegram bot:
```bash
python backend/telegram_bot.py
```

## Usage

1. Open your web browser and navigate to `http://localhost:5000`
2. Connect your Telegram bot using the "Connect Telegram Bot" button
3. Create new tasks using the "Create New Task" button
4. Monitor and control tasks through the web interface or Telegram bot

## Environment Variables

The application uses the following environment variables:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `REDIS_HOST`: Redis server host (default: localhost)
- `REDIS_PORT`: Redis server port (default: 6379)
- `CHROME_DRIVER_PATH`: Path to ChromeDriver executable
- `HEADLESS_MODE`: Run Chrome in headless mode (true/false)

## Security

- Keep your Telegram bot token secure
- Use HTTPS in production
- Implement proper authentication for API endpoints
- Regularly update dependencies

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
