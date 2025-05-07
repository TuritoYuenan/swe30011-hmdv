## Copyright (C) 2025 Minh-Triet Nguyen-Ta <104993913@student.swin.edu.au>

from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
import asyncio
import sqlite3
import serial
import os
import json

# Linux: `/dev/tty{USB,ACM}#`, Windows: `COM#`
ARDUINO_PORT = os.getenv("ARDUINO_PORT", 'COM8')
DATABASE_FILE = os.getenv("DATABASE_FILE", 'database-edge/sqlite.db')
DATABASE_TABLE = os.getenv("DATABASE_TABLE", 'readings')

arduino = serial.Serial(ARDUINO_PORT, 9600, timeout=1)
db_conn = sqlite3.connect(DATABASE_FILE)
db_conn.execute(f"""
CREATE TABLE IF NOT EXISTS {DATABASE_TABLE} (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	LPG REAL NOT NULL,
	CH4 REAL NOT NULL,
	CO REAL NOT NULL,
	Temperature REAL NOT NULL,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
db_conn.commit()


def db_insert(query: str, params: tuple) -> None:
	"""Insert data into the database."""
	cursor: sqlite3.Cursor = db_conn.cursor()
	cursor.execute(query, params)
	db_conn.commit()


def db_query(query: str, params: tuple = ()):
	"""Execute a query and return the results."""
	cursor: sqlite3.Cursor = db_conn.cursor()
	cursor.execute(query, params)
	return cursor.fetchall()


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
	db_insert(query, (lpg, ch4, co, temp))

	return {"status": "success", "message": "Data uploaded successfully"}


@app.get("/readings")
async def stream_latest_readings():
	"""Stream the latest sensor readings from database."""
	async def generator():
		while True:
			entry = db_query(f'SELECT * FROM {DATABASE_TABLE} ORDER BY id DESC LIMIT 1')
			if entry:
				data = {
					"lpg": entry[0][1],
					"ch4": entry[0][2],
					"co": entry[0][3],
					"temp": entry[0][4]
				}
				yield f"{json.dumps(data)}\n"
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

			line = arduino.readline().decode('utf-8').strip()
			yield (line + "\n")
			await asyncio.sleep(1)

	return StreamingResponse(
		generator(),
		media_type="text/event-stream",
		headers={"Access-Control-Allow-Origin": "*"}
	)


@app.get("/response_system/{command}")
def toggle_response_system(response: Response, command: str):
	"""Toggle the response system based on the command."""
	response.headers["Access-Control-Allow-Origin"] = "*"
	match command:
		case "engage":
			arduino.write(b"2")
			return { "status": "engaged" }
		case "disengage":
			arduino.write(b"0")
			return { "status": "disengaged" }
		case _:
			return { "status": "invalid" }
