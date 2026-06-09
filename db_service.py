"""
Database service for the shopping agent project.

This module contains the SQLite database access logic used by LangChain tools.
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "store.db")

def search_products_from_db(query: str, max_price: float | None = None, is_organic: bool | None = None) -> list[dict]:
    """
    Search products from the SQLite database.

    Args:
        query: Keyword matched against product name, description, and category.
        max_price: Optional maximum product price.
        is_organic: Optional organic filter.

    Returns:
        A list of matching product dictionaries.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    sql = "SELECT id, name, category, price, description, is_organic FROM products WHERE 1=1"
    params: list = []

    if query:
        sql += " AND (name LIKE ? OR description LIKE ? OR category LIKE ?)"
        like = f"%{query}%"
        params.extend([like, like, like])

    if max_price is not None:
        sql += " AND price <= ?"
        params.append(max_price)

    if is_organic is not None:
        sql += " AND is_organic = ?"
        params.append(1 if is_organic else 0)

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "category": row[2],
            "price": row[3],
            "description": row[4],
            "is_organic": bool(row[5]),
        }
        for row in rows
    ]

def get_product_rating(product_id: int) -> dict:
    """
    Return the average rating and review count for a single product.

    Args:
        product_id: The ID of the product.

    Returns:
        A dictionary containing product_id, average_rating, and review_count.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT AVG(rating), COUNT(*) FROM reviews WHERE product_id = ?",
        (product_id,),
    )

    row = cursor.fetchone()
    conn.close()

    average_rating = round(row[0], 2) if row and row[0] is not None else 0.0
    review_count = row[1] if row else 0

    return {"product_id": product_id, "average_rating": average_rating, "review_count": review_count}

def get_ratings_for_products(product_ids: list[int]) -> list[dict]:
    """
    Return rating summaries for multiple products.

    Args:
        product_ids: A list of product IDs.

    Returns:
        A list of dictionaries containing product_id, average_rating, and review_count.
    """
    if not product_ids:
        return []

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    placeholders = ",".join("?" * len(product_ids))

    cursor.execute(
        f"SELECT product_id, AVG(rating), COUNT(*) FROM reviews WHERE product_id IN ({placeholders}) GROUP BY product_id",
        product_ids,
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "product_id": row[0],
            "average_rating": round(row[1], 2),
            "review_count": row[2],
        }
        for row in rows
    ]

def create_order(product_id: int) -> dict:
    """
    Place an order for the given product ID.

    Creates a new order in the database and returns structured order details.
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, price FROM products WHERE id = ?",
        (product_id,),
    )

    row = cursor.fetchone()

    if not row:
        conn.close()
        return {
            "success": False,
            "message": f"Product with ID {product_id} not found.",
        }

    product_name, price = row

    cursor.execute(
        """
        INSERT INTO orders
        (
            product_id,
            customer_name,
            quantity,
            order_date,
            status,
            total_price
        )
        VALUES (?, ?, ?, DATE('now'), ?, ?)
        """,
        (
            product_id,
            "Demo Customer",
            1,
            "Pending",
            price,
        ),
    )

    order_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "success": True,
        "order_id": order_id,
        "product_id": product_id,
        "product_name": product_name,
        "quantity": 1,
        "status": "Pending",
        "total_price": price,
    }

if __name__ == "__main__":
    print("Search products test:")
    print(search_products_from_db(query="honey", max_price=20, is_organic=True))

    print("\nSingle product rating:")
    print(get_product_rating(1))

    print("\nBatch ratings:")
    print(get_ratings_for_products([1, 3, 5, 7]))

    print("\nCheckout test:")
    print(checkout(1))