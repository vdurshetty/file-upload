import psycopg2
import os
from dotenv import load_dotenv  # only needed locally

load_dotenv()
pgvector_key = os.environ.get("pg_password")


# Connect to your database
conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password=pgvector_key,
    host="db.hjutiuttzsdrzoyzuzmx.supabase.co",
    port=5432
)
cursor = conn.cursor()


def pg_create_table_index(script):
    # Create a table with a vector column
    with cursor as cur:
        cur.execute(script)
        conn.commit()
    if "table" in script.lower():
        print("Table successfully created...")
    elif "index" in script.lower():
        print("Index successfully created...")


def pg_drop_table_index(table_name, object_type="TABLE"):
    sql = "DROP ".join(object_type).join(" IF EXISTS ").join(table_name).join(";")
    cursor.execute(sql)
    conn.commit()


def pg_insert(sql, text, embedding):
    cursor.execute(sql, (text, embedding))
    conn.commit()


def pg_execute(sql, embedding):
    cursor.execute(sql, (embedding,))
    return cursor.fetchall()


def pg_execute_many(sql, data):
    cursor.executemany(sql, data)
    conn.commit()
    print("Multiple Records Inserted")


def pg_sql_execute(sql):
    cursor.execute(sql)
    return cursor.fetchall()

# create vector extension in postgresql database
# pg_create_table("CREATE EXTENSION vector;")
