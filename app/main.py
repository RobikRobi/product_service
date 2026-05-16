import os
from contextlib import asynccontextmanager


from fastapi import FastAPI, HTTPException, status
from psycopg import DatabaseError

from product_service.app.db import get_connection, init_db
from product_service.app.shemas import CreateProduct
from product_service.app.utillits import get_user_from_users_service




USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://0.0.0.0:8001")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "products_service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Products Service", lifespan=lifespan, root_path="/products")


@app.get("/status")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "products_service",
        "served_by": INSTANCE_NAME,
        "users_service_url": USERS_SERVICE_URL,
    }


@app.post("/create", status_code=status.HTTP_201_CREATED)
async def create_product(data: CreateProduct) -> dict[str, int | str | float | dict]:
    owner = await get_user_from_users_service(data.owner_user_id)

    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO products (name, description, price, quantity, owner_user_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    data.name,
                    data.description,
                    data.price,
                    data.quantity,
                    data.owner_user_id,
                ),
            )
            product_id = cursor.fetchone()["id"]
    except DatabaseError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create product",
        ) from error

    return {
        "id": product_id,
        "name": data.name,
        "description": data.description,
        "price": data.price,
        "quantity": data.quantity,
        "owner_user_id": data.owner_user_id,
        "owner": owner,
    }


@app.get("/all")
async def all_products() -> dict:
    with get_connection() as connection:
        rows = connection.execute("SELECT id, name, description, price, quantity, owner_user_id " \
        "FROM products " \
        "ORDER BY id").fetchall()
        return {
        "served_by": INSTANCE_NAME,
        "items": [dict(row) for row in rows],
    }

@app.get("/{product_id}")
async def get_product_id(product_id: int) -> dict:
    with get_connection() as connection:
        row = connection.execute("SELECT id, name, description, price, quantity, owner_user_id " \
                                 "FROM products " \
                                 "WHERE id = %s",
                                 (product_id,),
                                 ).fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found",
            )
        product = dict(row)
        product["owner"] = await get_user_from_users_service(product["owner_user_id"])
        product["served_by"] = INSTANCE_NAME
        return product
