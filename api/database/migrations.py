from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Engine
import os
import logging
from pathlib import Path
from typing import Optional, List

from api.database.database import engine, Base
from config import settings

logger = logging.getLogger(__name__)

class DatabaseMigrations:
    """
    Database migration management using Alembic
    """
    
    def __init__(self, engine: Engine = engine):
        self.engine = engine
        self.alembic_cfg = self._get_alembic_config()
    
    def _get_alembic_config(self) -> Config:
        """
        Get Alembic configuration
        """
        # Get the directory containing this file
        current_dir = Path(__file__).parent
        alembic_dir = current_dir / "alembic"
        
        # Create alembic directory if it doesn't exist
        alembic_dir.mkdir(exist_ok=True)
        
        # Create alembic.ini if it doesn't exist
        alembic_ini = current_dir / "alembic.ini"
        if not alembic_ini.exists():
            self._create_alembic_ini(alembic_ini, alembic_dir)
        
        # Configure Alembic
        alembic_cfg = Config(str(alembic_ini))
        alembic_cfg.set_main_option("script_location", str(alembic_dir))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.get_database_url())
        
        return alembic_cfg
    
    def _create_alembic_ini(self, ini_path: Path, script_location: Path):
        """
        Create alembic.ini configuration file
        """
        ini_content = f"""# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = {script_location}

# template used to generate migration file names; The default value is %%(rev)s_%%(slug)s
# Uncomment the line below if you want the files to be prepended with date and time
# file_template = %%Y%%m%%d_%%H%%M_%%%(rev)s_%%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# as well as the filename.
# If specified, requires the python-dateutil library that can be
# installed by adding `alembic[tz]` to the pip requirements
# string value is passed to dateutil.tz.gettz()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version number format
# version_num_format = %%d

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses
# os.pathsep. If this key is omitted entirely, it falls back to the legacy
# behavior of splitting on spaces and/or commas.
# Valid values for version_path_separator are:
#
# version_path_separator = :
# version_path_separator = ;
# version_path_separator = space
version_path_separator = os

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = {settings.get_database_url()}


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %%(levelname)-5.5s [%%(name)s] %%(message)s
datefmt = %%H:%%M:%%S
"""
        
        with open(ini_path, 'w') as f:
            f.write(ini_content)
        
        logger.info(f"Created alembic.ini at {ini_path}")
    
    def init_alembic(self) -> bool:
        """
        Initialize Alembic for the project
        """
        try:
            script_location = Path(self.alembic_cfg.get_main_option("script_location"))
            
            if not (script_location / "env.py").exists():
                command.init(self.alembic_cfg, str(script_location))
                self._customize_env_py(script_location / "env.py")
                logger.info("Alembic initialized successfully")
            else:
                logger.info("Alembic already initialized")
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Alembic: {e}")
            return False
    
    def _customize_env_py(self, env_py_path: Path):
        """
        Customize the env.py file for our project
        """
        env_content = '''from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Import your models here
from api.database.models import Base
from api.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = settings.get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.get_database_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
        
        with open(env_py_path, 'w') as f:
            f.write(env_content)
        
        logger.info(f"Customized env.py at {env_py_path}")
    
    def create_migration(self, message: str, autogenerate: bool = True) -> Optional[str]:
        """
        Create a new migration
        """
        try:
            if autogenerate:
                revision = command.revision(self.alembic_cfg, message=message, autogenerate=True)
            else:
                revision = command.revision(self.alembic_cfg, message=message)
            
            logger.info(f"Created migration: {message}")
            return revision.revision
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            return None
    
    def upgrade(self, revision: str = "head") -> bool:
        """
        Upgrade database to a specific revision
        """
        try:
            command.upgrade(self.alembic_cfg, revision)
            logger.info(f"Upgraded database to revision: {revision}")
            return True
        except Exception as e:
            logger.error(f"Failed to upgrade database: {e}")
            return False
    
    def downgrade(self, revision: str) -> bool:
        """
        Downgrade database to a specific revision
        """
        try:
            command.downgrade(self.alembic_cfg, revision)
            logger.info(f"Downgraded database to revision: {revision}")
            return True
        except Exception as e:
            logger.error(f"Failed to downgrade database: {e}")
            return False
    
    def get_current_revision(self) -> Optional[str]:
        """
        Get current database revision
        """
        try:
            with self.engine.connect() as connection:
                context = MigrationContext.configure(connection)
                return context.get_current_revision()
        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return None
    
    def get_history(self) -> List[dict]:
        """
        Get migration history
        """
        try:
            script = ScriptDirectory.from_config(self.alembic_cfg)
            history = []
            
            for revision in script.walk_revisions():
                history.append({
                    "revision": revision.revision,
                    "down_revision": revision.down_revision,
                    "branch_labels": revision.branch_labels,
                    "depends_on": revision.depends_on,
                    "doc": revision.doc,
                    "create_date": revision.create_date,
                })
            
            return history
        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return []
    
    def check_migration_status(self) -> dict:
        """
        Check migration status
        """
        try:
            current = self.get_current_revision()
            script = ScriptDirectory.from_config(self.alembic_cfg)
            head = script.get_current_head()
            
            return {
                "current_revision": current,
                "head_revision": head,
                "is_up_to_date": current == head,
                "pending_migrations": current != head
            }
        except Exception as e:
            logger.error(f"Failed to check migration status: {e}")
            return {"error": str(e)}
    
    def stamp(self, revision: str = "head") -> bool:
        """
        Stamp the database with a specific revision without running migrations
        """
        try:
            command.stamp(self.alembic_cfg, revision)
            logger.info(f"Stamped database with revision: {revision}")
            return True
        except Exception as e:
            logger.error(f"Failed to stamp database: {e}")
            return False

# Global migration manager instance
migration_manager = DatabaseMigrations()

# Convenience functions
def init_migrations() -> bool:
    """Initialize migrations for the project"""
    return migration_manager.init_alembic()

def create_migration(message: str, autogenerate: bool = True) -> Optional[str]:
    """Create a new migration"""
    return migration_manager.create_migration(message, autogenerate)

def upgrade_database(revision: str = "head") -> bool:
    """Upgrade database to latest or specific revision"""
    return migration_manager.upgrade(revision)

def downgrade_database(revision: str) -> bool:
    """Downgrade database to specific revision"""
    return migration_manager.downgrade(revision)

def get_migration_status() -> dict:
    """Get current migration status"""
    return migration_manager.check_migration_status()

def reset_migrations() -> bool:
    """Reset migrations by stamping with head"""
    return migration_manager.stamp("head")