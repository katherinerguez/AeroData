# AeroData
# Ingeniería de Datos
Este proyecto consiste en un análisis sobre los aeropuertos, donde se tendrá en cuenta datos sobre los vuelos, los aviones, las aerolíneas y los aeropuertos.

>>**Resumen:** Para observar una información sobre los datos históricos sobre el transporte aéreo de Los Estados Unidos, este proyecto presenta una página web donde se desplegan análisis que pueden ser de interés. Además de una API donde se puede extraer esta información que utilizamos para su uso personal o si presenta algún conocimiento sobre sql, puede hacer directamente las consultas a la base de datos.


## 1. Requerimientos de software
        Python  
        jinja2
        fastapi 
        uvicorn
        sqlalchemy
        supabase
        pandas
        psycopg2
        plotly
        dask
        pydantic

## 2. Ingesta
La información sobre el transporte aéreo lo obtuvimos en la página del Departamento de Transportación de los Estados Unidos.
        https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr

## 3. Preprocesamieento
La base de datos se creó en postgres, sacando las entidades y sus relaciones. Se realizó todo un proceso de limpieza de los datos, para convertirlos en un formato adecuado para su utilización así como la toma de decisiones respecto a algunas columnas que se encuentran disponibles en ls información obtenido pero que presentaban datos redundantes o muchos valores faltantes.

## 4. Interfaz Visual
  Para la interfaz visual se presenta una página web, realizada con Fast API, donde se muestran los análisis respecto a los aeropuertos. Además en otro puerto se presenta la API que nos brinda los datos a través de request y tambiénn se encuentra para realizar consultas directas a la base de datos.
  Todos estos archivos se encuentran disponibles en la carpeta llamada app, para ejecutar los acrhivos se encuentra el archivo run, con el cual se levantan todos los procesos de manera automática. Para ejecutar este archivo se ejecuta el siguiente comando en la consola, ./run.sh

