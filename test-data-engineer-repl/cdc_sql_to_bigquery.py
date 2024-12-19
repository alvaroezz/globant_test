import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import pyodbc
import pandas as pd
import os
import json

# Configuración de SQL Server
SQL_SERVER_HOST = os.getenv('SQL_SERVER_HOST', 'localhost')
SQL_SERVER_PORT = os.getenv('SQL_SERVER_PORT', '1433')
SQL_SERVER_USER = 'sa'
SQL_SERVER_PASSWORD = 'YourStrong@Passw0rd'
SQL_SERVER_DATABASE = 'YourDatabase'

# Configuración BigQuery
BQ_PROJECT = "the-delight-376003"
BQ_DATASET = "Desarrollo"
BQ_TABLE = "your_table"

def load_initial_data(root_folder):
    """
    Carga inicial de datos desde una estructura de carpetas y archivos CSV a SQL Server.
    """
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SQL_SERVER_HOST},{SQL_SERVER_PORT};"
        f"DATABASE={SQL_SERVER_DATABASE};"
        f"UID={SQL_SERVER_USER};"
        f"PWD={SQL_SERVER_PASSWORD}"
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Procesar carpeta central
    central_path = os.path.join(root_folder, 'central', 'CatLineasAreas.csv')
    if os.path.exists(central_path):
        print(f"Procesando catálogo: {central_path}")
        df = pd.read_csv(central_path)
        placeholders = ', '.join(['?'] * len(df.columns))
        for _, row in df.iterrows():
            cursor.execute(f"INSERT INTO dbo.CatLineasAreas VALUES ({placeholders})", tuple(row))
        conn.commit()
        print("Catálogo de líneas aéreas cargado correctamente.")

    # Procesar carpetas de sucursales
    for sucursal in ['sucursal1', 'sucursal2']:
        sucursal_path = os.path.join(root_folder, sucursal)
        if os.path.exists(sucursal_path):
            for file in os.listdir(sucursal_path):
                file_path = os.path.join(sucursal_path, file)
                if file == "pasajeros.csv":
                    table_name = "dbo.Pasajeros"
                elif file == "vuelos.csv":
                    table_name = "dbo.Vuelos"
                else:
                    print(f"Ignorando archivo desconocido: {file}")
                    continue

                print(f"Procesando archivo: {file_path} -> Tabla: {table_name}")
                df = pd.read_csv(file_path)
                placeholders = ', '.join(['?'] * len(df.columns))
                for _, row in df.iterrows():
                    cursor.execute(f"INSERT INTO {table_name} VALUES ({placeholders})", tuple(row))
                conn.commit()
                print(f"Datos de {file} cargados correctamente en {table_name}.")

    conn.close()
    print("Carga inicial completada.")

def enable_cdc():
    """
    Habilita CDC en SQL Server para las tablas relevantes.
    """
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SQL_SERVER_HOST},{SQL_SERVER_PORT};"
        f"DATABASE={SQL_SERVER_DATABASE};"
        f"UID={SQL_SERVER_USER};"
        f"PWD={SQL_SERVER_PASSWORD}"
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    cursor.execute("EXEC sys.sp_cdc_enable_db;")
    for table in ['CatLineasAreas', 'Pasajeros', 'Vuelos']:
        cursor.execute(f"""
            EXEC sys.sp_cdc_enable_table
            @source_schema = 'dbo',
            @source_name = '{table}',
            @role_name = NULL;
        """)
        print(f"CDC habilitado en la tabla {table}.")

    conn.commit()
    conn.close()

def fetch_cdc_changes():
    """
    Lee los cambios de CDC desde SQL Server para las tablas habilitadas.
    """
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SQL_SERVER_HOST},{SQL_SERVER_PORT};"
        f"DATABASE={SQL_SERVER_DATABASE};"
        f"UID={SQL_SERVER_USER};"
        f"PWD={SQL_SERVER_PASSWORD}"
    )
    conn = pyodbc.connect(conn_str)

    for table in ['dbo_CatLineasAreas_CT', 'dbo_Pasajeros_CT', 'dbo_Vuelos_CT']:
        query = f"SELECT * FROM cdc.{table}"
        df = pd.read_sql(query, conn)
        for _, row in df.iterrows():
            yield json.loads(row.to_json())

    conn.close()

class WriteToBigQuery(beam.DoFn):
    """
    Formatea y envía los datos a BigQuery.
    """
    def process(self, element):
        yield {
            "id": element.get("id"),
            "operation": element.get("__$operation"),
            "data": json.dumps(element)
        }

def run():
    # Configuración de las opciones de Dataflow
    options = PipelineOptions(
        project=BQ_PROJECT,
        region="multiregion",
        temp_location="gs://bucket/temp",
        staging_location="gs://bucket/staging",
        job_name="cdc-sqlserver-to-bigquery",
        runner="DataflowRunner"
    )

    # Carga inicial
    print("Cargando datos iniciales desde la estructura de carpetas...")
    load_initial_data("/app/data")

    # Habilitar CDC
    print("Habilitando CDC en SQL Server...")
    enable_cdc()

    # Pipeline de CDC
    print("Iniciando pipeline de CDC...")
    with beam.Pipeline(options=options) as p:
        (
            p
            | "Read CDC Changes" >> beam.Create(fetch_cdc_changes())
            | "Format for BigQuery" >> beam.ParDo(WriteToBigQuery())
            | "Write to BigQuery" >> beam.io.WriteToBigQuery(
                table=f"{BQ_PROJECT}:{BQ_DATASET}.{BQ_TABLE}",
                schema="id:STRING, operation:STRING, data:STRING",
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
            )
        )

if __name__ == "__main__":
    run()
