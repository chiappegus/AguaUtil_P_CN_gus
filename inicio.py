"""



Ultimo

source .env/Scripts/activate



pip freeze > requeriments.txt


pip install pandas matplotlib openpyxl  geopandas




# PASO 0: genera los decadales.
py scripts/0run_agua_util_P_CN_V2.py
# PASO 1: Generar archivos por departamento (necesita decadales)
py scripts/1resumen_AguaUtil_depto_P_CNV2.py
# PASO 2: Generar tabla consolidada
py scripts/2_0_proc_final_P_CN_V1.py
# PASO 3: Generar GPKG
py scripts/2_1proc_final_P_CN_V3.py



#PARA DIF DE PROMEDIO
py scripts/calcular_anomalias_P_CN.py
py scripts/generar_gpkg_anomalias_P_CN.py



#se va a crear un controlador.py para ejecutar todo en orden :

py controlador.py




"""
