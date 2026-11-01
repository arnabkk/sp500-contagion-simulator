"""Production entry point for hosting (e.g. Render): `gunicorn app:server`."""
from visualization import create_app

app = create_app('sp500_covid_data.json', 0.7)
server = app.server
