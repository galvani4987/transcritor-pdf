from celery import Celery

# TODO: Make broker and backend URLs configurable via environment variables
# For now, using localhost for Redis. This assumes Redis is running.
# In a Dockerized setup (e.g., with modular-dashboard-adv), this would be 'redis://redis:6379/0'
# if the Redis service is named 'redis'.

celery_app = Celery(
    'transcritor_pdf', # Using the project name as the main app name
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1', # Using a different DB for backend
    include=['src.tasks'] # List of modules to import when worker starts
)

# Optional Celery configuration
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    # visibility_timeout might be important if tasks are long
    # broker_transport_options={'visibility_timeout': 3600*4}, # 4 hours example
    result_expires=3600 * 24, # Expire results after 24 hours
)

if __name__ == '__main__':
    celery_app.start()
