-- Habilitar CDC en la base de datos
EXEC sys.sp_cdc_enable_db;

-- Habilitar CDC en una tabla específica
EXEC sys.sp_cdc_enable_table
    @source_schema = N'dbo',
    @source_name   = N'TablaDestino1',
    @role_name     = N'cdc_admin';

-- Verificar CDC habilitado
SELECT * FROM cdc.change_tables;
