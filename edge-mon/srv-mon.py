import aiohttp
import asyncio
import json
import logging
import os

SAFE_LIMITS = {
	"lpg": 1000,
	"ch4": 2000,
	"co": 50,
	"temp": 50
}

API_URL = os.getenv("API_URL", "http://localhost:8000")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"


async def check_readings(data_url, respond_url):
	async with aiohttp.ClientSession() as session:
		async with session.get(data_url) as response:
			response.raise_for_status()
			async for line in response.content:
				if not line:
					continue

				data = line.decode('utf-8')
				readings: dict = json.loads(data)

				limit_exceeded = any(readings[key] > SAFE_LIMITS[key] for key in SAFE_LIMITS)
				action_url = respond_url + ("/engage" if limit_exceeded else "/disengage")

				await session.post(action_url)


async def main():
	try:
		while True:
			await check_readings(API_URL + "/readings", API_URL + "/response_system")
			await asyncio.sleep(4)
	except Exception as error:
		logging.error("Error: %s", error)
	except KeyboardInterrupt:
		logging.info("* MON service manually stopped.")


if __name__ == "__main__":
	asyncio.run(main())
