import aiohttp

async def check_text_with_languagetool(text):
    url = "https://api.languagetool.org/v2/check"
    params = {
        "text": text,
        "language": "en-US"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=params) as response:
            result = await response.json()
            return result
