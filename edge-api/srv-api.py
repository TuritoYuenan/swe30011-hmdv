## Copyright (C) 2025 Minh-Triet Nguyen-Ta <104993913@student.swin.edu.au>

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from typing import Optional
import asyncio
import sqlite3
import serial
import os

# Linux: /dev/tty{USB,ACM}#, Windows: COM#
ARDUINO_PORT = os.getenv("ARDUINO_PORT", 'COM8')
DATABASE_FILE = os.getenv("DATABASE_FILE", 'edge-database/sqlite.db')
DATABASE_TABLE = os.getenv("DATABASE_TABLE", 'readings')

arduino = serial.Serial(ARDUINO_PORT, 9600, timeout=1)


class DatabaseConnection:
	"""Singleton class to manage connection to SQLite database."""
	_instance: Optional['DatabaseConnection'] = None
	_connection: Optional[sqlite3.Connection] = None

	def __new__(cls, *args, **kwargs) -> 'DatabaseConnection':
		if not cls._instance:
			cls._instance = super(DatabaseConnection, cls).__new__(cls, *args, **kwargs)
			cls._connection = sqlite3.connect(DATABASE_FILE)
		return cls._instance

	def insert(self, query: str, params: tuple) -> None:
		"""Insert data into the database."""
		cursor: sqlite3.Cursor = self._connection.cursor()
		cursor.execute(query, params)
		self._connection.commit()

	def query(self, query: str, params: tuple = ()):
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


@app.post("/readings")
async def upload_readings(data: dict):
	"""Upload sensor readings to the database."""
	db_conn = DatabaseConnection()

	# Extract data from the JSON payload
	lpg = data.get("LPG")
	ch4 = data.get("CH4")
	co = data.get("CO")
	temp = data.get("Temperature")

	# Validate the data
	if lpg is None or ch4 is None or co is None or temp is None:
		return {"status": "error", "message": "Invalid data format"}

	# Insert data into the database
	query = f"INSERT INTO {DATABASE_TABLE} (LPG, CH4, CO, Temperature) VALUES (?, ?, ?, ?)"
	db_conn.insert(query, (lpg, ch4, co, temp))

	return {"status": "success", "message": "Data uploaded successfully"}


@app.get("/readings")
async def stream_latest_readings():
	"""Stream the latest sensor readings from database."""
	db_conn = DatabaseConnection()

	async def generator():
		while True:
			entry = db_conn.query(f'SELECT * FROM {DATABASE_TABLE} ORDER BY id DESC LIMIT 1')[0]
			if entry:
				data = {
					"lpg": entry[1],
					"ch4": entry[2],
					"co": entry[3],
					"temp": entry[4]
				}
				yield f"{data}\n"
			await asyncio.sleep(4)

	return StreamingResponse(
		generator(),
		media_type="application/json",
		headers={"Access-Control-Allow-Origin": "*"}
	)


@app.get("/serial")
async def stream_serial_data():
	"""Stream raw data from the Arduino serial port."""
	async def generator():
		while True:
			while arduino.in_waiting == 0: await asyncio.sleep(0.1)

			line = arduino.readline()
			yield f"{line.decode('utf-8').strip()}\n"
			await asyncio.sleep(1)

	return StreamingResponse(
		generator(),
		media_type="text/event-stream",
		headers={"Access-Control-Allow-Origin": "*"}
	)


@app.get("/response_system/{command}")
def toggle_response_system(command: str):
	"""Toggle the response system based on the command."""
	encodeCommand = { "engage": b"2", "disengage": b"0" }

	if command not in encodeCommand: return { "status": "invalid" }

	arduino.write(encodeCommand[command])

	return { "status": "engaged" if command == "engage" else "disengaged" }
