# Copyright (C) 2025 Minh-Triet Nguyen-Ta <104993913@student.swin.edu.au>

from serial import Serial
import logging
import sqlite3

DEBUG_MODE = True
DATABASE_FILE = 'weather_data.db'
DATABASE_TABLE = 'weather'
SERIAL_PORT = '/dev/ttyACM0'


def setup_database(db_conn: sqlite3.Connection):
	"""Setup the SQLite database and create the table if not exist."""
	cursor = db_conn.cursor()

	cursor.execute(f'''
	CREATE TABLE IF NOT EXISTS {DATABASE_TABLE} (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		LPG REAL,
		CH4 REAL,
		CO REAL,
		Temperature REAL
	)
	''')

	db_conn.commit()


def generate() -> str:
	"""Generate mock data for testing."""
	import random
	import time

	time.sleep(1)  # Simulate interval between readings

	LPG = random.uniform(0, 100)
	CH4 = random.uniform(0, 100)
	CO = random.uniform(0, 100)
	Temperature = random.uniform(0, 100)

	return f'LPG:{LPG},CH4:{CH4},CO:{CO},Temperature:{Temperature}'


def extract(arduino: Serial) -> str | None:
	"""Extract data from the Arduino serial port."""
	if arduino.in_waiting > 0:
		line = arduino.readline().decode('utf-8').strip()
		return line
	return None


def transform(line: str) -> tuple:
	"""Transform serial line into a tuple for SQL."""
	data = {}

	for item in line.split(','):
		key, value = item.split(':')
		data[key.strip()] = float(value.strip())

	return tuple(data.values())


def load(data: tuple, db_conn: sqlite3.Connection, table_name: str) -> None:
	"""Load transformed data into the SQLite database."""
	cursor = db_conn.cursor()
	placeholders = ', '.join(['?'] * len(data))

	query = f"INSERT INTO {table_name} VALUES ({placeholders})"
	cursor.execute(query, data)

	db_conn.commit()


def main():
	"""Main ETL pipeline procedure."""
	arduino = Serial(SERIAL_PORT, 9600, timeout=1)
	db_conn = sqlite3.connect(DATABASE_FILE)

	try:
		while True:
			if DEBUG_MODE: logging.info('1. Extracting message')
			extracted = extract(arduino)

			if not extracted: continue

			if DEBUG_MODE: logging.info('2. Transforming to tuple')
			transformed = transform(extracted)

			if DEBUG_MODE: logging.info('3. Loading to SQLite database')
			load(transformed, db_conn, DATABASE_TABLE)
	finally:
		db_conn.close()
