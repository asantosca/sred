@echo off
REM Start Celery worker for SR&ED Intelligence

echo Starting Celery worker...
echo.

REM Activate virtual environment
call venv\Scripts\activate

REM Start Celery worker with document_processing queue
celery -A app.core.celery_app worker --loglevel=info --pool=solo --queues=document_processing

pause
