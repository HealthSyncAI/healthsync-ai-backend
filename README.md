# HealthSync AI Backend

Welcome to HealthSync AI, a production-ready healthcare application backend built with FastAPI. This document explains how to set up your development environment, run the backend server, and execute tests.

## Prerequisites

- [Docker](https://www.docker.com/) installed on your system
- Python 3.8+ installed locally
- Git for cloning the repository

## Getting Started

### 1. Clone the Repository
Clone the repository and navigate to the project directory:
```bash
git clone https://github.com/HealthSyncAI/healthsync-ai-backend.git
cd healthsync_ai
```

### 2. Set Up the Databases with Docker
For local development, start the PostgreSQL container with:
```angular2html
# Local (production use)
docker run --name healthsync-postgres \
  -e POSTGRES_USER=myuser \
  -e POSTGRES_PASSWORD=mypassword \
  -e POSTGRES_DB=healthsync_db \
  -p 5432:5432 \
  -d postgres
```
For testing purposes, run a separate PostgreSQL container (Optional):
```angular2html
# Test environment
docker run --name healthsync-postgres-test \
  -e POSTGRES_USER=myuser \
  -e POSTGRES_PASSWORD=mypassword \
  -e POSTGRES_DB=healthsync_db_test \
  -p 5433:5432 \
  -d postgres
```

### 3. Set Up the Python Environment
Create and activate a virtual environment, then install dependencies:
```angular2html
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export PYTHONPATH="."
python app/db/create_tables.py
```
### 4. Run the Backend Server
Start the backend server using Uvicorn with live reload enabled:
```angular2html
uvicorn app.main:app --reload
```
Your backend will be accessible at http://127.0.0.1:8000. 
To explore the API, visit the 
- automatically generated [Swagger documentation](http://127.0.0.1:8000/docs).
- postman [Postman documentation](https://documenter.getpostman.com/view/21095095/2sAYX8JML3)

### 5. Database Migrations (Alembic)
This project uses Alembic to manage database schema changes.
When you make changes to your SQLAlchemy models (files in app/models/), you need to generate a new migration script:
- Ensure your development database is running.
- Generate the migration script:
    ```angular2html
    alembic revision --autogenerate -m "Add new_field to User model"
    ```
- Review the generated script: Alembic will create a new file in alembic/versions/. Open this file and check that the upgrade() and downgrade() functions correctly reflect the changes you intended. Modify if necessary.
- Apply the migration:
    ```angular2html
    alembic upgrade head
    ```

### 6. Run the Tests (Optional)
You can run the tests using Pytest. For example:
```angular2html
pytest -v tests/test_appointment.py
pytest -v tests/test_auth.py
pytest -v tests/test_crud_schema.py
pytest -v tests/test_get_chatbot.py
pytest -v tests/test_health_record
pytest -v tests/test_post_chatbot.py
pytest -v tests/test_statistics.py
```
### 7. Performance Testing (Locust)
A locustfile.py is included for performance testing.
- Ensure the backend server is running.
- Install Locust (it's included in requirements.txt).
- Run Locust:
```angular2html
locust -f locustfile.py --host http://127.0.0.1:8000
```
License
This project is licensed under the MIT License - see the LICENSE file for details.


Make sure your environment variables (e.g., in the .env.sample file) are properly configured.