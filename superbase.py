import pandas as pd
import psycopg2
from supabase import create_client
from sqlalchemy import create_engine
from datetime import datetime, time
import json
# Configuración de Supabase
supabase_url = 'https://lxmcnjbmubtqmmctodja.supabase.co'
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4bWNuamJtdWJ0cW1tY3RvZGphIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU1MTQ2NjUsImV4cCI6MjA2MTA5MDY2NX0.oxeZkWABTipAgcQ68wKqvvG17U8HfmduO-1udhfOyKs"
supabase = create_client(supabase_url, supabase_key)

# Conexión PostgreSQL local
engine = create_engine('postgresql+psycopg2://postgres:Jennifer2004*@localhost:5432/fligth-database')

def leer_datos(tabla):
    return pd.read_sql(f"SELECT * FROM {tabla}", engine)

def limpiar_dataframe(df):
    # Reemplaza NaN, NaT y similares por None
    df = df.applymap(lambda x: None if pd.isna(x) else x)

    # Convierte correctamente por tipo
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].apply(lambda x: x.isoformat() if x else None)
        elif pd.api.types.is_bool_dtype(df[col]):
            df[col] = df[col].apply(lambda x: bool(x) if x is not None else None)
        elif pd.api.types.is_integer_dtype(df[col]):
            df[col] = df[col].astype('Int64')  # pandas nullable int
        elif pd.api.types.is_float_dtype(df[col]):
            df[col] = df[col].astype(object).where(df[col].notna(), None)
        elif pd.api.types.is_object_dtype(df[col]):
            df[col] = df[col].apply(lambda x: str(x) if x is not None else None)
    return df



def migrar_tabla(tabla_postgres, tabla_supabase):
    print(f"⏳ Migrando tabla '{tabla_postgres}' a '{tabla_supabase}'...")
    try:
        df = leer_datos(tabla_postgres)
        df = limpiar_dataframe(df)
        data = df.to_dict(orient="records")

        for i in range(0, len(data), 1000):

            if i+1000< len(data):
                chunk = data[i:i+1000]
            else:
                chunk = data[i:len(data)]

            for intento in range(10):
                try:
                    print("Yes ", i)
                    response = supabase.table(tabla_supabase).upsert(chunk).execute()
                    break  # si funciona, salir del bucle de reintentos
                except Exception as e:
                    print(f"❌ Timeout o error en chunk {i}: {e}")
                    time.sleep(3)  # espera antes de reintentar
            else:
                print(f"❌ Chunk {i} falló tras 3 intentos.")

            response = supabase.table(tabla_supabase).upsert(chunk).execute()

        print(f"✅ Tabla '{tabla_supabase}' migrada exitosamente. Registros insertados: {len(data)}")

    except Exception as e:
        print(f"❌ Error al migrar '{tabla_supabase}': {e}")

# # Migrar tablas
# migrar_tabla("airlines", "airlines")
# migrar_tabla("airports", "airports")
migrar_tabla("flights", "flights")

engine.dispose()
