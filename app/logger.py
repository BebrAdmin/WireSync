import logging
import logging.handlers
import os
import tarfile
import zipfile
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from app.config import LoggingConfig

LOG_DIR = "app/logs"
LOG_FILENAME = "app.log"
LOG_WHEN = "midnight"
LOG_INTERVAL = 1
LOG_ENCODING = "utf-8"

logger = logging.getLogger(__name__)

class ArchiveRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(
        self,
        filename,
        when="h",
        interval=1,
        backupCount=0,
        encoding=None,
        delay=False,
        utc=False,
        atTime=None,
        errors=None,
        archive_format="zip",  
    ):
        super().__init__(
            filename, when, interval, backupCount, encoding, delay, utc, atTime, errors
        )
        if archive_format not in {"zip", "gz"}:
            raise ValueError("archive_format must be either 'zip' or 'gz'")

        self.archive_format = archive_format
        logger.debug(f"Initialized ArchiveRotatingFileHandler with format: {self.archive_format}")

    def doRollover(self) -> None:
        super().doRollover()

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dir_name = os.path.dirname(self.baseFilename)
        archive_name = os.path.join(dir_name, f"{timestamp}.{self.archive_format}")

        self._archive_log_file(archive_name)
        self._remove_old_logs()

    def _archive_log_file(self, archive_name: str) -> None:
        logger.info(f"Archiving {self.baseFilename} to {archive_name}")
        if os.path.exists(self.baseFilename):
            if self.archive_format == "zip":
                self._archive_to_zip(archive_name)
            elif self.archive_format == "gz":
                self._archive_to_gz(archive_name)
        else:
            logger.warning(f"Log file {self.baseFilename} does not exist, skipping archive.")

    def _archive_to_zip(self, archive_name: str) -> None:
        log = self.getFilesToDelete()[0]
        new_log_name = self._get_log_filename(archive_name)
        with zipfile.ZipFile(archive_name, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.write(filename=log, arcname=new_log_name)

    def _archive_to_gz(self, archive_name: str) -> None:
        log = self.getFilesToDelete()[0]
        new_log_name = self._get_log_filename(archive_name)
        with tarfile.open(archive_name, "w:gz") as archive:
            archive.add(name=log, arcname=new_log_name)

    def _get_log_filename(self, archive_name: str) -> str:
        return os.path.splitext(os.path.basename(archive_name))[0] + ".log"

    def _remove_old_logs(self) -> None:
        files_to_delete = self.getFilesToDelete()
        logger.debug(f"Removing old log files: {files_to_delete}")
        for file in files_to_delete:
            if os.path.exists(file):
                try:
                    os.remove(file)
                    logger.debug(f"Successfully deleted old log file: {file}")
                except Exception as exception:
                    logger.error(f"Error deleting {file}: {exception}")

def setup_logging(config: LoggingConfig) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, LOG_FILENAME)

    logging.basicConfig(
        level=getattr(logging, config.LEVEL.upper(), logging.INFO),
        format=config.FORMAT,
        handlers=[
            ArchiveRotatingFileHandler(
                filename=log_file,
                when=LOG_WHEN,
                interval=LOG_INTERVAL,
                encoding=LOG_ENCODING,
                archive_format=config.ARCHIVE_FORMAT,
            ),
            logging.StreamHandler(),
        ],
    )

    logger.debug(
        f"Logging configuration: level={config.LEVEL}, "
        f"format={config.FORMAT}, archive_format={config.ARCHIVE_FORMAT}"
    )
    
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("aiogram.event").setLevel(logging.CRITICAL)
    logging.getLogger("aiosqlite").setLevel(logging.INFO)
    logging.getLogger("httpcore").setLevel(logging.INFO)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)