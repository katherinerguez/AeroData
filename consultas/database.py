from sqlalchemy import create_engine, text  # ✅ Importación faltante de 'text'

# Cadena de conexión (¡verifica que el nombre de la base de datos sea correcto!)
db_url = "postgresql://postgres:Jennifer2004*@localhost:5432/fligth-database"

# Función para obtener un motor de base de datos
def get_engine():
    return create_engine(db_url)

# ✅ Eliminamos la creación redundante del motor fuera de la función
engine = get_engine()  # ✅ Usamos la función para crear el motor

def get_db_url():
    return db_url

def execute_sql(query: str):
    """Ejecuta una consulta SQL y devuelve los resultados"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))  # ✅ Ahora 'text' está importado
            return result.fetchall()
    except Exception as e:
        # ✅ Manejo básico de errores
        print(f"Error ejecutando SQL: {e}")
        return []