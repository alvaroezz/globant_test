# Ejercicio práctico para Data Engineer Replication/Extraction en Deacero.

# Aquitectura

![Flujo](/app/replica_cdc_globant.png)


La estructura de carpetas del repositorio simula 3 servidores de Microsoft SQL Server uno con datos centrales y otros con datos por sucursal:

```
data
├── central
│   ├── CatLineasAereas.csv
├── sucursal1
│   ├── Pasajeros.csv
│   ├── Vuelos.csv
├── sucursal2
│   ├── Pasajeros.csv
│   ├── Vuelos.csv
```

## Objetivo

El requerimiento funcional consiste en centralizar y replicar la información en el datawareohuse de Bigquery.

Para esto debe realizar las implementaciones técnicas que considere necesarias para la replicación de datos con CDC y SQL Replicate hacia Bigquery.


# Configurar conexiones al proyecto de GCP

Instrucciones para obtener la Keyfile JSON:

1. Entra a tu proyecto en la consola de Google Cloud.
2. Ve a IAM & Admin > Service Accounts.
3. Crea una nueva cuenta de servicio dando los permisos de rol  *Administrador de Bigquery* y *Administrador de Dataflow*.
4. Ve a Keys > Add Key > Create New Key, y selecciona el formato JSON.
5. Descarga el archivo JSON. Este archivo lo utilizarás en la configuración del contenedor que realizara el ETL.


# Deplegar el Proyecto Localmente

1. Es necesario instalar Docker Desktop para lograr la ejecución de los contenedores de manera local, así como se explica en la documentación que se comparte.

[Instalar Docker Desktop](https://docs.docker.com/engine/install/)

2. Abrir terminal y ubicarse en el folder donde se almacena el proyecto.
3. Ejecutar el comando  'docker-compose build' para crear las imagenes de los componenetes que intervendrán en el pipeline.
4. Ejecutar el comando 'docker-compose up' para montar el contenedor con las imagenes de los componentes del pipeline

Este comando levantará 1 contenedor Docker en tu máquina, con los componentes necesarios para ejecutar el pipeline:

* SQL Server: Base de datos relacional
* Scrip ETL: Componente necesario para ejecutar el script que tiene las funciones de :

  * Crear la base de datos en SQL Server
  * Ingestar a la base de SQL Server las tablas con los datos de los archivos planos que se encuentran en los distintos folder en 3 tablas (CatLineasAereas, pasajeros, vuelos)
  * Haciendo uso de las credenciales generadas en el proyecto de GCP se permite acceder a lanzar un job por el servicio de Dataflow e ingestar las tablas en Bigquery

3. Verifica que se hayan creado el contenedor Docker ejecutando 'docker ps'.
