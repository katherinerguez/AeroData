import psycopg2

DATABASE_URL = "postgresql://postgres:kMefGeoDHCOvnbxXeyuaesTsnkMkxREi@shuttle.proxy.rlwy.net:43283/railway"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS airlines (
    airline_id INT PRIMARY KEY,
    unique_carrier VARCHAR(5)
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS airports (
    airport_id INT,
    airport_seq_id INT,
    city_market_id INT,
    code VARCHAR(5),
    city_name VARCHAR(50),
    state_abr VARCHAR(5),
    state_fips VARCHAR(5),
    state_name VARCHAR(50),
    wac INT,
    PRIMARY KEY (airport_id, airport_seq_id)
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

conn.commit()
cur.close()
conn.close()
print("Tablas creadas en Railway correctamente.")
