web: python -m alembic upgrade head && gunicorn api.main:app --workers 3 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
