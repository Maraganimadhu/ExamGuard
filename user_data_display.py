from database import get_db
import sqlite3

conn=get_db()

cursor=conn.cursor()

data=cursor.execute("""SELECT * FROM candidates""").fetchall()


for i in data:
    print(i)


conn.close()