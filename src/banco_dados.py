import os
import psycopg
from pathlib import Path
from dotenv import load_dotenv

# Carregar as variáveis do arquivo .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# Fazer conxao com banco de dados
def conectar():
    return psycopg.connect(
        host="127.0.0.1",
        port=5432,
        dbname="aps_reconhecimento_facial",
        user="aps_user",
        password=os.environ["POSTGRES_PASSWORD"]
    )
