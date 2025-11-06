# ---------------------------------------------------------------------------------------------- #
# THIS SCRIPT CREATES A SQLITE DATABASE WITH A SINGLE TABLE, CONTAINING PRODUCT ENTRIES BASED ON
# THE "LISTINGS.JSON" FILE GENERATED FROM STEP 1
# ---------------------------------------------------------------------------------------------- #
import json
import sqlite3

with open('listings.json', 'r') as f:
	data = json.load(f)

conn = sqlite3.connect('../abo.db')
cursor = conn.cursor()

# create table
table_name = 'listings'
columns_definition = []
for key, value in data[0].items():
    columns_definition.append(f"{key} TEXT")

create_table_sql = f'CREATE TABLE IF NOT EXISTS {table_name} ({", ".join(columns_definition)})'

cursor.execute(create_table_sql)
conn.commit() 

# insert values
columns = ','.join(data[0].keys())
question_marks = ','.join(['?' for item in data[0].keys()])
values = [tuple(item.values()) for item in data]
insert_sql = f'INSERT INTO {table_name} ({columns}) VALUES ({question_marks});'
cursor.executemany(insert_sql, values)
conn.commit() 

conn.close()