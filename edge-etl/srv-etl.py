## Copyright (C) 2025 Minh-Triet Nguyen-Ta <104993913@student.swin.edu.au>

from serial import Serial
import logging
import sqlite3
import time

DEBUG_MODE = True
DATABASE_FILE = 'edge-database/sqlite.db'
DATABASE_TABLE = 'readings'
SERIAL_PORT = 'COM11'


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

	time.sleep(4)

	LPG = random.randint(0, 100)
	CH4 = random.randint(0, 100)
	CO = random.randint(0, 100)
	Temperature = round(random.uniform(20, 60), 2)

	return f'LPG:{LPG},CH4:{CH4},CO:{CO},Temperature:{Temperature}'


def extract(arduino: Serial) -> str:
	"""Extract data from the Arduino serial port."""
	line = arduino.readline()
	return line.decode('utf-8').strip()


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

	query = f"INSERT INTO {table_name} (LPG, CH4, CO, Temperature) VALUES ({placeholders})"
	cursor.execute(query, data)

	db_conn.commit()


def main():
	"""Main ETL pipeline procedure."""
	logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
	if DEBUG_MODE: logging.info('Starting ETL pipeline')

	arduino = Serial(SERIAL_PORT, 9600, timeout=1)
	db_conn = sqlite3.connect(DATABASE_FILE)
	setup_database(db_conn)

	try:
		while True:
			while arduino.in_waiting == 0: time.sleep(1)

			# extracted = generate()
			extracted = extract(arduino)
			if DEBUG_MODE: logging.info('1. Extracted: %s', extracted)

			transformed = transform(extracted)
			if DEBUG_MODE: logging.info('2. Transformed to tuple')

			load(transformed, db_conn, DATABASE_TABLE)
			if DEBUG_MODE: logging.info('3. Loaded to SQLite')

			time.sleep(2)
	except KeyboardInterrupt:
		if DEBUG_MODE: logging.warning('ETL pipeline manually stopped')
	finally:
		if DEBUG_MODE: logging.info('Closing database connection')
		db_conn.close()
		arduino.close()

if __name__ == "__main__": main()
