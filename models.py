from dataclasses import dataclass

from decimal import Decimal

@dataclass
class Customer:
    id:int
    name:str
    mobile:str
    email:str
    lifetime_profit:Decimal

@dataclass
class Product:

    id: int
    name: str
    category: str
    price: Decimal
    cost_price: Decimal
    stock: int


@dataclass
class CartItem:

    product_id: int
    quantity: int