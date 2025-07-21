from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List
import re
from datetime import datetime
from bson import ObjectId
import json

from models import ProductCreate, Product, OrderCreate, Order
from database import products_collection, orders_collection

app = FastAPI(title="E-commerce Backend", version="1.0.0")

# Custom JSON Encoder for ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

@app.post("/products", status_code=201)
async def create_product(product: ProductCreate):
    """Create a new product"""
    product_dict = product.dict()
    product_dict["created_at"] = datetime.utcnow()
    
    result = products_collection.insert_one(product_dict)
    
    # Fetch the created product
    created_product = products_collection.find_one({"_id": result.inserted_id})
    created_product["_id"] = str(created_product["_id"])
    
    return created_product

@app.get("/products", status_code=200)
async def list_products(
    name: Optional[str] = Query(None, description="Filter by product name (supports regex)"),
    size: Optional[str] = Query(None, description="Filter by size"),
    limit: int = Query(10, ge=1, le=100, description="Number of products to return"),
    offset: int = Query(0, ge=0, description="Number of products to skip")
):
    """List products with optional filters"""
    
    # Build query filter
    query_filter = {}
    
    if name:
        # Support regex/partial search
        query_filter["name"] = {"$regex": name, "$options": "i"}
    
    if size:
        query_filter["size"] = size
    
    # Get total count for pagination info
    total = products_collection.count_documents(query_filter)
    
    # Fetch products with pagination
    cursor = products_collection.find(query_filter).sort("_id", 1).skip(offset).limit(limit)
    products = []
    
    for product in cursor:
        product["_id"] = str(product["_id"])
        products.append(product)
    
    return {
        "products": products,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }

@app.post("/orders", status_code=201)
async def create_order(order: OrderCreate):
    """Create a new order"""
    
    # Validate products exist and have sufficient inventory
    for item in order.items:
        product = products_collection.find_one({"_id": ObjectId(item.product_id)})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        
        if product["inventory_count"] < item.bought_quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient inventory for product {item.product_id}"
            )
    
    # Create order
    order_dict = order.dict()
    order_dict["created_at"] = datetime.utcnow()
    
    result = orders_collection.insert_one(order_dict)
    
    # Update inventory for each product
    for item in order.items:
        products_collection.update_one(
            {"_id": ObjectId(item.product_id)},
            {"$inc": {"inventory_count": -item.bought_quantity}}
        )
    
    # Fetch created order
    created_order = orders_collection.find_one({"_id": result.inserted_id})
    created_order["_id"] = str(created_order["_id"])
    
    return created_order

@app.get("/orders/{user_id}", status_code=200)
async def get_user_orders(
    user_id: str,
    limit: int = Query(10, ge=1, le=100, description="Number of orders to return"),
    offset: int = Query(0, ge=0, description="Number of orders to skip")
):
    """Get orders for a specific user"""
    
    # For this implementation, we'll filter by user_address containing user info
    # In a real app, you'd have a user_id field in orders
    query_filter = {"user_address.user_id": user_id}
    
    total = orders_collection.count_documents(query_filter)
    
    cursor = orders_collection.find(query_filter).sort("_id", 1).skip(offset).limit(limit)
    orders = []
    
    for order in cursor:
        order["_id"] = str(order["_id"])
        orders.append(order)
    
    return {
        "orders": orders,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }

@app.get("/")
async def root():
    return {"message": "E-commerce Backend API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
