import sqlite3
from django.core.management.base import BaseCommand
from datetime import datetime
from django.db import connections

import psycopg2

class Command(BaseCommand):
    help = "Insert POH and POI Data to the database"

    def handle(self, *args, **kwargs):
        try:
            # Establish a connection to the PostgreSQL database
            # conn = psycopg2.connect(
            #     dbname='immdb',
            #     user='imm',
            #     password='mspl@2025$^',
            #     host="192.168.10.245",  
            #     port="5433"
            # )

            conn = psycopg2.connect(
                dbname='inventory',
                user='postgres',
                password='password',
                host="127.0.0.1",  
                port="5432"
            )
            
            # Create a cursor object
            cur = conn.cursor()

            # # Execute a sample query
            cur.execute("SELECT version();")

            # # Fetch the result
            db_version = cur.fetchone()
            print(f"PostgreSQL database version: {db_version}")

            # Example of inserting data (uncomment and modify as needed)
            #cur.execute("select * from imsapp_particular");
            #print(cur.fetchall());
            #conn.commit() # Commit changes for INSERT, UPDATE, DELETE

        except psycopg2.Error as e:
            print(f"Error connecting to PostgreSQL database: {e}")

        finally:
            # Close the cursor and connection
            # if cur:
            #     cur.close()
            # if conn:
            #     conn.close()
            print("PostgreSQL connection closed.")