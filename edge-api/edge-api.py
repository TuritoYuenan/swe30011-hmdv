## Copyright (C) 2025 Minh-Triet Nguyen-Ta <104993913@student.swin.edu.au>

from fastapi import FastAPI, WebSocket
from typing import List, Optional
import asyncio
import sqlite3

DATABASE_FILE = 'edge-database/sqlite.db'
DATABASE_TABLE = 'readings'


class DatabaseConnection:
	"""Singleton class to manage connection to SQLite database."""
	_instance: Optional['DatabaseConnection'] = None
	_connection: Optional[sqlite3.Connection] = None

	def __new__(cls, *args, **kwargs) -> 'DatabaseConnection':
		if not cls._instance:
			cls._instance = super(DatabaseConnection, cls).__new__(cls, *args, **kwargs)
			cls._connection = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
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


@app.get("/")
def read_root():
	return {
		"message": "Welcome to the Edge Device API",
		"endpoints": {
			"readings": "/readings",
			"latest_reading": "/readings/latest",
			"docs": "/docs",
			"redoc": "/redoc"
		}
	}


@app.get("/readings")
def get_readings():
	"""Get 10 latest sensor readings"""
	db_conn = DatabaseConnection()
	entries = db_conn.query(f'SELECT * FROM {DATABASE_TABLE} ORDER BY id DESC LIMIT 10')

	return [
		{ 'lpg': row[1], 'ch4': row[2], 'co': row[3], 'temp': row[4] }
		for row in entries
	]


@app.websocket("/readings/latest")
async def get_latest_reading(websocket: WebSocket):
	"""Get the latest sensor readings"""
	await websocket.accept()
	db_conn = DatabaseConnection()

	while True:
		entry = db_conn.query(f'SELECT * FROM {DATABASE_TABLE} ORDER BY id DESC LIMIT 1')[0]

		if entry: await websocket.send_json({
			'lpg': entry[1], 'ch4': entry[2], 'co': entry[3], 'temp': entry[4]
		})
		else: await websocket.send_json({
			'lpg': None, 'ch4': None, 'co': None, 'temp': None
		})

		await asyncio.sleep(4)
