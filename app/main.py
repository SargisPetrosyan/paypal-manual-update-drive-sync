from app.core.config import Database
from app.google_drive.drive_sync_worker import HourlyWorkflowRunner


if __name__ == '__main__':
    print('DOCKER IS RUNNING')
    # workflow_runner = HourlyWorkflowRunner(database=Database())
    # workflow_runner.run()