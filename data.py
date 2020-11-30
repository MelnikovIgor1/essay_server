import sqlite3 as sql

con = sql.connect('database.db')
with con:
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS `users` (login TEXT, password TEXT, institution TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS `essays` (title TEXT, file_name TEXT, tags TEXT, author TEXT)")

    con.commit()

