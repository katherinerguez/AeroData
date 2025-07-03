import requests

API_KEY = "95af12dc-b1a6-4600-8e4d-5d8458529df1" # Reemplaza con tu API Key, esta  es una api de ejemplo
headers = {
    "X-API-Key": API_KEY
}
# URL base de tu API
BASE_URL = "https://aerodata.onrender.com/api"
# BASE_URL="http://127.0.0.1:8000" url local
# ---------------- Obtener todos los vuelos ----------------


def obtener_todos_vuelos(lote_size=50):
    """Obtiene todos los vuelos en lotes"""
    page = 1
    todos_vuelos = []
    
    while True:
        params = {
            "page": page,
            "page_size": lote_size
        }
        response = requests.get(f"{BASE_URL}/flights/", params=params, headers=headers)
        
        if response.status_code != 200:
            print(f"Error al obtener vuelos (página {page}):", response.status_code)
            break
            
        vuelos = response.json()
        if not vuelos:
            break
            
        todos_vuelos.extend(vuelos)
        print(vuelos)
        print(f"Obtenidos {len(vuelos)} vuelos (página {page})")
        page += 1
    
    return todos_vuelos
# ---------------- Obtener todas las aereolineas ----------------

def obtener_todas_aerolineas(lote_size=50):
    """Obtiene todas las aerolíneas en lotes"""
    page = 1
    todas_aerolineas = []
    
    while True:
        params = {
            "page": page,
            "page_size": lote_size
        }
        response = requests.get(f"{BASE_URL}/airlines/", params=params, headers=headers)
        
        if response.status_code != 200:
            print(f"Error al obtener aerolíneas (página {page}):", response.status_code)
            break
            
        aerolineas = response.json()
        if not aerolineas:
            break
            
        todas_aerolineas.extend(aerolineas)
        print(aerolineas)
        print(f"Obtenidas {len(aerolineas)} aerolíneas (página {page})")
        page += 1
    
    return todas_aerolineas

# # ---------------- Obtener vuelos filtrados por aerolínea ----------------

def obtener_vuelos_por_aerolinea(airline_id, lote_size=50):
    """Obtiene vuelos por aerolínea en lotes"""
    page = 1
    todos_vuelos = []
    
    while True:
        params = {
            "airline_id": airline_id,
            "page": page,
            "page_size": lote_size
        }
        response = requests.get(f"{BASE_URL}/flights/", params=params, headers=headers)
        
        if response.status_code != 200:
            print(f"Error al filtrar vuelos (página {page}):", response.status_code)
            break
            
        vuelos = response.json()
        if not vuelos:
            break
            
        todos_vuelos.extend(vuelos)
        print(f"Obtenidos {len(vuelos)} vuelos de aerolínea {airline_id} (página {page})")
        page += 1
    
    return todos_vuelos

#  ---------------- Obtener todos los aeropuertos ----------------

def obtener_aeropuertos():
    response = requests.get(f"{BASE_URL}/airports/", headers=headers)
    try:
        if response.status_code == 200:
            return response.json()
        else:
            print("Error al obtener aeropuertos:", response.status_code, response.text)
            return None
    except requests.exceptions.JSONDecodeError:
        print("La respuesta no es JSON:", response.text)
        return None


def obtener_vuelos_csv(lote_size=50):
    """Obtiene vuelos en formato CSV como texto"""
    page = 1
    while True:
        params = {
            "page": page,
            "page_size": lote_size,
            "format": "csv"
        }
        response = requests.get(f"{BASE_URL}/flights/", params=params, headers=headers)
        
        if response.status_code != 200:
            print(f"Error al obtener CSV de vuelos (página {page}):", response.status_code)
            break
        
        csv_data = response.text
        print(f"\n📄 CSV de la página {page}:\n", csv_data[:300])  # Mostrar primeras líneas
        page += 1
        break  
    
if __name__ == "__main__":
    
    print("\n🌍 Obteniendo aeropuertos...")
    aeropuertos = obtener_aeropuertos()
    if aeropuertos:
        for aeropuerto in aeropuertos[:3]:
            print(aeropuerto)
    
    print("\n🛫 Obteniendo aerolíneas en lotes...")
    aerolineas = obtener_todas_aerolineas(lote_size=10)
    if aerolineas:
        print(f"Total de aerolíneas obtenidas: {len(aerolineas)}")
        for aerolinea in aerolineas[:3]:
            print(aerolinea)
    
    print("\n✈️ Obteniendo vuelos de aerolínea 20366 en lotes...")
    vuelos_aerolinea = obtener_vuelos_por_aerolinea(20366, lote_size=10)
    if vuelos_aerolinea:
        print(f"Total de vuelos obtenidos: {len(vuelos_aerolinea)}")
        for vuelo in vuelos_aerolinea[:3]:
            print(vuelo)
    
    print("\n🛩 Obteniendo todos los vuelos en lotes...")
    todos_vuelos = obtener_todos_vuelos(lote_size=10)
    if todos_vuelos:
        print(f"Total de vuelos obtenidos: {len(todos_vuelos)}")
        for vuelo in todos_vuelos[:3]:
            print(vuelo)
