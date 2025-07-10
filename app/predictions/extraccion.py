from sqlalchemy import create_engine, MetaData, Table
import os
import pandas as pd
from datetime import datetime,timedelta
from dotenv import load_dotenv
import requests
from geopy.distance import geodesic
from sqlalchemy import create_engine, MetaData, Table, insert
from sqlalchemy.orm import sessionmaker, declarative_base
import pandas as pd
import os
from dotenv import load_dotenv
from catboost import CatBoostRegressor, Pool

load_dotenv()

user=os.getenv('user')
password=os.getenv('password')
host=os.getenv('host')
port=os.getenv('port')
dbname=os.getenv('dbname')
DB_URL = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

API_KEY = os.getenv("API_KEY")
current_id = 1039705

MODEL_PATH = 'flight_delay_model.cbm'
model_features = [
    "op_unique_carrier","op_carrier","origin_airport_id","dest_airport_id",
    "distance","op_carrier_fl_num","day_of_week","month","is_weekend",
    "scheduled_duration","dep_hour","dep_minute","arr_hour"
]
# crear motor y sesión
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

iata_to_id_dict = {'BHM': 10599, 'LGA': 12953, 'ATL': 10397, 'MOB': 13422, 'HSV': 12217, 'IAH': 12266, 'DFW': 11298, 'ORD': 13930, 'MGM': 13277, 'MIA': 13303, 'DCA': 11278, 'CLT': 11057, 'PHL': 14100, 'DEN': 11292, 'DHN': 11308, 'DTW': 11433, 'MDW': 13232, 'FLL': 11697, 'DAL': 11259, 'TPA': 15304, 'MCO': 13204, 'BWI': 10821, 'HOU': 12191, 'LAS': 12889, 'IAD': 12264, 'BFM': 10562, 'XNA': 15919, 'MSP': 13487, 'CLL': 11049, 'PHX': 14107, 'BNA': 10693, 'OKC': 13851, 'BTR': 10781, 'IND': 12339, 'MCI': 13198, 'AUS': 10423, 'CAE': 10868, 'MSN': 13485, 'MKE': 13342, 'LAX': 12892, 'Atlanta, GA': 1039705, 'Oakland, CA': 1379603, 'Detroit, MI': 1143302, 'Kansas City, MO': 1319801, 'Las Vegas, NV': 1288903, 'San Francisco, CA': 1477102, 'New York, NY': 1247803, 'Minneapolis, MN': 1348702, 'Los Angeles, CA': 1289203, 'Newark, NJ': 1161802, 'Milwaukee, WI': 1334205, 'Chicago, IL': 1393004, 'Washington, DC': 1127803, 'Baltimore, MD': 1082103, 'Orlando, FL': 1320402, 'Cleveland, OH': 1104203, 'St. Louis, MO': 1501603, 'Columbus, GA': 1115003, 'Fort Wayne, IN': 1182304, 'Green Bay, WI': 1197702, 'Wilmington, DE': 1232002, 'Phoenix, AZ': 1410702, 'Dallas/Fort Worth, TX': 1129804, 'Charlotte, NC': 1105703, 'Philadelphia, PA': 1410002, 'Denver, CO': 1129202, 'Pittsburgh, PA': 1412202, 'Raleigh/Durham, NC': 1449202, 'Albuquerque, NM': 1014003, 'Charleston, SC': 1099402, 'Dayton, OH': 1126702, 'Tulsa, OK': 1537002, 'Jacksonville, FL': 1245102, 'San Antonio, TX': 1468303, 'Bakersfield, CA': 1056103, 'Salt Lake City, UT': 1486903, 'Portland, OR': 1405702, 'Honolulu, HI': 1217302, 'Houston, TX': 1219102, 'Miami, FL': 1330303, 'Hartford, CT': 1052904, 'Charleston/Dunbar, WV': 1114603, 'Little Rock, AR': 1299204, 'Mammoth Lakes, CA': 1338801, 'Lexington, KY': 1294503, 'Charlotte Amalie, VI': 1502403, 'Atlantic City, NJ': 1015804, 'Fort Lauderdale, FL': 1169704, 'North Bend/Coos Bay, OR': 1396403, 'Des Moines, IA': 1142303, 'Jackson/Vicksburg, MS': 1244805, 'Myrtle Beach, SC': 1357702, 'Fairbanks, AK': 1163002, 'Seattle, WA': 1474703, 'Cincinnati, OH': 1119302, 'Tampa, FL': 1530402, 'Sarasota/Bradenton, FL': 1498603, 'Oklahoma City, OK': 1385103, 'Lake Charles, LA': 1291503, 'Corpus Christi, TX': 1114005, 'Norfolk, VA': 1393102, 'Omaha, NE': 1387102, 'Birmingham, AL': 1059904, 'Grand Rapids, MI': 1198603, 'Columbus, OH': 1106603, 'Syracuse, NY': 1509602, 'Cedar Rapids/Iowa City, IA': 1100303, 'Wichita, KS': 1227803, 'Providence, RI': 1430702, 'Fort Myers, FL': 1463502, 'Boston, MA': 1072102, 'West Palm Beach/Palm Beach, FL': 1402702, 'Columbia, SC': 1086803, 'Asheville, NC': 1043103, 'Indianapolis, IN': 1233904, 'Savannah, GA': 1468502, 'Greer, SC': 1199603, 'Dallas, TX': 1125903, 'Huntsville, AL': 1221702, 'Richmond, VA': 1452401, 'Memphis, TN': 1324402, 'Newport News/Williamsburg, VA': 1409803, 'Sioux Falls, SD': 1177502, 'Harrisburg, PA': 1323002, 'Lafayette, LA': 1295104, 'Shreveport, LA': 1481402, 'Montgomery, AL': 1327702, 'Manchester, NH': 1329604, 'Springfield, MO': 1478302, 'Knoxville, TN': 1541203, 'Augusta, GA': 1020803, 'Buffalo, NY': 1079204, 'Peoria, IL': 1410803, 'Greensboro/High Point, NC': 1199502, 'Montrose/Delta, CO': 1350202, 'Nashville, TN': 1069302, 'Durango, CO': 1141304, 'Amarillo, TX': 1027903, 'Mosinee, WI': 1120302, 'Fargo, ND': 1163703, 'Trenton, NJ': 1535602, 'Grand Junction, CO': 1192102, 'Madison, WI': 1348502, 'San Diego, CA': 1467903, 'New Orleans, LA': 1349503, 'Akron, OH': 1087402, 'Kahului, HI': 1383002, 'Mobile, AL': 1342202, 'Dubuque, IA': 1127402, 'San Angelo, TX': 1484202, 'Boise, ID': 1071302, 'Rochester, NY': 1457604, 'Spokane, WA': 1188402, 'San Jose, CA': 1483103, 'Burbank, CA': 1080003, 'El Paso, TX': 1154003, 'Ontario, CA': 1389101, 'Reno, NV': 1457002, 'Santa Ana, CA': 1490803, 'Austin, TX': 1042302, 'Albany, NY': 1025702, 'Long Beach, CA': 1295402, 'Louisville, KY': 1473003, 'Sacramento, CA': 1489302, 'Killeen, TX': 1198202, 'Fresno, CA': 1163805, 'Yuma, AZ': 1621801, 'Tucson, AZ': 1537602, 'Palm Springs, CA': 1426204, 'Jackson, WY': 1244102, 'Appleton, WI': 1040803, 'Eugene, OR': 1160302, 'Helena, MT': 1215603, 'Sun Valley/Hailey/Ketchum, ID': 1504102, 'Williston, ND': 1238902, 'Midland/Odessa, TX': 1315802, 'San Luis Obispo, CA': 1469802, 'Springfield, IL': 1495203, 'Monterey, CA': 1347603, 'Aspen, CO': 1037203, 'Bozeman, MT': 1084903, 'Waco, TX': 1015502, 'Colorado Springs, CO': 1110902, 'Santa Barbara, CA': 1468902, 'Arcata/Eureka, CA': 1015703, 'Anchorage, AK': 1029904, 'Billings, MT': 1062002, 'Roanoke, VA': 1457403, 'San Juan, PR': 1484304, 'Panama City, FL': 1148102, 'Valparaiso, FL': 1562402, 'White Plains, NY': 1219702, 'Burlington, VT': 1078502, 'Missoula, MT': 1348602, 'Pensacola, FL': 1419303, 'Lubbock, TX': 1289605, 'Hilo, HI': 1240203, 'Idaho Falls, ID': 1228002, 'Pellston, MI': 1415002, 'Medford, OR': 1326403, 'Rapid City, SD': 1445702, 'Duluth, MN': 1133703, 'Aguadilla, PR': 1073203, 'Kona, HI': 1275803, 'Baton Rouge, LA': 1078103, 'South Bend, IN': 1469605, 'Kalamazoo, MI': 1046902, 'Key West, FL': 1162402, 'Scranton/Wilkes-Barre, PA': 1043403, 'Lihue, HI': 1298202, 'Joplin, MO': 1251102, 'Tallahassee, FL': 1524904, 'Melbourne, FL': 1336003, 'Fayetteville, AR': 1591902, 'Sault Ste. Marie, MI': 1101303, 'Elko, NV': 1152503, 'Daytona Beach, FL': 1125203, 'Valdosta, GA': 1560702, 'Portland, ME': 1432103, 'Carlsbad, CA': 1104103, 'Bristol/Johnson City/Kingsport, TN': 1532302, 'Gillette, WY': 1186502, 'Crescent City, CA': 1093002, 'Great Falls, MT': 1200302, 'Brainerd, MN': 1073905, 'Hobbs, NM': 1217703, 'Gulfport/Biloxi, MS': 1197302, 'Mission/McAllen/Edinburg, TX': 1325602, 'Gainesville, FL': 1195302, 'Charlottesville, VA': 1099002, 'Hayden, CO': 1209402, 'St. Augustine, FL': 1549703, 'Manhattan/Ft. Riley, KS': 1329002, 'Minot, ND': 1343302, 'Chattanooga, TN': 1098002, 'Wilmington, NC': 1232303, 'Dothan, AL': 1130802, 'Casper, WY': 1112203, 'Muskegon, MI': 1334402, 'Bend/Redmond, OR': 1448902, 'Branson, MO': 1064301, 'Harlingen/San Benito, TX': 1220603, 'Lansing, MI': 1288403, 'Flint, MI': 1172103, 'Texarkana, AR': 1540103, 'Pasco/Kennewick/Richland, WA': 1425202, 'Modesto, CA': 1342402, 'Twin Falls, ID': 1538902, 'Nantucket, MA': 1015403, 'Pocatello, ID': 1411302, 'Redding, CA': 1448702, 'Tyler, TX': 1541103, 'Elmira/Corning, NY': 1153703, 'College Station/Bryan, TX': 1104902, 'Monroe, LA': 1337702, 'Traverse City, MI': 1538003, 'Grand Forks, ND': 1189802, 'Rock Springs, WY': 1454302, 'Jacksonville/Camp Lejeune, NC': 1379502, 'Dickinson, ND': 1131502, 'Fayetteville, NC': 1164102, 'Plattsburgh, NY': 1402501, 'Erie, PA': 1157704, 'Albany, GA': 1014602, 'Allentown/Bethlehem/Easton, PA': 1013503, 'Adak Island, AK': 1016502, 'Worcester, MA': 1393303, 'Santa Fe, NM': 1467402, 'Binghamton, NY': 1057703, 'Bloomington/Normal, IL': 1068502, 'Brunswick, GA': 1073103, 'State College, PA': 1471102, 'Moline, IL': 1336703, 'Rochester, MN': 1463303, 'Devils Lake, ND': 1144703, 'Eau Claire, WI': 1147103, 'International Falls, MN': 1234302, 'Kotzebue, AK': 1397002, 'Brownsville, TX': 1074702, 'Alexandria, LA': 1018502, 'Lincoln, NE': 1302902, 'Sioux City, IA': 1504803, 'Abilene, TX': 1013603, 'La Crosse, WI': 1307602, 'Newburgh/Poughkeepsie, NY': 1507002, 'Columbia, MO': 1111102, 'St. George, UT': 1479402, 'Fort Smith, AR': 1177801, 'Wichita Falls, TX': 1496002, 'Meridian, MS': 1324102, 'Saginaw/Bay City/Midland, MI': 1318403, 'Paducah, KY': 1400602, 'Ithaca/Cortland, NY': 1239702, 'Pago Pago, TT': 1422204, 'Garden City, KS': 1186703, 'Evansville, IN': 1161204, 'Bismarck/Mandan, ND': 1062702, 'Kalispell, MT': 1164802, 'Flagstaff, AZ': 1169502, 'Pueblo, CO': 1428803, 'Hancock/Houghton, MI': 1107602, 'Butte, MT': 1077902, 'Hattiesburg/Laurel, MS': 1410902, 'Hibbing, MN': 1212903, 'Watertown, NY': 1036102, 'Sitka, AK': 1482802, 'Chico, CA': 1100202, 'Laredo, TX': 1306104, 'Aberdeen, SD': 1014102, 'Latrobe, PA': 1289803, 'Christiansted, VI': 1502704, 'Jamestown, ND': 1251902, 'Ponce, PR': 1425403, 'Juneau, AK': 1252304, 'Beaumont/Port Arthur, TX': 1072804, 'New Bern/Morehead/Beaufort, NC': 1161706, 'Bangor, ME': 1058102, 'Grand Island, NE': 1198002, 'Alpena, MI': 1033302, 'Rhinelander, WI': 1452002, 'Vernal, UT': 1558202, 'Columbus, MS': 1200702, 'Champaign/Urbana, IL': 1106702, 'Nome, AK': 1387303, 'Bellingham, WA': 1066602, 'Lawton/Fort Sill, OK': 1289102, 'Hays, KS': 1225502, 'St. Cloud, MN': 1500802, 'Islip, NY': 1239102, 'Santa Maria, CA': 1490503, 'Bethel, AK': 1055102, 'Dillingham, AK': 1133602, 'Lewiston, ID': 1312702, 'Topeka, KS': 1172602, 'Gunnison, CO': 1201203, 'Marquette, MI': 1345902, 'Klamath Falls, OR': 1302402, 'Deadhorse, AK': 1470903, 'Ketchikan, AK': 1281902, 'Petersburg, AK': 1425603, 'Waterloo, IA': 1026802, 'Longview, TX': 1190502, 'Barrow, AK': 1075402, 'Bemidji, MN': 1063104, 'Yakutat, AK': 1599102, 'Cedar City, UT': 1091802, 'Eagle, CO': 1150303, 'Iron Mountain/Kingsfd, MI': 1233502, 'Toledo, OH': 1529502, 'Escanaba, MI': 1158702, 'Guam, TT': 1201602, 'Niagara Falls, NY': 1226503, 'Laramie, WY': 1288802, 'Cody, WY': 1109702, 'Moab, UT': 1109202, 'Gustavus, AK': 1199702, 'Roswell, NM': 1458801, 'Cordova, AK': 1092603, 'Wrangell, AK': 1584102, 'King Salmon, AK': 1024502, 'Hyannis, MA': 1225002, "Martha's Vineyard, MA": 1354102, 'Kodiak, AK': 1017001, 'West Yellowstone, MT': 1589702, 'Saipan, TT': 1495503, 'Macon, GA': 1320302}

