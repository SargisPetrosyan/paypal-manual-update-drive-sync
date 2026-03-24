import logging
import time

from sqlalchemy import Engine
from app.constants import  SHOPS
from app.core.config import Database
from app.db.schemes import InventoryUpdateRepository
from app.google_drive.aoth import DriveCredentialsGetter
from app.google_drive.client import GoogleDriveClient, SpreadSheetClient
from app.google_drive.context import Context
from app.google_drive.drive_remote_updater import DriveSpreadsheetUpdater
from app.google_drive.drive_manager import GoogleDriveFileManager
from app.google_drive.services import DriveFileStructureEnsurer
from app.google_drive.sheet_manager import SpreadSheetFileManager
from app.models.product import PaypalProductData
from app.zettle.services import InventoryManualDataCollector
import datetime


logger: logging.Logger = logging.getLogger(name=__name__)

class HourlyWorkflowRunner:
    def __init__(self,database:Database) -> None:
        self.engine: Engine = database.engine
        self.shops: tuple[str, str, str]= SHOPS
        self.google_creds = DriveCredentialsGetter()
        self.google_drive_client = GoogleDriveClient(creds=self.google_creds.creds)
        self.spreadsheet_file_client = SpreadSheetClient(creds=self.google_creds.creds)
        self.google_drive_file_manager = GoogleDriveFileManager(client=self.google_drive_client)
        self.spreadsheet_manager = SpreadSheetFileManager(client=self.spreadsheet_file_client)

    def run(self):
        utc_time =datetime.datetime.now(tz=datetime.timezone.utc)
        repo_updater: InventoryUpdateRepository = InventoryUpdateRepository(engine=self.engine)
        
        for name in self.shops:
            logger.info(f"check manual changes for '{name}'")

            manual_collector = InventoryManualDataCollector(
                utc_time=utc_time,
                repo_updater=repo_updater,
                shop_name=name,
)

            # step 1 filter changed product data
            list_of_manual_products: list[PaypalProductData] | None = manual_collector.get_manual_changed_products()
            if not list_of_manual_products:
                logger.info(f"there is no manual changes for  this date interval ")
                continue
            

            for product in list_of_manual_products:
                time.sleep(8) #delay requests for google drive limitations
                context =Context(product=product)
                # step 2 check if google drive had proper file structure
                drive_file_ensurer = DriveFileStructureEnsurer(
                    google_drive_file_manager=self.google_drive_file_manager,
                    spreadsheet_file_manager=self.spreadsheet_manager)
                
                drive_file_ensurer.ensure_drive_file_structure(context=context)

                context.product = product
                # step 3 process manual changes to worksheet
                drive_file_updater = DriveSpreadsheetUpdater(context=context)
                drive_file_updater.process_data_to_worksheet()
                


        