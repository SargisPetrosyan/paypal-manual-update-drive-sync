from typing import List
from fastapi.responses import JSONResponse
from gspread import Cell, ValueRange, Worksheet

from app.constants import (
    DAY_PRODUCT_AND_VARIANT_ID_COL,
    DAY_PRODUCT_STOCK_IN_COL,
    DAY_PRODUCT_STOCK_OUT_COL,
    MONTH_PRODUCT_AND_VARIANT_ID_COL,
    MONTH_PRODUCT_STOCK_OUT_NAME_ROW_OFFSET,
    MONTH_WORKSHEET_FIRST_CELL,
    MONTH_PRODUCT_DATA_CELL_RANGE,
)
from app.google_drive.context import Context
import logging

from app.models.google_drive import RowEditResponse
from app.utils import extract_row_from_notation

logger: logging.Logger = logging.getLogger(name=__name__)


class DayWorksheetProductReader:
    def __init__(
        self,
        worksheet: Worksheet,
    ) -> None:
        self.worksheet: Worksheet = worksheet
        self.stock_in_col: int = DAY_PRODUCT_STOCK_IN_COL
        self.stock_out_index: int = DAY_PRODUCT_STOCK_OUT_COL

    def get_product_row_by_name(self, product_variant_id: str) -> int:
        product: Cell | None = self.worksheet.find(
            query=product_variant_id, in_column=DAY_PRODUCT_AND_VARIANT_ID_COL
        )

        if not product:
            raise ValueError("Product was deleted")
        return product.row

    def get_product_stock_in(self, product_row: int) -> int:
        stock_in: Cell = self.worksheet.cell(row=product_row, col=self.stock_in_col)

        if not stock_in.value:
            raise TypeError("day product stock in value not exist")
        return int(stock_in.value)

    def get_product_stock_out(self, product_row: int) -> int:
        stock_out: Cell = self.worksheet.cell(row=product_row, col=self.stock_out_index)

        if not stock_out.value:
            raise TypeError("day product stock out value not exist")
        return int(stock_out.value)

    def product_exist(self, product_variant_id: str) -> bool:
        product: Cell | None = self.worksheet.find(
            query=product_variant_id, in_column=DAY_PRODUCT_AND_VARIANT_ID_COL
        )

        if not product:
            return False
        return True


class DayWorksheetProductWriter:
    def __init__(self, worksheet: Worksheet) -> None:
        self.worksheet: Worksheet = worksheet

    def add_new_product(self, context: Context) -> None:
        new_row: list[str | int | None] = [
            context.product.name,
            context.product.category_name,
            context.product.variant_name,
            context.product.cost_price,
            context.product.selling_price,
        ]
        response:JSONResponse = self.worksheet.append_row(values=new_row) #type:ignore
        response_validated: RowEditResponse = RowEditResponse.model_validate(response)
        row_number:int = extract_row_from_notation(response=response_validated)
        self.worksheet.update_cell(
            row=row_number, 
            col=DAY_PRODUCT_AND_VARIANT_ID_COL,
            value=context.product.product_variant_uuid)
        
    def update_stock_in(
        self,
        old_stock_in: int,
        amount: int,
        row: int,
    ) -> None:
        increment_values: int = old_stock_in + amount
        logger.info(f"update day report stock_out by value'{increment_values}'")
        self.worksheet.update_cell(
            row=row, value=increment_values, col=DAY_PRODUCT_STOCK_IN_COL
        )

    def update_stock_out(self, old_stock_out: int, amount: int, row: int) -> None:
        old_value: int = old_stock_out
        increment_values: int = old_value + amount
        logger.info(f"update day report stock_out by value'{increment_values}'")
        self.worksheet.update_cell(
            row=row,
            col=DAY_PRODUCT_STOCK_OUT_COL,
            value=-abs(increment_values),
        )

class MonthWorksheetProductReader:
    def __init__(
        self,
        worksheet: Worksheet,
    ) -> None:
        self.worksheet: Worksheet = worksheet

    def get_product_row_by_name(
        self,
        product_variant_id: str,
    ) -> int:
        product: Cell | None = self.worksheet.find(
            query=product_variant_id, in_column=MONTH_PRODUCT_AND_VARIANT_ID_COL
        )

        if not product:
            raise TypeError("Month product value not exist ")
        return product.row

    def get_product_stock_in(self, product_row: int, stock_in_col: int) -> int:
        product: Cell = self.worksheet.cell(row=product_row, col=stock_in_col)

        if not product.value:
            raise TypeError("Month product stock in value not exist ")
        return int(product.value)

    def get_product_stock_out(self, product_row: int, stock_out_col: int) -> int:
        stock_out: Cell = self.worksheet.cell(row=product_row, col=stock_out_col)

        if not stock_out.value:
            raise TypeError("Month product stock out value not exist ")
        return int(stock_out.value)

    def product_exist(self, product_variant_uuid: str) -> bool:
        product: Cell | None = self.worksheet.find(
            query=product_variant_uuid, in_column=MONTH_PRODUCT_AND_VARIANT_ID_COL
        )

        if not product:
            return False
        return True
    
    def get_product_stock_out_row(self,product_variant_id:str) -> int:
        product: Cell | None = self.worksheet.find(
            query=product_variant_id, in_column=MONTH_PRODUCT_AND_VARIANT_ID_COL
            )

        if not product:
            raise TypeError("Month product value not exist ")
        return product.row + MONTH_PRODUCT_STOCK_OUT_NAME_ROW_OFFSET #stock out row in next ro check_spreadsheet example



class MonthWorksheetProductWriter:
    def __init__(self, worksheet: Worksheet) -> None:
        self.worksheet: Worksheet = worksheet

    def add_new_product(self, context: Context) -> None:
        first_element: ValueRange | List[List[str]] = self.worksheet.get(
            range_name=MONTH_WORKSHEET_FIRST_CELL
        )
        
        if not first_element[0]:
            edit_response = self.worksheet.append_row(
                values=[
                    context.product.name,
                    context.product.category_name,
                    context.product.variant_name,
                    context.product.cost_price,
                    context.product.selling_price,
                ],
                table_range=MONTH_PRODUCT_DATA_CELL_RANGE,
                )
        else:
            edit_response = self.worksheet.append_row(
                values=[
                    context.product.name,
                    context.product.category_name,
                    context.product.variant_name,
                    context.product.cost_price,
                    context.product.selling_price,
                ]
            )

        response_validated: RowEditResponse = RowEditResponse.model_validate(edit_response)
        row_number:int = extract_row_from_notation(response=response_validated)
        self.worksheet.update_cell(
            row=row_number, 
            col=MONTH_PRODUCT_AND_VARIANT_ID_COL,
            value=context.product.product_variant_uuid)
        
        self._col = int(context.name.month_stock_in_and_out_col_index)

    def update_stock_in(
        self,
        old_stock_in: int,
        amount: int,
        row: int,
        col: int,
    ) -> None:
        increment_values: int = old_stock_in + amount
        logger.info(
            msg=f"update day report stock_out by value: '{increment_values}' row:'{row}', col:'{col}'"
        )

        self.worksheet.update_cell(
            row=row,
            value=increment_values,
            col=col,  
        )

    def update_stock_out(
        self, old_stock_out: int, amount: int, row: int, col: int
    ) -> None:
        old_value: int = old_stock_out
        increment_values: int = old_value + amount
        logger.info(
            msg=f"update day report stock_out by value'{increment_values}' row:'{row}', col:'{col}'"
        )

        self.worksheet.update_cell(
            row=row,
            col=col,
            value=-abs(increment_values),
        )
