from app.core.config import Database
from app.core.logging import setup_logger
from app.google_drive.drive_sync_worker import HourlyWorkflowRunner
import datetime
import logging 

setup_logger()

logger: logging.Logger = logging.getLogger(name=__name__)

if __name__ == '__main__':
    logger.info("run worker")
    utc_time: datetime.datetime = datetime.datetime.now(tz=datetime.timezone.utc)
    workflow_runner = HourlyWorkflowRunner(database=Database(time=utc_time),time=utc_time)
    workflow_runner.run()