def save_today_data(df):
    df = df.drop(columns=['op_unique_carrier'], errors='ignore')  # errors='ignore' evita error si no existe

    df.to_sql(
    name="real_time",
    con=engine,
    if_exists="append",
    index=False,
    method="multi"
)

def get_flights():
    df = check_today_data()
    if df is not None:
        print("✅ Datos cargados de Supabase")
        return df

    print("📡 No hay datos en Supabase, consultando API…")
    df = fetch_flights_from_api()
    df = transform_df(df)  
    df = predict_delays(df)  
    save_today_data(df)
    return df

def calc_duration(row):
    try:
        dep = datetime.strptime(row['scheduled_dep_time'], '%H:%M:%S')
        arr = datetime.strptime(row['scheduled_arr_time'], '%H:%M:%S')
        if arr < dep:
            arr += timedelta(days=1)  # cruza medianoche
        return (arr - dep).total_seconds() / 60
    except Exception:
        return None


def calc_distance(row, airport_coords):
    origin = airport_coords.get(row['origin_airport_id'])
    dest = airport_coords.get(row['dest_airport_id'])
    if origin and dest:
        return geodesic(origin, dest).miles
    return None

def fetch_all_airport_coords(api_key):
    base_url = f'https://api.aviationstack.com/v1/airports?access_key={api_key}'
    airport_coords = {}
    for offset in range(0, 10000, 1000):
        url = f'{base_url}&limit=1000&offset={offset}'
        response = requests.get(url)
        data = response.json()
        if data.get('data'):
            for airport in data['data']:
                iata = airport.get('iata_code')
                lat = airport.get('latitude')
                lon = airport.get('longitude')
                if iata and lat and lon:
                    airport_coords[iata] = (float(lat), float(lon))
        else:
            break
    print(f"✅ Coordenadas cargadas: {len(airport_coords)} aeropuertos")
    return airport_coords

