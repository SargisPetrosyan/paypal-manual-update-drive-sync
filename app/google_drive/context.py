import logging

from gspread import Worksheet
from app.models.product import PaypalProductData
from app.utils import FileName

logger: logging.Logger = logging.getLogger(name=__name__)


class Context:
    def __init__(
        self,
        product: PaypalProductData,
    ) -> None:
        
        self._parent_folder_id: str | None = None
        self._year_folder_id: str | None = None
        self._day_spreadsheet_id: str | None = None
        self._month_spreadsheet_id: str | None = None
        self.product:PaypalProductData = product
        self.name:FileName = FileName(date=self.product.timestamp)
        self._month_worksheet:Worksheet | None= None
        self._day_worksheet:Worksheet | None= None


    @property
    def parent_folder_id(self) -> str:
        if not self._parent_folder_id:
            raise TypeError("parent_folder_id cant be NONE")
        return self._parent_folder_id

    @property
    def year_folder_id(self) -> str:
        if not self._year_folder_id:
            raise TypeError("year_folder_id cant be NONE")
        return self._year_folder_id

    @property
    def day_spreadsheet_id(self) -> str:
        if not self._day_spreadsheet_id:
            raise TypeError("day_spreadsheet_id cant be NONE")
        return self._day_spreadsheet_id

    @property
    def month_spreadsheet_id(self) -> str:
        if not self._month_spreadsheet_id:
            raise TypeError("month_spreadsheet_id cant be NONE")
        return self._month_spreadsheet_id
    
    @property
    def month_worksheet(self) -> Worksheet:
        if not self._month_worksheet:
            raise TypeError("month worksheet can't be NONE")
        return self._month_worksheet

    @property
    def day_worksheet(self) -> Worksheet:
        if not self._day_worksheet:
            raise TypeError("day worksheet can't be NONE")
        return self._day_worksheet


    @parent_folder_id.setter
    def parent_folder_id(self, id: str) -> None:
        self._parent_folder_id = id

    @year_folder_id.setter
    def year_folder_id(self, id: str) -> None:
        self._year_folder_id = id

    @day_spreadsheet_id.setter
    def day_spreadsheet_id(self, id: str) -> None:
        self._day_spreadsheet_id = id

    @month_spreadsheet_id.setter
    def month_spreadsheet_id(self, id: str) -> None:
        self._month_spreadsheet_id = id

    @day_worksheet.setter
    def day_worksheet(self, worksheet: Worksheet) -> None:
        self._day_worksheet = worksheet

    @month_worksheet.setter
    def month_worksheet(self, worksheet: Worksheet) -> None:
        self._month_worksheet = worksheet
