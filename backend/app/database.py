
import logging
import os
from pathlib import Path

import pymysql
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)

db = SQLAlchemy()


def verify_and_configure_database(app):
    """
    Verify MySQL connectivity before SQLAlchemy initialization.

    Uses SSL when MYSQL_SSL_CA is configured.
    SQLite fallback is allowed only when explicitly enabled.
    """
    db_uri = str(app.config.get("SQLALCHEMY_DATABASE_URI", ""))

    if "mysql" not in db_uri.lower():
        return

    user = app.config.get("MYSQL_USER", "root")
    password = app.config.get("MYSQL_PASSWORD", "")
    host = app.config.get("MYSQL_HOST", "localhost")
    port = int(app.config.get("MYSQL_PORT", 3306))
    dbname = app.config.get("MYSQL_DB", "marketplace_reviewer")
    ssl_ca = app.config.get("MYSQL_SSL_CA", "")

    try:
        logger.info("Testing MySQL connection to %s:%s...", host, port)

        connection_options = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "connect_timeout": 20,
            "charset": "utf8mb4",
        }

        if ssl_ca:
            if not Path(ssl_ca).is_file():
                raise FileNotFoundError(
                    f"MySQL CA certificate not found: {ssl_ca}"
                )

            connection_options["ssl"] = {"ca": ssl_ca}
            connection_options["database"] = dbname
        else:
            connection_options["database"] = dbname

        conn = pymysql.connect(**connection_options)

        with conn.cursor() as cursor:
            cursor.execute("SELECT DATABASE()")
            logger.info(
                "MySQL connection verified. Database: %s",
                cursor.fetchone()[0]
            )

        conn.close()

    except Exception as error:
        logger.exception("MySQL connection failed: %s", error)

        allow_fallback = (
            str(os.getenv("ALLOW_SQLITE_FALLBACK", "true")).lower()
            == "true"
        )

        if not allow_fallback:
            raise RuntimeError(
                "MySQL connection failed and SQLite fallback is disabled."
            ) from error

        logger.warning("Switching to local SQLite database.")

        db_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "marketplace_reviewer.db"
        )

        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"sqlite:///{db_path}"
        )
        app.config.pop("SQLALCHEMY_ENGINE_OPTIONS", None)


def init_db(app):
    """
    Creates application tables and seeds initial data.
    """
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables initialized successfully.")

            from app.utils.seed_data import seed_initial_data
            seed_initial_data()

            logger.info("Initial data seeding completed.")

        except Exception:
            logger.exception("Error creating tables or seeding data.")
            raise
