import aiohttp
import os

API_URL = "https://openrouter.ai/api/v1/chat/completions"


async def query_openrouter(user_input: str, system_prompt: str) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return "❌ Error: OpenRouter API key not found."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/mistral-7b-instruct:free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        "max_tokens": 300,
        "temperature": 0.7
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=headers, json=payload) as response:
            data = await response.json()
            print(f"Response status: {response.status}")
            print(f"Response data: {data}")

            if response.status == 200:
                try:
                    return data["choices"][0]["message"]["content"]
                except Exception as e:
                    return f"Error parsing response: {str(e)}"
            else:
                return f"Error {response.status}: {data}"

