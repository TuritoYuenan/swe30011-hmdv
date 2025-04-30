## Copyright (C) 2025 Minh-Triet Nguyen-Ta <104993913@student.swin.edu.au>

import logging
import asyncio
import aiohttp

DEBUG_MODE = True


def generate() -> str:
	"""Generate mock data for testing."""
	import random
	import time

	time.sleep(4)

	lpg = random.randint(0, 100)
	ch4 = random.randint(0, 100)
	co = random.randint(0, 100)
	temp = round(random.uniform(20, 60), 2)

	return f'LPG:{lpg},CH4:{ch4},CO:{co},Temperature:{temp}'


async def extract(session: aiohttp.ClientSession, stream_url: str):
	"""Extract data from the serial stream."""
	async with session.get(stream_url) as response:
		async for raw_data in response.content:
			yield raw_data


def transform(raw_data: bytes):
	"""Transform serial line into JSON/dict."""
	data_line = raw_data.decode('utf-8').strip()
	json_data = dict(item.split(":") for item in data_line.split(","))
	return json_data


async def load(session: aiohttp.ClientSession, post_url: str, data: dict):
	"""Load transformed data into the database via POST endpoint."""
	async with session.post(post_url, json=data) as response:
		result = await response.text()
		return result


async def main(stream_url: str, post_url: str):
	"""Main ETL pipeline procedure."""
	logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

	async with aiohttp.ClientSession() as session:
		async for extracted in extract(session, stream_url):
			if DEBUG_MODE: logging.info('=> Extracted: %s', extracted)
			transformed = transform(extracted)
			if DEBUG_MODE: logging.info('==> Transformed: %s', transformed)
			load_result = await load(session, post_url, transformed)
			if DEBUG_MODE: logging.info('===> Loaded with response: %s', load_result)


if __name__ == "__main__":
	try:
		url_stream = "http://localhost:8000/serial"
		url_post = "http://localhost:8000/readings"
		asyncio.run(main(url_stream, url_post))
	except KeyboardInterrupt:
		logging.info("* ETL service manually stopped")
