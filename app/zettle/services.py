
import os
from typing import Any, Sequence
from uuid import UUID
from pydantic import ValidationError
from app.db.schemes import InventoryUpdateRepository
from app.models.inventory import InventoryUpdateData
from app.models.product import PaypalProductData,ProductData,ListOfPurchases
from app.zettle.data_fetchers import ProductDataFetcher, PurchasesFetcher
from datetime import datetime, timedelta, timezone
from app.db.models import InventoryBalanceUpdateModel
from app.utils import PaypalTokenData, PreviewsHourWindow, any_to_sweden_time

import logging


logger: logging.Logger = logging.getLogger(name=__name__)

class InventoryUpdatesDataJoiner:
    def __init__(
            self,
            inventory_changes:Sequence[InventoryBalanceUpdateModel]) -> None:
        
        self.inventory_changes:Sequence[InventoryBalanceUpdateModel] = inventory_changes
        self._inventory_update_joined:dict[tuple[UUID,UUID], InventoryUpdateData] = {}
    
    def join_inventory_update_data(self) -> dict[tuple[UUID,UUID], InventoryUpdateData]:
        for update in self.inventory_changes:
            key:tuple[UUID,UUID] = (update.product_id, update.variant_id)
            change:int = update.after - update.before
            if key in self._inventory_update_joined:
                self._inventory_update_joined[key].updated_value += change
            else:
                self._inventory_update_joined[key] = InventoryUpdateData(
                    stock=update.before,
                    updated_value=update.after,
                    timestamp=update.timestamp,
                )
        logger.info(msg=f"Inventory data was joined products count: '{len(self._inventory_update_joined)}")
        return self._inventory_update_joined
    
class PurchaseDataJoiner:
    def __init__(self):
        self._purchases_joined:dict[tuple[UUID,UUID], int ] = {}

    
    def join_purchase_update_data(self,purchases:ListOfPurchases) -> dict[tuple[UUID,UUID], int]:
        # fetch stored inventory updates

        validated_purchases:ListOfPurchases = ListOfPurchases.model_validate(obj=purchases)

        for purchases_iter in validated_purchases.purchases:
            for product_iter in purchases_iter.products:
                key:tuple[UUID,UUID] = (product_iter.productUuid, product_iter.variantUuid)
                quantity:int = product_iter.quantity
                if key not in self._purchases_joined:
                    self._purchases_joined[key] = quantity
                else:
                    self._purchases_joined[key] += quantity
        logger.info("purchases data was joined")
        return self._purchases_joined
                    

class InventoryManualChangesChecker:
    def __init__(
            self,
            purchases_merged:dict[tuple[UUID,UUID],int],
            inventory_update_merged:dict[tuple[UUID,UUID],InventoryUpdateData],
            ) -> None:
        
        self.marge_inventory_update: dict[tuple[UUID,UUID],InventoryUpdateData] = inventory_update_merged
        self.marge_purchases_update: dict[tuple[UUID,UUID],int] = purchases_merged

    def get_manual_changes(self) -> dict[tuple[UUID, UUID], InventoryUpdateData]:
        logger.info("get manual changes comparing purchases and db result")
        for purchase, value in self.marge_purchases_update.items():
            try:
                self.marge_inventory_update[purchase].updated_value = self.marge_inventory_update[purchase].updated_value + value
                if self.marge_inventory_update[purchase].stock == self.marge_inventory_update[purchase].updated_value:
                    del self.marge_inventory_update[purchase]
            except KeyError:
                logger.critical(msg="database storing logic not working properly, purchases and db product changes not matches")
                raise ValueError("database has missing value")
        logger.info(f"manual changes count:{len(self.marge_inventory_update)}")
        return self.marge_inventory_update
            

