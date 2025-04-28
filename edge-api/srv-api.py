## Copyright (C) 2025 Minh-Triet Nguyen-Ta <104993913@student.swin.edu.au>

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, List
import asyncio
import sqlite3
import serial

DATABASE_FILE = 'edge-database/sqlite.db'
DATABASE_TABLE = 'readings'
ARDUINO_PORT = 'COM7' # Linux: /dev/tty{USB,ACM}#, Windows: COM#

arduino = serial.Serial(ARDUINO_PORT, 9600, timeout=1)


class DatabaseConnection:
	"""Singleton class to manage connection to SQLite database."""
	_instance: 'DatabaseConnection' | None = None
	_connection: sqlite3.Connection | None = None

	def __new__(cls, *args, **kwargs) -> 'DatabaseConnection':
		if not cls._instance:
			cls._instance = super(DatabaseConnection, cls).__new__(cls, *args, **kwargs)
			cls._connection = sqlite3.connect(DATABASE_FILE)
		return cls._instance

	def query(self, query: str, params: tuple = ()) -> List[tuple]:
		"""Execute a query and return the results."""
		cursor: sqlite3.Cursor = self._connection.cursor()
		cursor.execute(query, params)
		return cursor.fetchall()

	def close_connection(self) -> None:
		"""Close connection to database."""
		if self._connection:
			self._connection.close()
			self._connection = None
			DatabaseConnection._instance = None


app = FastAPI(
    title="Hazardous MDV Edge API",
	description="Edge Device API for Hazardous MDV system - SWE30011 Individual Practical Assignment",
	version="1.0.0",
	docs_url="/docs",
	redoc_url="/redoc",
)

async def stream_latest_readings() -> AsyncGenerator[dict, None]:
	"""Stream the latest sensor readings."""
	db_conn = DatabaseConnection()
	while True:
		entry = db_conn.query(f'SELECT * FROM {DATABASE_TABLE} ORDER BY id DESC LIMIT 1')[0]
		if entry: yield {
			"lpg": entry[1],
			"ch4": entry[2],
			"co": entry[3],
			"temp": entry[4]
		}
		await asyncio.sleep(4)


@app.get("/readings")
async def get_latest_readings():
	"""Stream the latest sensor readings as a response."""
	async def generator():
		async for reading in stream_latest_readings():
			yield f"{reading}\n\n"

	return StreamingResponse(
		generator(),
		media_type="text/event-stream",
		headers={"Access-Control-Allow-Origin": "*"}
	)

@app.get("/response_system/{command}")
def toggle_response_system(command: str):
	"""Toggle the response system based on the command."""
	encodeCommand = {
		"engage": b"2",
		"disengage": b"0"
	}

	if command not in encodeCommand: return { "status": "invalid" }

	arduino.write(encodeCommand[command])

	return { "status": "engaged" if command == "engage" else "disengaged" }
