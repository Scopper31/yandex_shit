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


sqlite_connection = sql_connection()
sql_table(sqlite_connection)
sqlite_connection.close()
