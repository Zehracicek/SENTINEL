from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

import sys
import os

BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BACKEND_DIR)

from dotenv import load_dotenv

# models -> database zinciri DATABASE_URL bekliyor; import'tan önce yüklenmeli.
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

from models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _sync_database_url() -> str:
    """Alembic senkron sürücü ister; asyncpg dizesi verilmişse çevir."""
    url = (os.getenv("DATABASE_URL_SYNC") or "").strip()
    if not url:
        url = (os.getenv("DATABASE_URL") or "").strip().replace(
            "postgresql+asyncpg://", "postgresql://"
        )
    if not url:
        raise RuntimeError(
            "DATABASE_URL_SYNC veya DATABASE_URL tanımlı değil; "
            "backend/.env dosyasını .env.example'dan türetin."
        )
    return url


config.set_main_option("sqlalchemy.url", _sync_database_url())

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
