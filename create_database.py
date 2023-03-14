import sqlite3
from sqlite3 import Error
from datetime import date, datetime, timedelta


def sql_connection():
    try:
        con = sqlite3.connect('sqlite_python.db')
        return con
    except Error:
        print(Error)


# def sql_table(con):
#     sqlite_create_table_query = '''CREATE TABLE sqlitedb_subscribers (
#                                         email text NOT NULL UNIQUE,
#                                         ending_date datetime);'''
#     cursor = con.cursor()
#     cursor.execute(sqlite_create_table_query)
#     con.commit()
#     cursor.close()
#
#
# sqlite_connection = sql_connection()
# sql_table(sqlite_connection)
# sqlite_connection.close()


# def delete_record(con):
#     time_now = datetime.now().date().isoformat()
#     sql_delete_query = f"""DELETE from sqlitedb_subscribers where ending_date < {time_now}"""
#     cursor = con.cursor()
#     cursor.execute(sql_delete_query)
#     con.commit()
#     cursor.close()
#
#
# sqlite_connection = sql_connection()
# delete_record(sqlite_connection)
# sqlite_connection.close()


# def add_subscriber(con, email):
#     time_now = datetime.now().date()
#     half_of_year = timedelta(days=182)
#     sql_insert_query = f"""INSERT INTO sqlitedb_subscribers VALUES ('{email}', {time_now + half_of_year})"""
#     cursor = con.cursor()
#     cursor.execute(sql_insert_query)
#     con.commit()
#     cursor.close()
# 
# 
# sqlite_connection = sql_connection()
# mail = input()
# add_subscriber(sqlite_connection, mail)
# sqlite_connection.close()
