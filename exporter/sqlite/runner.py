import json
import logging
import os
import shutil
import sys
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
from typing import Iterable
from typing import Iterator
from typing import Tuple

import apsw
from django.conf import settings

from exporter.sqlite.plan import Operation

logger = logging.getLogger(__name__)


def normalise_loglevel(loglevel):
    """
    Attempt conversion of `loglevel` from a string integer value (e.g. "20")
    to its loglevel name (e.g. "INFO").

    This function can be used after, for instance, copying log levels from
    environment variables, when the incorrect representation (int as string
    rather than the log level name) may occur.
    """
    try:
        return logging._levelToName.get(int(loglevel))
    except:
        return loglevel


class SQLiteMigrationCurrentDirectory:
    """
    Context manager class that uses the application's current base directory for
    managing SQLite migrations.

    Upon exiting the context manager, SQLite-specific migration files are
    deleted.
    """

    def __enter__(self):
        logger.info(f"Entering context manager {self.__class__.__name__}")
        return settings.BASE_DIR

    def __exit__(self, exc_type, exc_value, traceback):
        logger.info(f"Exiting context manager {self.__class__.__name__}")
        for file in Path(settings.BASE_DIR).rglob(
            "**/migrations/*sqlite_export.py",
        ):
            file.unlink()


class SQLiteMigrationTemporaryDirectory(TemporaryDirectory):
    """
    Context manager class that provides a newly created temporary directory
    (under the OS's temporary directory system) for managing SQLite migrations.

    Upon exiting the context manager, the temporary directory is deleted.
    """

    def __enter__(self):
        logger.info(f"Entering context manager {self.__class__.__name__}")
        tmp_dir = super().__enter__()
        tmp_dir = os.path.join(tmp_dir, "tamato_sqlite_migration")
        shutil.copytree(settings.BASE_DIR, tmp_dir)
        return tmp_dir

    def __exit__(self, exc_type, exc_value, traceback):
        logger.info(f"Exiting context manager {self.__class__.__name__}")
        super().__exit__(exc_type, exc_value, traceback)


class SQLiteMigrator:
    """
    Populates a new and empty SQLite database file with the Tamato database
    schema derived from Tamato's models.

    This is required because SQLite uses different fields to PostgreSQL, missing
    migrations are first generated to bring in the different style of
    validity fields.

    This is done by creating additional, auxiliary migrations that are specific
    to the SQLite and then executing them to populate the database with the
    schema.
    """

    sqlite_file: Path

    def __init__(self, sqlite_file: Path, migrations_in_tmp_dir=False):
        self.sqlite_file = sqlite_file
        self.migration_directory_class = (
            SQLiteMigrationTemporaryDirectory
            if migrations_in_tmp_dir
            else SQLiteMigrationCurrentDirectory
        )

    def migrate(self):
        with self.migration_directory_class() as migration_dir:
            logger.info(f"Running SQLite migrations in {migration_dir}")
            self.manage(migration_dir, "makemigrations", "--name", "sqlite_export")
            self.manage(migration_dir, "migrate")

    def manage(self, exec_dir: str, *manage_args: str):
        """
        Runs a Django management command on the SQLite database.

        This management command will be run such that ``settings.SQLITE`` is
        True, allowing SQLite specific functionality to be switched on and off
        using the value of this setting.

        `exec_dir` sets the directory in which the management command should be
        executed.
        """

        sqlite_env = os.environ.copy()

        # Correct log levels that are incorrectly expressed as string ints.
        if "CELERY_LOG_LEVEL" in sqlite_env:
            sqlite_env["CELERY_LOG_LEVEL"] = normalise_loglevel(
                sqlite_env["CELERY_LOG_LEVEL"],
            )

        sqlite_env["DATABASE_URL"] = f"sqlite:///{str(self.sqlite_file)}"
        # Required to make sure the postgres default isn't set as the DB_URL
        if sqlite_env.get("VCAP_SERVICES"):
            vcap_env = json.loads(sqlite_env["VCAP_SERVICES"])
            vcap_env.pop("postgres", None)
            sqlite_env["VCAP_SERVICES"] = json.dumps(vcap_env)

        run(
            [sys.executable, "manage.py", *manage_args],
            cwd=exec_dir,
            capture_output=False,
            env=sqlite_env,
        )


class Runner:
    """Runs commands on an SQLite database."""

    database: apsw.Connection

    def __init__(self, database: apsw.Connection) -> None:
        self.database = database

    @classmethod
    def make_tamato_database(cls, sqlite_file: Path) -> "Runner":
        """Generate a new and empty SQLite database with the TaMaTo schema
        derived from Tamato's models - by performing 'makemigrations' followed
        by 'migrate' on the Sqlite file located at `sqlite_file`."""

        sqlite_migrator = SQLiteMigrator(
            sqlite_file=sqlite_file,
            migrations_in_tmp_dir=settings.SQLITE_MIGRATIONS_IN_TMP_DIR,
        )
        sqlite_migrator.migrate()

        assert sqlite_file.exists()
        return cls(apsw.Connection(str(sqlite_file)))

    def read_schema(self, type: str) -> Iterator[Tuple[str, str]]:
        """
        Generator yielding a tuple of 'name' and 'sql' column values from
        Sqlite's "schema table", 'sqlite_schema'.

        The `type` param filters rows that have a matching 'type' column value,
        which may be any one of: 'table', 'index', 'view', or 'trigger'.

        See https://www.sqlite.org/schematab.html for further details.
        """
        cursor = self.database.cursor()
        cursor.execute(
            f"""
            SELECT 
                name, sql
            FROM
                sqlite_master
            WHERE 
                sql IS NOT NULL
                AND type = '{type}'
                AND name NOT LIKE 'sqlite_%'
            """,
        )
        yield from cursor.fetchall()

    @property
    def tables(self) -> Iterator[Tuple[str, str]]:
        """Generator yielding a tuple of each Sqlite table object's 'name' and
        the SQL `CREATE_TABLE` statement that can be used to create the
        table."""
        yield from self.read_schema("table")

    @property
    def indexes(self) -> Iterator[Tuple[str, str]]:
        """Generator yielding a tuple of each SQLite table index object name and
        the SQL `CREATE_INDEX` statement that can be used to create it."""
        yield from self.read_schema("index")

    def read_column_order(self, table: str) -> Iterator[str]:
        """
        Returns the name of `table`'s columns in the order they are defined in
        an SQLite database.

        This is necessary because the Django migrations do not generate the
        columns in the order they are defined on the model, and there's no other
        easy way to work out what the correct order is aside from reading them.
        """
        cursor = self.database.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        for column in cursor.fetchall():
            yield column[1]

    def run_operations(self, operations: Iterable[Operation]):
        """Runs each operation in `operations` against `database` member
        attribute (a connection object to an SQLite database file)."""
        cursor = self.database.cursor()
        for operation in operations:
            logger.debug("%s: %s", self.database, operation[0])
            try:
                cursor.executemany(*operation)
            except apsw.SQLError as e:
                logger.error(e)
