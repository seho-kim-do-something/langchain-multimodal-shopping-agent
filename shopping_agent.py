from typing import Optional

import json
import base64
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_groq import ChatGroq
from db_service import create_order, get_product_rating, search_products_from_db
from langchain_core.messages import HumanMessage

load_dotenv()

llm = ChatGroq(model="qwen/qwen3-32b", temperature=0)
vision_llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", temperature=0)

@tool
def search_products(query: str, max_price: Optional[float] = None, is_organic: Optional[bool] = None) -> str:
    """
    Search the product database by keyword.

    Args:
        query: Keyword matched against product name, description, and category.
        max_price: Optional maximum product price.
        is_organic: Optional organic filter. Use True for organic products and False for non-organic products.

    Returns:
        A JSON array of matching products, each containing id, name, category, price, description, and is_organic.
    """
    products = search_products_from_db(query=query, max_price=max_price, is_organic=is_organic)
    return json.dumps(products)

@tool
def get_rating(product_id: int) -> str:
    """
    Return the average rating and review count for a single product.

    Args:
        product_id: The ID of the product.

    Returns:
        A JSON object containing product_id, average_rating, and review_count.
    """
    result = get_product_rating(product_id)
    return json.dumps(result)


@tool
def checkout(product_id: int) -> str:
    """
    Place an order for the given product ID.

    Args:
        product_id: The ID of the product to order.

    Returns:
        A JSON object containing the order confirmation details.
    """
    result = create_order(product_id)
    return json.dumps(result)

@tool
def describe_product_image(image_path: str) -> str:
    """
    Analyze a product image and return its key attributes as a JSON object.

    Use this when the user uploads a photo of a product they are interested in.
    The returned attributes can be used directly with search_products.
    """

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    ext = os.path.splitext(image_path)[1].lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

    message = HumanMessage(
        content=[
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{image_data}"},
            },
            {
                "type": "text",
                "text": (
                    "Look at this product image and extract its key attributes. "
                    "If the image does not appear to be a retail product, return null for product_type, search_query, and is_organic. "
                    "Return ONLY a JSON object with these fields:\n"
                    "- product_type: what kind of product it is (e.g. honey, olive oil, almonds)\n"
                    "- search_query: a short keyword to search for it (e.g. 'honey', 'olive oil')\n"
                    "- is_organic: true if the label says organic, false if not, null if unclear\n"
                    "- description: one sentence describing the product\n"
                    "\n"
                    "Example for a non-product image:\n"
                    "{\n"
                    "  \"product_type\": null,\n"
                    "  \"search_query\": null,\n"
                    "  \"is_organic\": null,\n"
                    "  \"description\": \"The image does not appear to show a retail product.\"\n"
                    "}"
                ),
            },
        ]
    )

    response = vision_llm.invoke([message])
    return response.content

agent = create_agent(
    tools=[search_products, get_rating, checkout, describe_product_image],
    model=llm,
    system_prompt=(
        "You are a helpful shopping assistant. Follow these rules strictly.\n\n"
        "IMAGE SEARCH - when the user provides an image path:\n"
        "1. Call describe_product_image with the provided image path to identify the product.\n"
        "2. Use the returned search_query and is_organic values to call search_products.\n"
        "3. Continue with the BROWSING flow from step 2 onward.\n\n"
        "BROWSING - when the user describes what they want to buy:\n"
        "1. Call search_products to find matching items. Apply any price or organic filters given by the user.\n"
        "   If search_products returns no matches, try one similar keyword or synonym once before saying no products were found.\n"
        "   Example: if the user searches for headset, also try headphones; if the user searches for earphones, also try earbuds.\n"
        "2. For each candidate product, call get_rating to retrieve its average rating.\n"
        "3. Filter by the user's minimum rating if specified.\n"
        "4. Present qualifying products as a numbered list using this exact plain-text format:\n"
        "   <number>. <name> (ID:<product_id>) - $<price> - <rating> stars - <organic or non-organic>\n"
        "   Add a blank line between each product entry. Always include (ID:X) so the product can be referenced later.\n"
        "5. If only one product qualifies, still show it in the list and ask: Would you like to order it? Just say yes or give me the number.\n"
        "6. Do not call checkout during the search/recommendation step.\n\n"
        "SCOPE RULES:\n"
        "1. You only assist with product search, product ratings, product image search, and product ordering.\n"
        "2. If a question is unrelated to shopping, products, product images, ratings, or orders, politely refuse and say: I'm a shopping assistant and can only help with product search, ratings, image-based product search, and ordering.\n"
        "3. Do not answer general knowledge, programming, history, science, math, politics, or other unrelated questions.\n"
        "4. Do not invent products that are not returned by search_products.\n"
        "5. If search_products returns no matches after one synonym retry, tell the user that no matching products were found.\n"
        "6. Only use information available through the provided tools.\n\n"
        "ORDERING RULES:\n"
        "1. Only call checkout when the user clearly confirms they want to buy, such as yes, sure, go ahead, order number 2, the first one, or get me #3.\n"
        "2. Look at your previous message to find the product ID for the chosen product. If only one product was listed and the user says yes, use that product ID.\n"
        "3. Call checkout with the selected product_id.\n"
        "4. Confirm the order to the user in plain text.\n"
        "5. Never place an order unless the user explicitly confirms.\n"
        "6. Never guess a product_id. Always take it from the (ID:X) in your own previous message."
    ),
)

if __name__ == "__main__":
    response = agent.invoke({
        "messages": [{
            "role": "user",
            "content": "I want organic beauty products under $25 with 4+ rating",
        }]
    })
    print(response["messages"][-1].content)

    # image_path = os.path.join("resources", "organic-honey.png")
    # response = describe_product_image.invoke({
    #     "image_path": image_path
    # })
    # print("Image description response:", response)