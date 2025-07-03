import os
import json
from supabase import create_client, Client
from supabase.client import ClientOptions
from kafka import KafkaConsumer
from typing import Dict, Any
import logging
import time
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
# Configuración de Supabase
SUPABASE_URL = os.getenv("supabase_url_realtime")
SUPABASE_KEY = os.getenv("superbase_key_realtime")

# Inicialización del cliente Supabase con opciones personalizadas
# supabase: Client = create_client(
#     SUPABASE_URL,
#     SUPABASE_KEY,
#     options=ClientOptions(
#         postgrest_client_timeout=30,
#         storage_client_timeout=30,
#         schema='public'
#     )
# )
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
class FlightDataConsumer:
    def __init__(self, kafka_config: Dict[str, Any]):
        self.supabase = supabase
        self.consumer = KafkaConsumer(
            'flight-data-topic',  # Nombre del topic
            bootstrap_servers=kafka_config.get('bootstrap_servers', ['localhost:9092']),
            group_id='flight-data-consumer-group',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True,
            max_poll_records=100
        )
        self.logger = logging.getLogger(__name__)
    
    def process_flight_data(self, flight_data: Dict[str, Any]) -> bool:
        """
        Procesa y almacena los datos de vuelo en Supabase
        """
        try:
            # Validación de datos requeridos (ajustada para campos anidados)
            position = flight_data.get("position", {})
            
            if not flight_data.get("icao24") or not position.get("last_contact"):
                self.logger.warning(f"Datos incompletos recibidos: {flight_data}")
                return False

            # Preparación de datos para inserción (accede a campos anidados)
            processed_data = {
                "icao24": flight_data.get("icao24"),
                "origin_country": flight_data.get("origin_country"),
                "time_position": position.get("timestamp"),  # Acceso anidado
                "last_contact": position.get("last_contact"),  # Acceso anidado
                "latitude": position.get("latitude"),  # Acceso anidado
                "longitude": position.get("longitude"),  # Acceso anidado
                "altitude": flight_data.get("altitude", {}),  # Incluye ambos valores (geo y baro)
                "velocity": flight_data.get("movement", {}).get("velocity"),  # Acceso anidado
                "vertical_rate": flight_data.get("movement", {}).get("vertical_rate"),  # Acceso anidado
                "first_seen": flight_data.get("flight_info", {}).get("firstSeen"),  # Desde flight_info
                "last_seen": flight_data.get("flight_info", {}).get("lastSeen"),  # Desde flight_info
                "est_arrival_airport": flight_data.get("flight_info", {}).get("estArrivalAirport")  # Desde flight_info
            }
            print("datos procesados",processed_data)
            # Inserción en Supabase
            response = self.supabase.table("current_flight").insert(processed_data).execute()
            
            if response.data:
                self.logger.info(f"Datos insertados exitosamente para ICAO24: {flight_data.get('icao24')}")
                return True
            else:
                self.logger.error(f"Error al insertar datos: {response}")
                return False
        except Exception as e:
            self.logger.error(f"Error procesando datos de vuelo: {str(e)}")
            return False
    def start_consuming(self, batch_size: int = 50, batch_timeout: int = 5):
        """
        Inicia el consumo de mensajes con procesamiento por lotes
        """
        batch = []
        last_batch_time = time.time()
        
        self.logger.info("Iniciando consumer de datos de vuelos...")
        
        try:
            for message in self.consumer:
                try:
                    flight_data = message.value
                    batch.append(flight_data)
                    
                    # Procesar lote cuando se alcanza el tamaño objetivo o timeout
                    current_time = time.time()
                    should_process = (
                        len(batch) >= batch_size or 
                        (current_time - last_batch_time) >= batch_timeout
                    )
                    
                    if should_process and batch:
                        self.process_batch(batch)
                        batch = []
                        last_batch_time = current_time
                        
                except json.JSONDecodeError:
                    self.logger.error(f"Error decodificando mensaje: {message.value}")
                except Exception as e:
                    self.logger.error(f"Error procesando mensaje: {str(e)}")
                    
        except KeyboardInterrupt:
            self.logger.info("Consumer detenido por usuario")
        finally:
            self.consumer.close()
    
    def process_batch(self, batch: List[Dict[str, Any]]) -> None:
        """
        Procesa un lote de datos de vuelos
        """

        processed_batch = []
        
