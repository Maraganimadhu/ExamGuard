
import sqlite3


DB="database/examguard.db"

def get_db():
    connection=sqlite3.connect(DB)
    return connection

# conn=sqlite3.connect(DB)
# cursor=conn.cursor()

# Create a table

def init_db():
    connection = get_db()
    connection.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL,
        photo TEXT
    )
    """)
    # connection.commit()
    # connection.close()
    # connection.execute("""
    #      ALTER TABLE candidates
    #     ADD COLUMN photo TEXT
    #  """)




    # connection.execute("""
    # drop table candidates
    # """)
    # connection.commit()
    # connection.close()
    # print("table dropped successfully")


    connection.commit()
    connection.close()
    print("data base created successfuly")
