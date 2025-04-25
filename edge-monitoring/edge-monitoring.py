## Copyright (C) 2025 Minh-Triet Nguyen-Ta <104993913@student.swin.edu.au>

from serial import Serial
import logging
import sqlite3
import time

DEBUG_MODE = True
DATABASE_FILE = 'edge-database/sqlite.db'
DATABASE_TABLE = 'readings'
SERIAL_PORT = 'COM11'

query = f"""SELECT CO, CH4, LPG, temperature FROM {DATABASE_TABLE} ORDER BY timestamp DESC LIMIT 1"""

def main():
	"""Main monitoring daemon procedure."""
	if DEBUG_MODE: logging.info('Starting ETL pipeline')

	arduino = Serial(SERIAL_PORT, 9600, timeout=1)
	db_conn = sqlite3.connect(DATABASE_FILE)

	try:
		while True:
			cursor = db_conn.cursor()
			cursor.execute(query)
			result = cursor.fetchone()

			if result:
				co, ch4, lpg, temperature = result
				if co > 50 or ch4 > 50 or lpg > 50 or temperature > 50:
					arduino.write(b'2')
					if DEBUG_MODE: logging.info('Potential leakage!')
				else:
					arduino.write(b'0')
					if DEBUG_MODE: logging.info('Readings are normal')

			time.sleep(4)
	finally:
		if DEBUG_MODE: logging.info('Closing database connection')
		db_conn.close()
		arduino.close()

if __name__ == "__main__": main()
