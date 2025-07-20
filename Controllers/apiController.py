from typing import Dict, List, Any

from fastapi import HTTPException, status, FastAPI, Request
from pydantic import BaseModel


from Model.pluginModel import Model

collection = Model()

class WooCommerceProducts(BaseModel):
    site_url: str
    site_id: str
    products: List[Dict[str, Any]]

async def generate_embeddings(text:str):
    model =SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    embeddings = model.encode(text)
    print("embedding generation complete")
    print(embeddings)
    return embeddings

async def process_woocommerce_products(request: Request):
    try:
        data = await request.json()
        payload = WooCommerceProducts(**data)  # Validate the incoming data

        site_url = payload.site_url
        site_id = payload.site_id
        products = payload.products

        # Ensure site_url ends with a slash
        if not site_url.endswith('/'):
            site_url = site_url + '/'

        try:
            delete_result = collection.delete_many({"site_id": site_id, "for": "WooCommerce"})
            print(f"Deleted {delete_result.deleted_count} existing chunks for site_id: {site_id}")
        except Exception as e:
            print(f"Failed to delete existing chunks: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to clear existing chunks: {str(e)}"
            )

        total_products_processed = 0

        # Process the products received in the request
        for product in products:
            # Extract required fields
            product_data = {
                "name": product.get("title", ""),  # Assuming "title" is the product name
                "permalink": product.get("link", ""),  # Assuming "link" is the permalink
                "description": product.get("description", ""),
                "short_description": product.get("short_description", ""),
                "price": product.get("price", ""),
                "stock_status": product.get("stock_status", ""),
                "for":"WooCommerce",
                "site_id": site_id
            }

            # Create combined description field
            product_data["combined_description"] = f"{product_data['name']} {product_data['description']} {product_data['short_description']}. The price is {product_data['price']} {product_data['stock_status']}"

            # Generate embeddings for the combined description
            vectors = await generate_embeddings(product_data["combined_description"])
            embeddings = vectors.tolist()

            # Add embeddings to product data
            product_data["embeddings"] = embeddings

            # Store in database
            collection.insert_one(product_data)

            total_products_processed += 1
            print(f"total processed:{total_products_processed}")

        return {
            "status": "success",
            "products_processed": total_products_processed,
            "message": f"Successfully processed {total_products_processed} products from WooCommerce"
        }

    except HTTPException as e:
        print(f"HTTPException occurred: {e}")
        raise e
    except Exception as e:
        print(f"Exception occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing WooCommerce products: {str(e)}"
        )