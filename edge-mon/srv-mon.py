## Copyright (C) 2025 Minh-Triet Nguyen-Ta <104993913@student.swin.edu.au>

import aiohttp
import asyncio
import logging
import os
import json

API_URL = os.getenv("API_URL", "http://localhost:8000")
DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"

SAFE_LIMITS = {
	"lpg": 1000,
	"ch4": 1000,
	"co": 9,
	"temp": 50
}


async def main():
	"""Main monitoring daemon procedure."""
	logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

	async with aiohttp.ClientSession() as session:
		while True:
			async with session.get(API_URL + "/readings") as response:
				response.raise_for_status()
				async for line in response.content:
					if not line: continue

					readings: dict = json.loads(line.decode('utf-8'))
					logging.info("Readings: %s", readings)

					limit_exceeded = any(readings[key] > SAFE_LIMITS[key] for key in SAFE_LIMITS)
					logging.info("Limit exceeded: %s", limit_exceeded)

					command = ("/engage" if limit_exceeded else "/disengage")
					await session.get(API_URL + "/response_system" + command)

			await asyncio.sleep(4)


if __name__ == "__main__":
	try:
		asyncio.run(main())
	except Exception as error:
		logging.error("* Error: %s", error)
	except KeyboardInterrupt:
		logging.info("* MON service manually stopped.")