from sqlalchemy import select

from datetime import datetime
from sqlalchemy import MetaData, select, and_
import pandas as pd

def check_today_data():
    """
    Filtra datos de la tabla 'real_time' para obtener solo los registros de hoy
    
    Args:
        engine: SQLAlchemy engine previamente creado
        
    Returns:
        DataFrame con los datos de hoy o None si no hay registros
    """
    try:
        # Obtener fecha actual en formato YYYY-MM-DD
        today = datetime.now().date()

        
        # Configurar metadata y reflejar la tabla
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        if "real_time" not in metadata.tables:
            print("Error: La tabla 'real_time' no existe en la base de datos")
            return None
            
        vuelos = metadata.tables["real_time"]
        
        # Crear consulta optimizada
        stmt = select(vuelos).where(vuelos.c.flight_date == today)
        
        # Ejecutar consulta y obtener resultados
        with engine.connect() as conn:
            result = conn.execute(stmt)
            
            # Convertir directamente a DataFrame (más eficiente)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            
            return df if not df.empty else None
            
    except Exception as e:
        print(f"Error al obtener datos: {str(e)}")
        return None


def fetch_flights_from_api(hours_ahead=24, max_results=2000):
    base_url = "https://api.aviationstack.com/v1/flights"
    all_flights = []
    
    # Configuración básica de parámetros
    params = {
        'access_key': API_KEY,
        'flight_status': 'scheduled',
        'limit': 100  # Máximo permitido por request
    }
    
    # Si quieres vuelos para todo el día, no uses filtros temporales
    # Si prefieres un rango específico:
    if hours_ahead:
        now = datetime.utcnow()
        time_limit = now + timedelta(hours=hours_ahead)
        params.update({
            'dep_estimated_from': now.strftime('%Y-%m-%dT%H:%M:%S'),
            'dep_estimated_to': time_limit.strftime('%Y-%m-%dT%H:%M:%S')
        })
    
    # Implementación de paginación
    offset = 0
    while len(all_flights) < max_results:
        params['offset'] = offset
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        raw_data = response.json()
        
        if not raw_data.get("data"):
            break
            
        all_flights.extend(raw_data["data"])
        offset += len(raw_data["data"])
        
        # Si obtenemos menos resultados que el límite, es el final
        if len(raw_data["data"]) < params['limit']:
            break
    
    return pd.DataFrame(all_flights)

