# Bingo Game Backend

## Overview
This is the backend repository for the Bingo Game application. It is built using Django and Django Channels, with PostgreSQL as the database and Redis as the channel layer for handling real-time communication and offline update queues.

## Technologies Used
- **Django** - Web framework for backend logic
- **Django Channels** - WebSockets and real-time messaging
- **PostgreSQL** - Relational database for persistent data storage
- **Redis** - Used for offline update queues and as a Django Channels layer

## Features
- WebSocket-based real-time communication
- Offline update queuing with Redis
- PostgreSQL database for storing game states and user data
- Redis-backed Django Channels for message queuing
- Sentry logging for real-time feedback

## Setup Instructions

### Prerequisites
Ensure you have the following installed:
- Python 3.11
- PostgreSQL
- Redis
- poetry

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/keisler-au/bingo-backend.git
  ```

2. **Set up the Postgres and Redis servers:**
   Ensure Postgres and Redis is running locally or use a remote Redis instance.

3. **Prepare the environment:**
   ```
   ./build.sh
   ```

4. **Run the Django development server:**
   ```
   poetry run daphne -b 0.0.0.0 -p 8000 app.asgi:application
   ```

## Environment Variables
Create a `.env` file and define required environment variables such as:
```
SECRET_KEY=

REDIS_HOST=
REDIS_PORT=6379
REDIS_PASSWORD=

DB_NAME=
DB_USERNAME=
DB_PASSWORD=
POSTGRES_PASSWORD=
DB_HOST=
DB_PORT=

SENTRY_DNS=

```

## Running Tests
```
poetry run python manage.py test
```

## Contributing
1. Fork the repo
2. Create a new branch (`feature-branch`)
3. Commit your changes
4. Push to your branch and create a pull request

## Contact
For any issues, open a GitHub issue or reach out to `joshkeisler.au@gmail.com`.
