import subprocess
import os

# === Configuración local ===
LOCAL_DB_NAME = "fligth-database"
LOCAL_DB_USER = "postgres"
TABLES = ["airports", "flights", "airlines"]  # Cambia por tus nombres reales
OUTPUT_FILE = "export_tablas.sql"

# === Configuración remota (Railway) ===
RAILWAY_DB_URL =  "postgresql://postgres:kMefGeoDHCOvnbxXeyuaesTsnkMkxREi@shuttle.proxy.rlwy.net:43283/railway"

def export_tables():
    """Exporta las 3 tablas desde PostgreSQL local"""
    tables_flags = " ".join([f"-t {table}" for table in TABLES])
    command = f'pg_dump -h localhost -U {LOCAL_DB_USER} -d {LOCAL_DB_NAME} {tables_flags} --data-only --no-owner --no-acl > {OUTPUT_FILE}'
    
    print("🚀 Exportando tablas desde PostgreSQL local...")
    subprocess.run(command, shell=True, check=True, executable="/bin/bash")
    print(f"✅ Exportación completada: {OUTPUT_FILE}")

def import_to_railway():
    """Importa los datos a la base de datos en Railway usando psql"""
    print("📡 Importando datos a Railway PostgreSQL...")
    command = f'psql "{RAILWAY_DB_URL}" -f {OUTPUT_FILE}'
    
    try:
        subprocess.run(command, shell=True, check=True, executable="/bin/bash")
        print("✅ Datos importados correctamente a Railway.")
    except subprocess.CalledProcessError as e:
        print("❌ Error al importar datos:", e)

if __name__ == "__main__":
    # Para evitar problemas con la contraseña, se usa PGPASSWORD o se configura auth
    os.environ["PGPASSWORD"] = input("🔑 Ingresa tu contraseña de PostgreSQL local: ")

    export_tables()
    import_to_railway()