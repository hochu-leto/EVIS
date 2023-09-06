import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT # <-- ADD THIS LINE

con = psycopg2.connect(dbname='postgres',
      user='postgres', host='localhost',
      port='5432', password='1111')

con.autocommit = True
# con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT) # <-- ADD THIS LINE

cur = con.cursor()

# Use the psycopg2.sql module instead of string concatenation
# in order to avoid sql injection attacks.
cur.execute(sql.SQL("CREATE DATABASE {}").format(
        sql.Identifier('sqlalchemy_tuts'))
    )
print("Database has been created successfully !!");

# Closing the connection
con.close()