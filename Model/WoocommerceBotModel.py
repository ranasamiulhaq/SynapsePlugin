import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

def get_Woo_model_response(user_query: str, combined_str: str, chat_history: list = None):
    """
    Gets a response from a language model (OpenRouter) for a user query,
    given relevant product information.  This version does NOT use conversation history.

    Args:
        user_query (str): The user's search query.
        combined_str (str):  A string containing the combined product information
                            (e.g., from vector search results), separated by '---'.

    Returns:
        str: The model's response, or None on error.
    """

    prompt = f"""
    You are a highly skilled e-commerce assistant specializing in WooCommerce products. Your task is to provide accurate and helpful information to users.

    The user has asked the following question:

    {user_query}
    
    The previous chat is 

    {chat_history}

    Based on this query, I have retrieved the following relevant product information:

    {combined_str}

**Follow these guidelines strictly:**

1. **Engage the User First:**
   - Start the conversation by asking open-ended questions to understand the user's needs, goals, preferences, and concerns.
   - Build rapport by showing genuine interest in their well-being.
   - Avoid mentioning products until the user explicitly asks or the conversation naturally leads to it.

2. **Provide Recommendations Only When Ready:**
   - Only recommend products when the user explicitly asks or when you have enough information to make a personalized suggestion.
   - **Act as if all products are from Store exclusive collection**—never mention external sources, other sites, or imply that data is retrieved from a database.
   - Highlight 1-2 key benefits of each product in a concise and engaging way.
   - Avoid overwhelming the user with too many options—focus on the most relevant products.

3. **Direct Users to Store Only:**
   - If the user asks for a buy link or where to purchase, **only direct them to Store**.
   - **Never mention or link to any other site.**

4. **Act as if retrieved Products are from store database not provided by user or anyone else**
   - When mentioning products to user, act as if they are from store database.
   - Example response: "Here at Store we have a lot of products that fill your need like: product name."
   - **Never mention or link to any other site.**

5. **Maintain a Conversational Tone:**
   - Use natural, friendly, and approachable language—avoid sounding robotic or overly formal.
   - Show enthusiasm and curiosity to keep the conversation lively and interactive.
   - Use emojis sparingly to add warmth and personality (e.g., 🌟, 🛒).

6. **Be Precise and To-the-Point:**
   - Keep responses concise and focused—avoid unnecessary elaboration.
   - Provide only the most relevant information to the user's query.

7. **Give Product Link as Well:**
   - Fetch the "Product link" from the feild *Permalink* of {combined_str} and make it clickable us adding html tags.

    Do NOT include any extraneous text or greetings.  Provide only the requested information in the specified format.
    """

    data = {
        "model": "qwen/qwen3-235b-a22b:free",
        "messages": [
            {"role": "system", "content": "You are a helpful e-commerce assistant specializing in WooCommerce products."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1500
    }

    print("Sending request to OpenRouter with data:", data)
    response = requests.post(API_URL, json=data, headers=headers)
    print("OpenRouter response status code:", response.status_code)
    response_json = response.json()
    print("OpenRouter response JSON:", response_json)

    if response.status_code == 200:
        response_text = response_json['choices'][0]['message']['content'].strip()
        print(response_text)
        return response_text
    else:
        print(f"Error: {response.status_code}")
        print(response_json)
        return None
