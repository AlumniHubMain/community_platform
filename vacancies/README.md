# Vacancy Extractor

A Python-based service for extracting and processing job vacancies from multiple company career websites. The service uses Playwright for web scraping, PostgreSQL for data storage, and Google Cloud Platform for deployment.

## Features

- Concurrent extraction of vacancy links from multiple sources
- Support for multiple companies (Booking, InDrive, Wargaming)
- Automated pagination handling
- Structured data storage in PostgreSQL
- Cloud SQL integration
- LLM-powered vacancy content parsing

## Tech Stack

- Python 3.12+
- PostgreSQL
- Playwright
- SQLAlchemy
- Pydantic
- Google Cloud Platform
- LangChain with Vertex AI

## Project Structure

```tree
vacancies/
├── app/
│   ├── core/
│   │   ├── link_extractor/     # Company-specific link extractors
│   │   └── data_extractor/     # Vacancy content extraction
│   ├── db/                 # Database models and repositories
│   ├── config/            # Application configuration
│   └── main.py           # Main application entry point
├── notebooks/            # Jupyter notebooks for development
├── Dockerfile           # Container configuration
├── pyproject.toml      # Project dependencies
└── README.md
```

## Installation

1. Clone the repository
2. Install dependencies using UV:

```bash
uv sync
```

## Configuration

The application requires the following environment variables:

- `DB_NAME`: PostgreSQL database name this is not production secret, only development
- `DB_USER`: Database user this is not production secret, only development
- `DB_PASS`: Database password this is not production secret, only development
- `INSTANCE_CONNECTION_NAME`: Cloud SQL instance connection name (for GCP deployment) production and development
- `BACKEND_CREDENTIALS`: JSON string containing database credentials this is only production secret

## Development

To run the application locally:

```shell
python -m app.main
```

### VS Code Development

For development in VS Code, you can use one of the following launch configurations. Create or update `.vscode/launch.json`:

#### Container-based configuration

```json
{
    "image": "vacancies",
    "service": {
        "name": "vacancies",
        "containerPort": 8080,
        "resources": {
            "limits": {
                "cpu": 1,
                "memory": "512Mi"
            }
        },
        "env": [
            {
                "name": "INSTANCE_CONNECTION_NAME",
                "value": "communityp-440714:us-central1:community-platform"
            },
            {
                "name": "DB_USER",
                "value": "postgres"
            },
            {
                "name": "DB_PASS",
                "value": "Fmq-Czs-hu5-Luy"
            },
            {
                "name": "DB_NAME",
                "value": "production"
            },
            {
                "name": "PYTHONPATH",
                "value": "/app"
            },
            {
                "name": "PYDEVD_DISABLE_FILE_VALIDATION",
                "value": "1"
            },
            {
                "name": "PYTHONARGS",
                "value": "-Xfrozen_modules=off"
            }
        ]
    },
    "target": {
        "minikube": {}
    },
    "watch": true,
    "debug": {
        "sourceFileMap": {
            "${workspaceFolder}/vacancies": "/app"
        },
        "pythonPath": "python3"
    }
}
```

#### Local development configuration

```json
{
    "name": "Python: Main",
    "type": "debugpy",
    "request": "launch",
    "program": "${workspaceFolder}/vacancies/app/main.py",
    "console": "integratedTerminal",
    "justMyCode": true,
    "env": {
        "PYTHONPATH": "${workspaceFolder}/vacancies"
    },
    "cwd": "${workspaceFolder}/vacancies"
}
```

The first configuration runs the application in a containerized environment, while the second one runs it directly on your local machine.

## Deployment

Deploy to Google Cloud Platform using:

```shell
gcloud builds submit --region=us-east4 --tag us-east4-docker.pkg.dev/communityp-440714/extractor-vacancies/vacancies-app:latest
```

## Extractors

The application includes extractors for the following companies:

- Booking.com (`BookingLinkExtractor`)
- InDrive (`InDriveLinkExtractor`)
- Wargaming (`WargamingLinkExtractor`)

Each extractor implements the `BaseLinkExtractor` interface and handles company-specific webpage structures and pagination.

## Database Schema

The vacancy data is stored in a PostgreSQL database with the following main fields:

- Basic information (title, description, URL)
- Skills and requirements
- Location and remote work options
- Salary information
- Company and department details
- Timestamps for tracking updates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