def get_or_create_airport_id(iata_code,airport_coords):
    global current_id
    if pd.isna(iata_code) or iata_code not in airport_coords:
        return None
    
    if iata_code in iata_to_id_dict:
        return iata_to_id_dict[iata_code]
    else:
        current_id += 1
        iata_to_id_dict[iata_code] = str(current_id)
        return str(current_id)
def transform_df(df):
    # Extraer datos básicos
    df['op_carrier'] = df['airline'].apply(lambda x: x.get('iata') if isinstance(x, dict) else None)
    df['op_carrier_fl_num'] = df['flight'].apply(lambda x: x.get('number') if isinstance(x, dict) else None)
    
    # Aeropuertos de origen y destino
    df['origin_airport_id'] = df['departure'].apply(lambda x: x.get('iata') if isinstance(x, dict) else None)
    df['dest_airport_id'] = df['arrival'].apply(lambda x: x.get('iata') if isinstance(x, dict) else None)
    
    # NOMBRES DE LOS AEROPUERTOS (lo que quieres)
    df['departure_airport_name'] = df['departure'].apply(lambda x: x.get('airport') if isinstance(x, dict) else None)
    df['arrival_airport_name'] = df['arrival'].apply(lambda x: x.get('airport') if isinstance(x, dict) else None)
    
    df['airline_name'] = df['airline'].apply(lambda x: x.get('name') if isinstance(x, dict) else None)

    # Fechas programadas
    df['scheduled_dep'] = pd.to_datetime(
        df['departure'].apply(lambda x: x.get('scheduled') if isinstance(x, dict) else None),
        errors='coerce'
    ).dt.strftime("%Y-%m-%d %H:%M:%S")
    df['scheduled_arr'] = pd.to_datetime(
        df['arrival'].apply(lambda x: x.get('scheduled') if isinstance(x, dict) else None),
        errors='coerce'
    ).dt.strftime("%Y-%m-%d %H:%M:%S")
    # Verificar si hay horas mayores a 12 (formato 24h)

    df['scheduled_dep_time'] = pd.to_datetime(df['scheduled_dep']).dt.strftime('%H:%M:%S')
    df['scheduled_arr_time'] = pd.to_datetime(df['scheduled_arr']).dt.strftime('%H:%M:%S')


    df['dep_hour'] = df['scheduled_dep_time'].apply(lambda x: int(x.split(':')[0]) if pd.notnull(x) else None)
    df['dep_minute'] = df['scheduled_dep_time'].apply(lambda x: int(x.split(':')[1]) if pd.notnull(x) else None)
    df['arr_hour'] = df['scheduled_arr_time'].apply(lambda x: int(x.split(':')[0]) if pd.notnull(x) else None)

    df['day_of_week'] = datetime.today().weekday()
    df['month'] = datetime.today().month
    df['is_weekend'] = df['day_of_week'].isin([5,6]).astype(int)

    df['scheduled_duration'] = df.apply(calc_duration, axis=1)

    airport_coords = fetch_all_airport_coords(API_KEY)
    df['distance'] = df.apply(lambda row: calc_distance(row, airport_coords), axis=1)
    
    df['op_unique_carrier'] = df['op_carrier']

    df['origin_airport_id'] = df['origin_airport_id'].apply(lambda x: get_or_create_airport_id(x, airport_coords))
    df['dest_airport_id']   = df['dest_airport_id'].apply(lambda x: get_or_create_airport_id(x, airport_coords))

    
    # Eliminar columnas anidadas si ya no se necesitan
    df.drop(columns=['departure', 'arrival',"live","aircraft","airline","flight"], inplace=True, errors='ignore')

    return df
def predict_delays(df):
    model = CatBoostRegressor()
    model.load_model(MODEL_PATH)

    features = df[model_features].copy()
    features = features.dropna()  # opcional: evita filas incompletas

    prediction_pool = Pool(
        data=features,
        cat_features=[
            "op_unique_carrier","op_carrier","op_carrier_fl_num",
            "origin_airport_id","dest_airport_id","day_of_week","month","dep_hour","arr_hour"
        ]
    )

    predictions = model.predict(prediction_pool)
    df.loc[features.index, 'predicted_delay'] = predictions
    return df
    