from confluent_kafka import Producer
import json
import requests
import time
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import os

load_dotenv()

# Configuración del productor
from kafka import KafkaProducer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    key_serializer=lambda k: k.encode('utf-8') if k else None
)

API_URL_STATE_VECTORS = os.getenv('API_URL_STATE_VECTORS')
API_URL_FLIGHTS = os.getenv('API_URL_FLIGHTS')

def fetch_data():
    try:
        timestamp = int(time.time())
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_states = executor.submit(requests.get, API_URL_STATE_VECTORS)
            future_flights = executor.submit(requests.get, API_URL_FLIGHTS, params={
                "begin": timestamp - 7200, 
                "end": timestamp
            })
            
            response_states = future_states.result()
            response_flights = future_flights.result()

            if response_states.status_code == 429 or response_flights.status_code == 429:
                print("[INFO] Límite de tasa excedido. Reintentando en 60 segundos...")
                time.sleep(60)
                return None, None

            if response_states.status_code == 200 and response_flights.status_code == 200:
                return response_states.json(), response_flights.json()
            else:
                print(f"[ERROR] Estados: {response_states.status_code}, Vuelos: {response_flights.status_code}")
                return None, None
                
    except Exception as e:
        print(f"[ERROR] Error en fetch_data: {str(e)}")
        return None, None

def send_to_kafka(states_data, flights_data, topic='flight-data-topic'):
    """Envía datos procesados a Kafka"""
    if not states_data or "states" not in states_data:
        print(f"[WARNING] Sin datos de estado para {topic}")
        return
    
    # Crear diccionario de vuelos por ICAO24
    flights_dict = {}
    if flights_data:
        for flight in flights_data:
            icao24 = flight.get("icao24")
            if icao24:
                flights_dict[icao24] = {
                    "firstSeen": flight.get("firstSeen"),
                    "lastSeen": flight.get("lastSeen"),
                    "estDepartureAirport": flight.get("estDepartureAirport"),
                    "estArrivalAirport": flight.get("estArrivalAirport")
                }

    # Procesar cada estado

    for state in states_data["states"]:
        if len(state) < 17:  
            continue
            
        icao24 = state[0]
        flight_info = flights_dict.get(icao24, {})
        
        # Construir la estructura 
        message = {
            "icao24": icao24,
            "callsign": state[1] or "",
            "origin_country": state[2],
            "position": {
                "timestamp": state[3],
                "last_contact": state[4],
                "longitude": state[5],
                "latitude": state[6]
            },
            "altitude": {
                "geo": state[7],
                "baro": state[13] if len(state) > 13 else None
            },
            "movement": {
                "velocity": state[9],
                "heading": state[10],
                "vertical_rate": state[11]
            }, 

            "flight_info": flight_info  # Datos de vuelo asociados

        }
        
        producer.send(
            topic=topic,
            value=message,  
            key=icao24  
        )
    
    producer.flush()
    print(f"[INFO] Enviados {len(states_data['states'])} mensajes a Kafka")

if __name__ == '__main__':
    while True:
        try:
            states, flights = fetch_data()
            if states:
                send_to_kafka(states, flights)
            time.sleep(10)  
        except KeyboardInterrupt:
            print("\nDeteniendo productor...")
            break
        except Exception as e:
            print(f"[CRITICAL] Error en loop principal: {str(e)}")
            time.sleep(30)  