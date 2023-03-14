import sqlite3
from sqlite3 import Error


def sql_connection():
    try:
        con = sqlite3.connect('sqlite_python.db')
        return con
    except Error:
        print(Error)


def sql_table(con):
    sqlite_create_table_query = '''CREATE TABLE sqlitedb_subscribers (
                                        email text NOT NULL UNIQUE,
                                        joining_date datetime);'''
    cursor = con.cursor()
    cursor.execute(sqlite_create_table_query)
    con.commit()


sqlite_connection = sql_connection()
sql_table(sqlite_connection)
