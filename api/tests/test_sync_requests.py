from json import load
import httpx
import asyncio

API_KEY = "c8af290f6d9b4d14bfe201727261202"
params = {"key": API_KEY, "q": "Minsk"}
response = httpx.get("http://api.weatherapi.com/v1/current.json", params=params)
print(response.status_code)
print(response.json())
# response_dict = load(response.json())

params = {"key": API_KEY, "q": "Minsk"}
response = httpx.post("http://httpbin.org/post", data=params)
print(response.status_code)
print(response.json())

async def get_weather():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://api.weatherapi.com/v1/current.json", params=params)
        return response.json()

asyncio.run(get_weather())
