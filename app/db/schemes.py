from datetime import datetime
from typing import Sequence
from sqlalchemy import Engine
from sqlmodel import  Session, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar
from app.db.models import InventoryBalanceUpdateModel
import logging

logger: logging.Logger = logging.getLogger(name=__name__)

class  InventoryUpdateRepository():
    def __init__(self,engine) -> None:
        self.engine: Engine  = engine
        
    def fetch_data_by_date_interval(self,start_date:datetime, end_date:datetime) -> Sequence[InventoryBalanceUpdateModel]:
        logger.info("get update data from database ")
        with Session(bind=self.engine) as session:
            statement: SelectOfScalar[InventoryBalanceUpdateModel] = select(InventoryBalanceUpdateModel) \
                .where(InventoryBalanceUpdateModel.timestamp > start_date,
                        InventoryBalanceUpdateModel.timestamp < end_date)
            
            results: Sequence[InventoryBalanceUpdateModel] = session.exec(statement=statement).all()
            return results