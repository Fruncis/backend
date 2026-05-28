"""
Alembic environment configuration.

This module is executed by Alembic when running any migration command
(``alembic upgrade head``, ``alembic revision --autogenerate``, etc.).

**Critical**: The first thing we do is add the project root (one level
above this ``migrations/`` directory) to ``sys.path`` so that all
internal imports (``core.config``, ``adapters.outbound.postgres``, …)
resolve correctly when Alembic is invoked from the command line.
"""

from __future__ import annotations

# ── Path fix — MUST come before any app imports ──────────────────────
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ── App imports ──────────────────────────────────────────────────────
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from adapters.outbound.postgres.database import Base
from adapters.outbound.postgres.candidate_orm import CandidateORM  # noqa: F401  — register model
from core.config.settings import get_settings

# ── Alembic Config object ───────────────────────────────────────────
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the SQLAlchemy URL programmatically from application settings.
config.set_main_option("sqlalchemy.url", get_settings().database.url)

# ``target_metadata`` tells Alembic which tables to track for
# ``--autogenerate``.  By importing CandidateORM above we ensure
# that its table is registered on ``Base.metadata``.
target_metadata = Base.metadata


# ── Offline migrations ──────────────────────────────────────────────


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL and not an ``Engine``.
    Calls to ``context.execute()`` emit the given SQL string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ── Online migrations ───────────────────────────────────────────────


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an ``Engine`` and associates a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# ── Dispatch ─────────────────────────────────────────────────────────

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
