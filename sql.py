import sqlite3
from sqlite3 import Error
from datetime import date, datetime, timedelta


def sql_connection():
    try:
        con = sqlite3.connect('sqlite_python.db')
        return con
    except Error:
        print(Error)


def sql_table(con):
    sqlite_create_table_query = '''CREATE TABLE sqlitedb_subscribers (
                                        email TEXT NOT NULL UNIQUE,
                                        ending_date timestamp);'''
    cursor = con.cursor()
    cursor.execute(sqlite_create_table_query)
    con.commit()
    cursor.close()


# sqlite_connection = sql_connection()
# sql_table(sqlite_connection)
# sqlite_connection.close()


def delete_pidor(con, email):
    sql_delete_query = f"""DELETE from sqlitedb_subscribers where email == {email}"""
    cursor = con.cursor()
    cursor.execute(sql_delete_query)
    con.commit()
    cursor.close()


# pidors_email = input()
# sqlite_connection = sql_connection()
# delete_pidor(sqlite_connection, pidors_email)
# sqlite_connection.close()



def delete_record(con):
    time_now = datetime.now().date()
    sql_delete_query = f"""DELETE from sqlitedb_subscribers where ending_date < {time_now}"""
    cursor = con.cursor()
    cursor.execute(sql_delete_query)
    con.commit()
    cursor.close()


# sqlite_connection = sql_connection()
# delete_record(sqlite_connection)
# sqlite_connection.close()


def add_subscriber(con, email):
    try:
        time_now = datetime.now().date()
        half_of_year = timedelta(days=182)
        ending_time = time_now + half_of_year
        sql_insert_query = """INSERT INTO 'sqlitedb_subscribers'
                                  ('email', 'ending_date')
                                  VALUES (?, ?);"""
        cursor = con.cursor()
        cursor.execute(sql_insert_query, (email, ending_time))
        con.commit()
        cursor.close()
    except Error:
        print('такой уже есть')


# sqlite_connection = sql_connection()
# mail = input()
# add_subscriber(sqlite_connection, mail)
# sqlite_connection.close()


def check_subscribtion(con, mail):
    time_now = datetime.now().date()
    sqlite_select_query = """SELECT * from sqlitedb_subscribers where email = ?"""
    cursor = con.cursor()
    cursor.execute(sqlite_select_query, (mail,))
    record = cursor.fetchone()
    time = date(*list(map(int, record[1].split('-'))))
    if time > time_now:
        con.commit()
        cursor.close()
        return True
    con.commit()
    cursor.close()
    return False


# sqlite_connection = sql_connection()
# mail = input()
# print(check_subscribtion(sqlite_connection, mail))
# sqlite_connection.close()


def check_existence(con, mail):
    cursor = con.cursor()
    info = cursor.execute('SELECT * FROM sqlitedb_subscribers WHERE email=?', (mail,))
    if info.fetchone() is None:
        return False
    else:
        return True

# sqlite_connection = sql_connection()
# mail = input()
# print(check_existence(sqlite_connection, mail))
# sqlite_connection.close()
