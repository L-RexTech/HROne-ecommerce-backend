from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ProductCreate(BaseModel):
    name: str
    price: float
    description: str
    category: str
    inventory_count: int
    size: str

class Product(BaseModel):
    id: str = Field(alias="_id")
    name: str
    price: float
    description: str
    category: str
    inventory_count: int
    size: str
    created_at: datetime

    class Config:
        populate_by_name = True

class OrderItem(BaseModel):
    product_id: str
    bought_quantity: int
    total_amount: float

class OrderCreate(BaseModel):
    items: List[OrderItem]
    total_amount: float
    user_address: Dict[str, Any]

class Order(BaseModel):
    id: str = Field(alias="_id")
    items: List[OrderItem]
    total_amount: float
    user_address: Dict[str, Any]
    created_at: datetime

    class Config:
        populate_by_name = True
