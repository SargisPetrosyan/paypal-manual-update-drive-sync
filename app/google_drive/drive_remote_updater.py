from app.google_drive.context import Context
from app.google_drive.services import (
        DayProductExistenceEnsurer,
        DayWorksheetValueUpdater,
        MonthProductExistenceEnsurer,
        MonthWorksheetValueUpdater)


class DriveSpreadsheetUpdater:
    def __init__(self,context:Context) -> None:
        self.context: Context = context
    
    def process_data_to_worksheet(self) -> None:
        # step 4.1 ensure day worksheet product:
        day_product = DayProductExistenceEnsurer(day_worksheet=self.context.day_worksheet, context=self.context)
        day_product.ensure_day_product(product=self.context.product)

        # step 4.2 ensure day worksheet product:
        month_product = MonthProductExistenceEnsurer(month_worksheet=self.context.month_worksheet,context=self.context)
        month_product.ensure_month_product(product=self.context.product)

        # step 5.1 update day remote worksheet
        DayWorksheetValueUpdater.update_day_worksheet(
            day_worksheet_reader=day_product.day_worksheet_reader,
            day_worksheet_writer=day_product.day_worksheet_writer,
            context=self.context
        )

        # step 5.2 update month remote worksheet
        MonthWorksheetValueUpdater.update_month_worksheet(
            month_worksheet_reader=month_product.month_worksheet_reader,
            month_worksheet_writer=month_product.month_worksheet_writer,
            context=self.context,
        )
