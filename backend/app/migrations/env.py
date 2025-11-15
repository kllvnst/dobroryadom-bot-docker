from logging.config import fileConfig
import os, sys

from alembic import context
from sqlalchemy import create_engine, pool

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from app.models import Base 

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

dsn_from_ini = config.get_main_option("sqlalchemy.url")
if dsn_from_ini.startswith("postgresql+asyncpg"):
    dsn_from_ini = dsn_from_ini.replace("postgresql+asyncpg", "postgresql+psycopg2")
DATABASE_URL = dsn_from_ini

SKIP_TABLES = {
    "spatial_ref_sys", "geometry_columns", "geography_columns",
    "raster_columns", "raster_overviews"
}
SKIP_SCHEMAS = {"tiger", "topology"}

def include_object(object, name, type_, reflected, compare_to):
    schema = getattr(object, "schema", None)
    if type_ == "table":
        if name in SKIP_TABLES:
            return False
        if schema in SKIP_SCHEMAS:
            return False
    return True

def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = create_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
        future=True,
    )
    with connectable.connect() as connection:
        do_run_migrations(connection)

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
