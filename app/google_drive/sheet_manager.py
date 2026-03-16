from typing import Any
from app.google_drive.client import SpreadSheetClient
from gspread.exceptions import WorksheetNotFound
from gspread.worksheet import Worksheet
from gspread.spreadsheet import Spreadsheet
import logging
from app.constants import (
    WORKSHEET_SAMPLE_COPY_NAME,
    WORKSHEET_SAMPLE_NAME,
)
import logging

logger: logging.Logger = logging.getLogger(name=__name__)


class SpreadSheetFileManager:
    def __init__(self, client: SpreadSheetClient) -> None:
        self.client: SpreadSheetClient = client
        logger.info(msg="'SpreadSheetFileManager' was created ")

    def copy_spreadsheet(
        self, spreadsheet_id: str, title: str, folder_id: str
    ) -> Spreadsheet:
        return self.client.copy(
            field_id=spreadsheet_id, title=title, folder_id=folder_id
        )

    def copy_sheet_to_spreadsheet(
        self, template_id: str, sheet_id: int, destination_spreadsheet_id: str
    ) -> Any:
        self.client.spreadsheets_sheets_copy_to(
            id=template_id,
            sheet_id=sheet_id,
            destination_spreadsheet_id=destination_spreadsheet_id,
        )

    def worksheet_exist(self, spreadsheet_id: str, sheet_name: str) -> bool | Worksheet:
        try:
            worksheet: Worksheet = self.client.get_worksheet(
                spreadsheet_id=spreadsheet_id, worksheet_title=sheet_name
            )
        except WorksheetNotFound:
            return False
        return worksheet

    def get_spreadsheet(self, spreadsheet_id) -> Spreadsheet:
        return self.client.open_by_key(spreadsheet_id=spreadsheet_id)

    def get_worksheet_by_title(
        self, title: str, spreadsheet: Spreadsheet
    ) -> Worksheet | None:
        name: str = str(object=title)
        try:
            worksheet: Worksheet = spreadsheet.worksheet(title=name)
            return worksheet
        except WorksheetNotFound:
            return None

    def delete_worksheet(self, spreadsheet: Spreadsheet, title: str) -> None:
        worksheet: Worksheet = spreadsheet.worksheet(title=f"{title}")
        spreadsheet.del_worksheet(worksheet)

    def create_worksheet(
        self,
        worksheet_name: str,
        templates_spreadsheet_id: str,
        spreadsheet: Spreadsheet,
    ) -> Worksheet:
        # copy sheet sample to spreadsheet
        self.copy_sheet_to_spreadsheet(
            template_id=templates_spreadsheet_id,
            sheet_id=0,
            destination_spreadsheet_id=spreadsheet.id,
        )
        logger.info(f"copying worksheet from template")
        # rename copied worksheet tamale name
        worksheet: Worksheet = spreadsheet.worksheet(title=WORKSHEET_SAMPLE_COPY_NAME)
        logger.info(
            f"renaming worksheet form '{WORKSHEET_SAMPLE_COPY_NAME} to {worksheet_name}'"
        )

        worksheet.update_title(title=worksheet_name)

        return worksheet

    def create_spreadsheet(
        self,
        file_name: str,
        spreadsheet_template_id: str,
        worksheet_name: str,
        year_folder_id: str,
    ) -> Spreadsheet:
        spreadsheet_copy: Spreadsheet = self.copy_spreadsheet(
            spreadsheet_id=spreadsheet_template_id,
            title=file_name,
            folder_id=year_folder_id,
        )
        logger.info(msg=f"file 'file_name: {file_name}' was not found")
        logger.info(msg=f"creating new file 'file_name: {file_name}'")
        spreadsheet_id: str = spreadsheet_copy.id

        spreadsheet: Spreadsheet = self.get_spreadsheet(spreadsheet_id=spreadsheet_id)

        logger.info(
            msg=f"rename template names from 'WORKSHEET_SAMPLE_NAME to {worksheet_name}'"
        )
        # rename copied worksheet tamale name
        worksheet: Worksheet = spreadsheet.worksheet(title=WORKSHEET_SAMPLE_NAME)

        worksheet.update_title(title=worksheet_name)
        logger.info(
            msg=f"renaming template names from 'WORKSHEET_SAMPLE_NAME to {worksheet_name}' was successfully done!!!"
        )
        return spreadsheet
