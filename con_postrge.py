import psycopg2
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, time
from dotenv import load_dotenv
import os
load_dotenv()
password=os.getenv('password')
user=os.getenv('user')
# # Configuración de Supabase
# SUPABASE_URL = "https://supabase.com/dashboard/project/lxmcnjbmubtqmmctodja"
# SUPABASE_KEY = "Jennifer2004*"
# table_name = "nombre_tabla"  # Nombre de la tabla en Supabase

# # 1. Cargar datos locales (ejemplo con CSV o DataFrame)
# datos_locales = pd.read_csv("datos.csv")  # Ajusta según tu origen de datos

# # 2. Conectar a Supabase
# supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# # 3. Subir datos fila por fila
# for _, fila in datos_locales.iterrows():
#     data = fila.to_dict()  # Convierte cada fila a un diccionario
#     supabase.table(table_name).insert(data).execute()

# # Alternativa: Subir datos en lote (más eficiente)
# datos_lista = datos_locales.to_dict(orient="records")  # Convierte DataFrame a lista de dicts
# supabase.table(table_name).insert(datos_lista).execute()

# Conexión a la base de datos
conn = psycopg2.connect(
    dbname="fligth-database",
    user=user
    password=password,
    host="localhost",
    port="5432"
)

# Crear un cursor para ejecutar consultas
cur = conn.cursor()
print(" Iniciando borrado de migración de datos...")
cur.execute("""
    DROP TABLE IF EXISTS aircrafts;
    DROP TABLE IF EXISTS airports;
    DROP TABLE IF EXISTS flights;
    DROP TABLE IF EXISTS airlines
""")
print(" Iniciando script de migración de datos...")
cur.execute("""
CREATE TABLE IF NOT EXISTS airlines (
    airline_id INT PRIMARY KEY,
    unique_carrier VARCHAR(5)
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS airports (
    airport_id INT, --linea nueva 
    airport_seq_id INT,
    city_market_id INT,
    code VARCHAR(5),
    city_name VARCHAR(50),
    state_abr VARCHAR(5),
    state_fips VARCHAR(5),
    state_name VARCHAR(50),
    wac INT,
    PRIMARY KEY (airport_id, airport_seq_id)  -- Clave compuesta Linea nueva
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS flights (
    flight_id SERIAL PRIMARY KEY,
    fl_date DATE,
    op_unique_carrier VARCHAR(5),
    op_carrier_airline_id INT,
    op_carrier VARCHAR(5),
    tail_num VARCHAR(10),
    op_carrier_fl_num VARCHAR(10),
    origin_airport_id INT,
    dest_airport_id INT,
    crs_dep_time TIME,
    dep_time TIME,
    dep_delay FLOAT,
    wheels_off TIME,
    wheels_on TIME,
    crs_arr_time TIME,
    arr_time TIME,
    arr_delay FLOAT,
    cancelled BOOLEAN,
    diverted BOOLEAN,
    air_time FLOAT,
    distance FLOAT,
    flights FLOAT
);
""")
print(" Tablas creadas")
conn.commit()
print("Commit de tablas")
# 2. Cargar los datos existentes de la tabla `flight`
df = pd.read_sql_query("SELECT * FROM datos_vuelos", conn)
df.columns = df.columns.str.lower()


# 4. Insertar datos únicos en airlines

airlines = df[['op_unique_carrier', 'op_carrier_airline_id']].drop_duplicates()
print(" Insertando datos en airlines...")
total_rows=len(df)
for i, row in airlines.iterrows():
    cur.execute("""
        INSERT INTO airlines (airline_id, unique_carrier)
        VALUES (%s, %s)
        ON CONFLICT (airline_id) DO NOTHING;
    """, (row['op_carrier_airline_id'], row['op_unique_carrier']))
    if i % 10000 == 0:
        print(f" Procesando fila {i} de {total_rows} ({(i/total_rows)*100:.1f}%)")
print("Datos en flights insertados.")
# 5. Insertar datos únicos en airports

origin_airports = df[['origin_airport_id', 'origin_airport_seq_id', 'origin_city_market_id',
                      'origin', 'origin_city_name', 'origin_state_abr', 'origin_state_fips',
                      'origin_state_nm', 'origin_wac']].drop_duplicates()

dest_airports = df[['dest_airport_id', 'dest_airport_seq_id', 'dest_city_market_id',
                    'dest', 'dest_city_name', 'dest_state_abr', 'dest_state_fips',
                    'dest_state_nm', 'dest_wac']].drop_duplicates()