#         for flight_data in batch:
#             if self.validate_flight_data(flight_data):
#                 required_fields = ['icao24', 'position.last_contact']  # Ejemplo simplificado
# # O directamente:
#             if not flight_data.get('position', {}).get('last_contact'):
#                 processed_data = self.transform_flight_data(flight_data)
#                 processed_batch.append(processed_data)

        for i, flight_data in enumerate(batch):

            # Verificar last_contact
            last_contact = flight_data.get('position', {}).get('last_contact')

            if last_contact is None:
                continue

            # Validar datos
            valid = self.validate_flight_data(flight_data)

            if valid:
                processed_data = self.transform_flight_data(flight_data)
                processed_batch.append(processed_data)

        if processed_batch:
            try:
                response = self.supabase.table('current flights').insert(processed_batch).execute()
                print(1111111111111111111111111111111111111)
                if response:   
                    self.logger.info(f"Lote de {len(processed_batch)} registros insertado exitosamente")
            except Exception as e:
                self.logger.error(f"Error insertando lote: {str(e)}")
                
    def validate_flight_data(self, flight_data: Dict[str, Any]) -> bool:
        """
        Valida la estructura y contenido de los datos de vuelo
        """
        position = flight_data.get("position", {})

        # Campos requeridos: nombres de las claves, no sus valores
        required_fields = ['icao24']
        position_required_fields = ['last_contact']

        # Verificar campos requeridos en el nivel principal
        for field in required_fields:
            if field not in flight_data or flight_data[field] is None:
                return False

        # Verificar campos requeridos dentro de 'position'
        for field in position_required_fields:
            if field not in position or position[field] is None:
                return False
        
        # position = flight_data.get("position", {})

        # last_contact= position.get("last_contact") 
        # required_fields = ['icao24', last_contact]

        # Verificar campos requeridos
        # for field in required_fields:
        #     if field==last_contact:
        #         if field not in position or position[field] is None:
        #             return False
        #     if field not in flight_data or flight_data[field] is None:
        #         return False
        # print(2)
        # # Validar rangos de coordenadas geográficas
        # if position.get('latitude'):
        #     if not (-90 <= float(flight_data['latitude']) <= 90):
        #         return False
        # print(3) 
        # if position.get('longitude'):
        #     if not (-180 <= float(flight_data['longitude']) <= 180):
        #         return False
        # print(4)
        # # Validar altitud razonable
        # if flight_data.get('altitude'):
        #     if not (-1000 <= float(flight_data['altitude']) <= 50000):
        #         return False
                
        return True
    def safe_int_conversion(self, value):
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None

    def safe_float_conversion(self, value):
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None
    
    def transform_flight_data(self, flight_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma los datos de vuelo al formato requerido por la base de datos
        """
        return {
            'icao24': str(flight_data.get('icao24', '')).upper(),
            'origin_country': flight_data.get('origin_country'),
            'time_position': flight_data.get('position', {}).get('timestamp'),
            'last_contact': flight_data.get('position', {}).get('last_contact'),
            'latitude': flight_data.get('position', {}).get('latitude'),
            'longitude': flight_data.get('position', {}).get('longitude') ,
            'altitude': self.safe_float_conversion(flight_data.get('altitude')),
            'velocity': self.safe_float_conversion(flight_data.get('velocity')),
            'vertical_rate': self.safe_float_conversion(flight_data.get('vertical_rate')),
            'first_seen': self.safe_int_conversion(flight_data.get('firstSeen')),
            'last_seen': self.safe_int_conversion(flight_data.get('lastSeen')),
            'est_arrival_airport': flight_data.get('estArrivalAirport')
        }

def setup_logging():
    """
    Configura el sistema de logging para el consumer
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('flight_consumer.log'),
            logging.StreamHandler()
        ]
    )

# Punto de entrada principal
if __name__ == "__main__":
    setup_logging()
    print(111111111111111111111111111111111111111111111)
    kafka_config = {
        'bootstrap_servers': ['localhost:9092'],
        'group_id': 'flight-data-consumer'
    }
    
    consumer = FlightDataConsumer(kafka_config)
    consumer.start_consuming(batch_size=100, batch_timeout=10)