class ManualProductData:
    def __init__(
            self,
            manual_changes: dict[tuple[UUID,UUID],InventoryUpdateData],
            organization_id:str,
            product_data_fetcher:ProductDataFetcher) -> None:
        
        self.manual_changes: dict[tuple[UUID,UUID],InventoryUpdateData] = manual_changes
        self.organization_id: str = organization_id
        self.data_fetcher:ProductDataFetcher = product_data_fetcher
        self.list_of_products:list[PaypalProductData] = []
    
    def get_manual_changes_product_data(self) -> list[PaypalProductData]:
        logger.info("fill product missing data for drive storing")
        for key,value in self.manual_changes.items():
            product_data:dict = self.data_fetcher.get_product_data(
                product_uuid=str(object=key[0]), 
                organization_id=self.organization_id)
        
            validated_product_data:ProductData = ProductData.model_validate(obj=product_data)
            
            for variant in validated_product_data.variants:
                if variant and variant.uuid == key[1]:
                    product:PaypalProductData = PaypalProductData(
                        name=(
                            validated_product_data.name
                            if validated_product_data.name is not None
                            else "None"
                        ),
                        variant_name=(
                            str(object=variant.name)
                            if variant is not None
                            else "None"
                        ),
                        product_variant_uuid=f"{str(key[0])},{str(key[1])}",
                        category_name=(
                            validated_product_data.category.name
                            if validated_product_data.category is not None
                            else "None"
                        ),
                        selling_price=(
                            variant.price.amount // 100
                            if variant and variant.price is not None
                            else "None"
                        ),
                        cost_price=(
                            variant.costPrice.amount // 100
                            if variant and variant.costPrice is not None 
                            else "None"
                        ),
                        after=value.updated_value,
                        before=value.stock,
                        timestamp= value.timestamp,
                        organization_id=self.organization_id
                    )
                    self.list_of_products.append(product)
                    
        return self.list_of_products

class InventoryManualDataCollector:
    def __init__(
            self,repo_updater:InventoryUpdateRepository, 
            shop_name:str, 
            utc_time:datetime,) -> None:
        
        self.shop_name: str = shop_name
        self.paypal_token = PaypalTokenData(shop_name=self.shop_name)
        self.purchase_fetcher:PurchasesFetcher = PurchasesFetcher(token_data=self.paypal_token)
        self.repo_updater:InventoryUpdateRepository = repo_updater
        self.time_interval  = PreviewsHourWindow(date=utc_time)
        self._purchases_joined_joined:dict[frozenset[UUID], int] = {}
        # self.start_date: datetime = datetime.strptime("2026-03-21 11:14:02+0000","%Y-%m-%d %H:%M:%S%z").astimezone(timezone.utc)
        # self.end_date: datetime = datetime.strptime("2026-03-21 14:07:40+0000","%Y-%m-%d %H:%M:%S%z").astimezone(timezone.utc)
        self.start_date: datetime = self.time_interval.start_date
        self.end_date:datetime =  self.time_interval.end_date

    def get_manual_changed_products(self) -> list[PaypalProductData] | None:
                
        organization_id: str = str(object=UUID(hex=os.environ[f"{self.shop_name.upper()}_ORGANIZATION_UUID"]))

        #fetch inventory data from database
        inventory_updates: Sequence[InventoryBalanceUpdateModel] = self.repo_updater.fetch_data_by_date_interval(
            start_date=any_to_sweden_time(self.start_date),
            end_date=any_to_sweden_time(self.end_date),
            organization_id=organization_id)
        
        if not inventory_updates:
            logger.info(f"other was not any changes for time interval start:'{any_to_sweden_time(self.start_date)}', end:'{any_to_sweden_time(self.end_date)}'")
            return None
        # inventory update data joining
        inventory_data_joiner = InventoryUpdatesDataJoiner(inventory_changes=inventory_updates)
        
        inventory_data_joined: dict[tuple[UUID,UUID], InventoryUpdateData] = inventory_data_joiner.join_inventory_update_data()

        # purchases data joining
        purchases_joiner = PurchaseDataJoiner()
        
        # get purchases by time interval
        purchases: dict[Any,Any] = self.purchase_fetcher.get_purchases(
            start_date=self.start_date,
            end_date=self.end_date,
        )

        try:
            validate_purchases:ListOfPurchases = ListOfPurchases.model_validate(obj=purchases)
        except ValidationError:
            logger.critical("purchases can't pass validation") 
            raise
        
        purchases_data_merged: dict[tuple[UUID,UUID], int] = purchases_joiner.join_purchase_update_data(purchases=validate_purchases)

        # minus purchases changes to get manual ones
        inventory_manual_checker = InventoryManualChangesChecker(
            inventory_update_merged=inventory_data_joined,
            purchases_merged=purchases_data_merged,
        )

        manual_changes: dict[tuple[UUID,UUID], InventoryUpdateData] = inventory_manual_checker.get_manual_changes()

        if not manual_changes:
            logger.info(f"there is not manual changes for time interval start:'{any_to_sweden_time(self.start_date)}', end:'{any_to_sweden_time(self.end_date)}'")
            return None
        
        # get product data for manual changes
        product_data_fetcher:ProductDataFetcher = ProductDataFetcher(token_data=self.paypal_token) 
        product_data_manual = ManualProductData(
            manual_changes=manual_changes,
            organization_id=organization_id,
            product_data_fetcher=product_data_fetcher)
        
        product_data_with_manual_changes:list[PaypalProductData] =  product_data_manual.get_manual_changes_product_data()
        return product_data_with_manual_changes