# Renombrar columnas para que coincidan
origin_airports.columns = ['airport_id', 'airport_seq_id', 'city_market_id',
                           'code', 'city_name', 'state_abr', 'state_fips',
                           'state_name', 'wac']

dest_airports.columns = origin_airports.columns

# Unir los aeropuertos origen y destino
airports = pd.concat([origin_airports, dest_airports]).drop_duplicates()
print("⏳ Insertando datos en airports...")

for i, row in airports.iterrows():
    cur.execute("""
        INSERT INTO airports (airport_id, airport_seq_id, city_market_id,
                               code, city_name, state_abr, state_fips,
                               state_name, wac)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (airport_id, airport_seq_id) DO NOTHING;  -- Clave compuesta completa;
    """, tuple(row))

    if i % 10000 == 0:
        print(f" Procesando fila {i} de {total_rows} ({(i/total_rows)*100:.1f}%)")
print(" Datos en flights insertados.")
# 6. Insertar los vuelos en flights

def convert_hhmm(time_val):
    try:
        if pd.isna(time_val) or time_val == '':
            return None
            
        # Convertir a entero primero
        time_num = int(float(time_val))
        
        # Manejar caso especial 2400
        if time_num == 2400:
            return time(23, 59, 59)
            
        # Validar rango
        if time_num < 0 or time_num > 2359:
            return None
            
        # Convertir a string con ceros a la izquierda
        time_str = f"{time_num:04d}"
        
        # Extraer horas y minutos
        hours = int(time_str[:2])
        minutes = int(time_str[2:])
        
        # Validar componentes
        if hours > 23 or minutes > 59:
            return None
            
        return time(hours, minutes, 0)
    except (ValueError, TypeError):
        return None
def parse_fl_date(date_val):
    """Versión robusta para manejar múltiples formatos de fecha"""
    if pd.isna(date_val):
        return None
        
    try:
        # Intentar convertir directamente con pandas (que maneja muchos formatos)
        parsed = pd.to_datetime(date_val, errors='coerce')
        if not pd.isna(parsed):
            return parsed.date()
            
        # Si falla, intentar manualmente con formatos específicos
        date_str = str(date_val).strip()
        
        # Formato yyyymmdd como número
        if date_str.isdigit() and len(date_str) == 8:
            return datetime.strptime(date_str, "%Y%m%d").date()
            
        # Otros formatos comunes
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
                
        return None
        
    except Exception as e:
        print(f"Error parsing date {date_val}: {str(e)}")
        return None
print(" Insertando datos en flights...")

for i, row in df.iterrows():
    # Convertir todos los campos
    fl_date = parse_fl_date(row['fl_date'])
    
    crs_dep_time = convert_hhmm(row['crs_dep_time'])
    dep_time = convert_hhmm(row['dep_time'])
    wheels_off = convert_hhmm(row['wheels_off'])
    wheels_on = convert_hhmm(row['wheels_on'])
    crs_arr_time = convert_hhmm(row['crs_arr_time'])
    arr_time = convert_hhmm(row['arr_time'])   
    
    cur.execute("""
    INSERT INTO flights (
        fl_date, op_unique_carrier, op_carrier_airline_id,
        op_carrier, tail_num, op_carrier_fl_num,
        origin_airport_id, dest_airport_id,
        crs_dep_time, dep_time, dep_delay, wheels_off,
        wheels_on, crs_arr_time, arr_time, arr_delay,
        cancelled, diverted, air_time,
        distance, flights
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s
    );
""", (
    fl_date,
    row['op_unique_carrier'],
    row['op_carrier_airline_id'],
    row['op_carrier'],
    row['tail_num'],
    row['op_carrier_fl_num'],
    row['origin_airport_id'],
    row['dest_airport_id'],
    crs_dep_time,
    dep_time,
    row['dep_delay'],
    wheels_off,
    wheels_on,
    crs_arr_time,
    arr_time,
    row['arr_delay'],
    bool(row['cancelled']) if not pd.isna(row['cancelled']) else False,
    bool(row['diverted']) if not pd.isna(row['diverted']) else False,
    row['air_time'],
    row['distance'],
    row['flights']
))
    if i % 10000 == 0:
        print(f" Procesando fila {i} de {total_rows} ({(i/total_rows)*100:.1f}%)")
print(" Datos en flights insertados.")

# Finalizar cambios
conn.commit()

# Cerrar conexión
cur.close()
conn.close()
