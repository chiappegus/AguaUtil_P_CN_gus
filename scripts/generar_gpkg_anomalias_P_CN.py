"""
Genera un GeoPackage (GPKG) con las anomalías de P/CN por departamento.
"""

import geopandas as gpd
import pandas as pd
import os
import datetime as dt
from funciones_auxiliares import parse_config

def generar_gpkg_anomalias():
    # Leer configuración
    nml = parse_config('./namelist_agua_util_P_CN.txt')
    fecha = nml.get('deca')
    fecha_f = dt.datetime.strptime(fecha, '%Y-%m-%d')
    
    # Carpetas
    out_final = nml.get('carpeta_out_final')
    shapefile_loc = nml.get('shapefile_loc')
    
    # Archivos
    archivo_anom = os.path.join(out_final, f"{fecha_f.strftime('%Y%m%d')}", f"Anomalias_P_CN_{fecha_f.strftime('%Y%m%d')}.xlsx")
    archivo_gpkg = os.path.join(out_final, f"{fecha_f.strftime('%Y%m%d')}", f"Anomalias_P_CN_{fecha_f.strftime('%Y%m%d')}.gpkg")
    
    print("="*60)
    print("🗺️ GENERANDO GPKG DE ANOMALÍAS P/CN")
    print(f"📅 Fecha: {fecha}")
    print(f"📁 Shapefile base: {shapefile_loc}")
    print(f"📁 Anomalías: {archivo_anom}")
    print(f"📁 GPKG salida: {archivo_gpkg}")
    print("="*60)
    
    # 1. Leer shapefile
    print("\n📖 Leyendo shapefile de departamentos...")
    gdf = gpd.read_file(shapefile_loc)
    print(f"✅ Shapefile cargado: {len(gdf)} departamentos")
    
    # 2. Leer anomalías
    print("\n📖 Leyendo archivo de anomalías...")
    df_anom = pd.read_excel(archivo_anom)
    print(f"✅ Anomalías cargadas: {len(df_anom)} registros")
    print(f"   Columnas: {df_anom.columns.tolist()}")
    
    # 3. Asegurar formato del link (5 dígitos)
    if 'LINK' in df_anom.columns:
        df_anom['link'] = df_anom['LINK'].astype(str).str.zfill(5)
        print("✅ Columna 'LINK' usada para el join")
    elif 'link' in df_anom.columns:
        df_anom['link'] = df_anom['link'].astype(str).str.zfill(5)
        print("✅ Columna 'link' usada para el join")
    else:
        print("❌ No se encontró columna de link en el archivo de anomalías")
        return
    
    # 4. Renombrar columnas del shapefile para evitar duplicados
    gdf = gdf.rename(columns={
        'gid': 'gid_shp',
        '__gid': '_id_shp',
        'prov': 'provincia_id',
        'nomprov': 'provincia_nombre',
        'depto': 'depto_id',
        'nomdep': 'departamento_nombre',
        'link': 'link_shp'
    })
    # Asegurar link_shp como string de 5 dígitos
    gdf['link_shp'] = gdf['link_shp'].astype(str).str.zfill(5)
    
    # 5. Unir tablas por link
    print("\n🔗 Uniendo tablas...")
    gdf_merged = gdf.merge(df_anom, left_on='link_shp', right_on='link', how='left')
    
    # 6. Contar registros
    registros_con_datos = gdf_merged['ANOMALIA'].notna().sum()
    registros_sin_datos = len(gdf_merged) - registros_con_datos
    print(f"✅ Join completado. Registros con datos: {registros_con_datos}")
    print(f"   Registros sin datos: {registros_sin_datos}")
    
    # 7. Eliminar columnas duplicadas antes de guardar
    # Después del merge puede haber 'link' (de df_anom) y 'LINK' (original)
    # También 'link_x' y 'link_y' si los nombres se duplican.
    # Nos quedamos con la columna 'link_shp' como referencia y eliminamos las demás
    columnas_a_eliminar = ['link', 'LINK', 'link_x', 'link_y']
    for col in columnas_a_eliminar:
        if col in gdf_merged.columns:
            gdf_merged = gdf_merged.drop(columns=[col])
    
    # 8. Guardar GPKG
    print("\n💾 Guardando GPKG...")
    gdf_merged.to_file(archivo_gpkg, driver='GPKG')
    print(f"✅ GPKG guardado: {archivo_gpkg}")
    
    print("\n" + "="*60)
    print("✅ PROCESO COMPLETADO")
    print(f"📁 GPKG: {archivo_gpkg}")
    print("="*60)

if __name__ == '__main__':
    generar_gpkg_anomalias()