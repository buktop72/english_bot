import aiohttp
import ssl
from config import HF_API_TOKEN

API_URL = "https://api-inference.huggingface.co/models/bigscience/bloom-560m"


headers = {
    "Authorization": f"Bearer {HF_API_TOKEN}"
}

ssl_context = ssl.create_default_context(cafile="cacert.pem")

async def query_huggingface(prompt: str) -> str:
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 200,
            "temperature": 0.7
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=headers, json=payload, ssl=ssl_context) as response:
            print(f"Response status: {response.status}")
            data = await response.json()
            print(f"Response data: {data}")

            if response.status == 200:
                try:
                    return data[0].get("generated_text", "No generated_text found.")
                except Exception as e:
                    return f"Error parsing response: {str(e)}"
            else:
                return f"Error {response.status}: Unable to connect to Hugging Face API."

