import os
import psycopg


def conectar():
    return psycopg.connect(
        host="127.0.0.1",
        port=5432,
        dbname="aps_reconhecimento_facial",
        user="aps_user",
        password=os.environ["POSTGRES_PASSWORD"]
    )
