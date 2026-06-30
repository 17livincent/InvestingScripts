import os
from pathlib import Path

from sqlalchemy import URL, create_engine


ENV_FILE_PATH = Path(__file__).resolve().parent / ".env"


def load_env_file(env_file_path=ENV_FILE_PATH):
    if not env_file_path.exists():
        return

    with env_file_path.open("r") as env_file:
        for line in env_file:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith("#") or "=" not in stripped_line:
                continue

            key, value = stripped_line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")

            if key and key not in os.environ:
                os.environ[key] = value


def get_env_value(*names, default=None):
    for name in names:
        value = os.environ.get(name)
        if value:
            return value

    return default


def get_db_engine():
    load_env_file()

    database_url = get_env_value("INVESTING_DATABASE_URL")
    if database_url:
        return create_engine(database_url)

    connection_url = URL.create(
        "postgresql+psycopg2",
        username=get_env_value("INVESTING_DB_USER", "POSTGRES_USER", default="investing"),
        password=get_env_value("INVESTING_DB_PASSWORD", "POSTGRES_PASSWORD", default="investing"),
        host=get_env_value("INVESTING_DB_HOST", "POSTGRES_HOST", default="localhost"),
        port=int(get_env_value("INVESTING_DB_PORT", "POSTGRES_PORT", default="5432")),
        database=get_env_value("INVESTING_DB_NAME", "POSTGRES_DB", default="investing"),
    )

    return create_engine(connection_url)
