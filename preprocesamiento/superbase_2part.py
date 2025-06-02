import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from datetime import datetime  
import time 
import json
from supabase import create_client
from dotenv import load_dotenv
import os
load_dotenv()
local_katy = os.getenv('local_katy')
supabase_url = os.getenv('supabase_url')
supabase_key = os.getenv('supabase_key')
# Conexión a la base de datos local
engine = create_engine(f'postgresql+psycopg2://{local_katy}')

# Configuración de Supabase (asegúrate de tener las credenciales correctas)
supabase = create_client(supabase_url, supabase_key)

def leer_datos(tabla):
    return pd.read_sql(f"SELECT * FROM {tabla}", engine)

def limpiar_dataframe(df):
   
    # Reemplaza NaN, NaT y similares por None para mayor compatibilidad
    df = df.where(pd.notna(df), None)

    # Convertir correctamente según el tipo de datos
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].apply(lambda x: x.isoformat() if x else None)
        elif pd.api.types.is_bool_dtype(df[col]):
            df[col] = df[col].apply(lambda x: bool(x) if x is not None else None)
        elif pd.api.types.is_integer_dtype(df[col]):
            df[col] = df[col].astype('Int64')  # Uso de enteros nulos de pandas
        elif pd.api.types.is_float_dtype(df[col]):
            df[col] = df[col].astype(object).where(df[col].notna(), None)
        elif pd.api.types.is_object_dtype(df[col]):
            df[col] = df[col].apply(lambda x: str(x) if x is not None else None)
    return df

def migrar_tabla(tabla_origen, tabla_destino):
    print(f"Migrando datos de '{tabla_origen}' a '{tabla_destino}'...")
    try:
        df = leer_datos(tabla_origen)
        df = limpiar_dataframe(df)
        
        chunk_size = 1000
        total_registros = len(df)
        errores = []  # Lista para almacenar filas con errores
        
        for i in range(2102769, total_registros, chunk_size):
            chunk_df = df.iloc[i:i+chunk_size]
            
            for index, fila in chunk_df.iterrows():
                fila_dict = fila.to_dict()
                
                for intento in range(3):
                    try:
                        response = supabase.table(tabla_destino).insert(fila_dict).execute()
                        print(f"Fila {index} insertada exitosamente.")
                        break
                    except Exception as e:
                        print(f"Error en fila {index} (intento {intento+1}): {e}")
                        if intento == 2:  
                            errores.append({
                                "fila": fila_dict,
                                "error": str(e)
                            })
                            print(f"Fila {index} registrada como error.")
            
            print(f"Chunk {i} procesado. Errores registrados: {len(errores)}")
        
    except Exception as e:
        print(f"Error crítico en la migración: {e}")

# migrar_tabla("airlines", "airlines")
# migrar_tabla("airports", "airports")
migrar_tabla("flights", "flights")

engine.dispose()
# la cantidad por donde me quede en flights 2180679