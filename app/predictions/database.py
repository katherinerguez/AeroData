from sqlalchemy import create_engine, MetaData, Table
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Construir URL de conexión (asegúrate que no incluya el nombre de la tabla)
db_url = f"postgresql://{os.getenv('DB_USER')}:Jennifer2004%2A@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?sslmode=require"
print(db_url)
db_url1 = "postgresql://postgres:kMefGeoDHCOvnbxXeyuaesTsnkMkxREi@shuttle.proxy.rlwy.net:43283/railway"

engine = create_engine(db_url)
