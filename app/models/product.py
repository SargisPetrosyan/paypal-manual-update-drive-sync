from uuid import UUID
from pydantic import BaseModel
from datetime import datetime
from typing import  TypedDict
from dataclasses import dataclass
from app.constants import EMPTY_FIELD_NAME


class Price(BaseModel,str_strip_whitespace=True):
    amount:int
    currencyId:str

class Variants(BaseModel,str_strip_whitespace=True):
    uuid: UUID
    name: str | None
    price: Price | None
    costPrice: Price | None


class Category(BaseModel,str_strip_whitespace=True):
    uuid:UUID
    name:str

class ProductData(BaseModel, str_strip_whitespace=True):
    uuid: UUID
    categories: list[ None | str]
    name: str | None
    variants: list[Variants | None]
    category: Category | None


class Products(BaseModel,str_strip_whitespace=True):
    quantity: int
    productUuid: UUID
    variantUuid: UUID
    unitPrice: int
    name:str 
    variantName:str


class Purchases(BaseModel,str_strip_whitespace=True):
    amount:int
    timestamp:datetime
    products:list[Products]
    refunded: bool
    refund: bool

class ListOfPurchases(BaseModel):
    purchases: list[Purchases]

@dataclass
class PaypalProductData():
    organization_id: str
    product_variant_uuid: str
    before: int 
    after: int
    timestamp: datetime
    name: str
    variant_name: str 
    category_name: str 
    cost_price: str | int 
    selling_price: str | int

class ListOfProductData(TypedDict):
    list_of_products: dict[tuple[UUID,UUID], list[PaypalProductData]]
