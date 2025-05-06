import requests

# URL base de tu API
BASE_URL = "http://localhost:8002"

# ---------------- Obtener todos los vuelos ----------------
def obtener_vuelos():
    response = requests.get(f"{BASE_URL}/flights/")
    if response.status_code == 200:
        return response.json()
    else:
        print("Error al obtener vuelos:", response.status_code)

# ---------------- Obtener vuelos filtrados por aerolínea ----------------
def obtener_vuelos_por_aerolinea(airline_id):
    response = requests.get(f"{BASE_URL}/flights/?airline_id={airline_id}")
    if response.status_code == 200:
        return response.json()
    else:
        print("Error al filtrar vuelos:", response.status_code)

# ---------------- Obtener todos los aeropuertos ----------------
def obtener_aeropuertos():
    response = requests.get(f"{BASE_URL}/airports/")
    return response.json() if response.status_code == 200 else None

# ---------------- Obtener una aerolínea por ID ----------------
def obtener_aerolinea_por_id(airline_id):
    response = requests.get(f"{BASE_URL}/airlines/{airline_id}")
    return response.json() if response.status_code == 200 else None

# ---------------- Uso de las funciones ----------------
if __name__ == "__main__":
    print("🔍 Vuelos totales:")
    vuelos = obtener_vuelos()
    print(vuelos[:3])  # Solo los primeros 3 para mostrar

    print("\n🛫 Vuelos de aerolínea 20363:")
    vuelos_aerolinea = obtener_vuelos_por_aerolinea(20363)
    print(vuelos_aerolinea)

    print("\n🌍 Lista de aeropuertos:")
    aeropuertos = obtener_aeropuertos()
    for aeropuerto in aeropuertos[:3]:
        print(aeropuerto)
