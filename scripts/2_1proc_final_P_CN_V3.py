"""
Script para unir la tabla P_CN con el shapefile de departamentos
y generar un archivo GPKG listo para usar en QGIS/ArcGIS
"""

import pandas as pd
import geopandas as gpd
import os
import datetime as dt
from funciones_auxiliares import parse_config

def generar_gpkg_P_CN():
    """
    Une la tabla P_CN con el shapefile de departamentos
    Genera un archivo GPKG
    """
    
    # Leer configuración
    nml = parse_config('./namelist_agua_util_P_CN.txt')
    fecha = nml.get('deca')
    fecha_f = dt.datetime.strptime(fecha, '%Y-%m-%d')
    
    # Rutas
    shapefile_loc = nml.get('shapefile_loc')
    out_final_folder = nml.get('carpeta_out_final')
    
    # Carpeta de salida
    out_folder = out_final_folder + fecha_f.strftime('%Y%m%d') + '/'
    
    # Archivo de tabla P_CN
    archivo_tabla = os.path.join(out_folder, f'Tabla_P_CN_{fecha_f.strftime("%Y%m%d")}.xlsx')
    
    # Archivo de salida GPKG
    archivo_gpkg = os.path.join(out_folder, f'P_CN_{fecha_f.strftime("%Y%m%d")}.gpkg')
    
    print("="*60)
    print("🗺️ GENERANDO GPKG PARA P/CN")
    print("="*60)
    print(f"📅 Fecha: {fecha}")
    print(f"📁 Shapefile base: {shapefile_loc}")
    print(f"📁 Tabla P_CN: {archivo_tabla}")
    print(f"📁 GPKG salida: {archivo_gpkg}")
    print("="*60)
    
    # 1. Leer shapefile de departamentos
    print("\n📖 Leyendo shapefile de departamentos...")
    try:
        gdf = gpd.read_file(shapefile_loc, layer='PARTIDOS')
        print(f"✅ Shapefile cargado: {len(gdf)} departamentos")
        print(f"   Columnas originales: {list(gdf.columns)}")
    except Exception as e:
        print(f"❌ Error leyendo shapefile: {e}")
        return
    
    # 2. Leer tabla P_CN
    print("\n📖 Leyendo tabla P_CN...")
    try:
        df_pcn = pd.read_excel(archivo_tabla)
        print(f"✅ Tabla cargada: {len(df_pcn)} registros")
        print(f"   Columnas: {list(df_pcn.columns)}")
    except Exception as e:
        print(f"❌ Error leyendo tabla: {e}")
        return
    
    # 3. Renombrar TODAS las columnas del shapefile que puedan chocar
    print("\n🔧 Renombrando columnas del shapefile para evitar duplicados...")
    
    # Lista de columnas problemáticas (en minúscula o mayúscula)
    columnas_a_renombrar = {
        'gid': 'gid_shp',
        '__gid': 'id_shp',
        'prov': 'provincia_id',
        'depto': 'depto_id',
        'link': 'link_shp',
        'ENLACE_PROV': 'enlace_prov',
        'ENLACE_DEP': 'enlace_dep',
        'LINKDEP1': 'linkdep1',
    }
    
    # Aplicar renombres (solo si la columna existe)
    for col_old, col_new in columnas_a_renombrar.items():
        if col_old in gdf.columns:
            gdf = gdf.rename(columns={col_old: col_new})
            print(f"   - Renombrado: '{col_old}' -> '{col_new}'")
    
    print(f"\n📋 Columnas del shapefile después de renombrar:")
    print(f"   {list(gdf.columns)}")
    
    # 4. Identificar la columna de link (ahora se llama 'link_shp')
    col_link_gdf = 'link_shp'
    if col_link_gdf not in gdf.columns:
        print(f"❌ No se encontró columna '{col_link_gdf}' en shapefile")
        print(f"   Columnas disponibles: {list(gdf.columns)}")
        return
    
    print(f"🔗 Usando columna '{col_link_gdf}' para unir")
    
    # 5. Unir (JOIN)
    print("\n🔗 Uniendo tablas...")
    
    # Asegurar que los links sean del mismo tipo (string con 5 dígitos)
    gdf[col_link_gdf] = gdf[col_link_gdf].astype(str).str.zfill(5)
    df_pcn['LINK'] = df_pcn['LINK'].astype(str).str.zfill(5)
    
    # Hacer el join
    gdf_merged = gdf.merge(df_pcn, left_on=col_link_gdf, right_on='LINK', how='left')
    
    # Eliminar la columna 'LINK' duplicada
    if 'LINK' in gdf_merged.columns:
        gdf_merged = gdf_merged.drop(columns=['LINK'])
    
    print(f"✅ Join completado")
    print(f"   - Departamentos con datos: {gdf_merged['P_CN'].notna().sum()}")
    print(f"   - Departamentos sin datos: {gdf_merged['P_CN'].isna().sum()}")
    
    # 6. Guardar GPKG
    print(f"\n💾 Guardando GPKG...")
    try:
        gdf_merged.to_file(archivo_gpkg, driver='GPKG')
        print(f"✅ GPKG guardado: {archivo_gpkg}")
    except Exception as e:
        print(f"❌ Error guardando GPKG: {e}")
        return
    
    # 7. Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN FINAL")
    print("="*60)
    print(f"📁 Archivo: {archivo_gpkg}")
    print(f"📊 Departamentos totales: {len(gdf_merged)}")
    print(f"📊 Con valor P_CN: {gdf_merged['P_CN'].notna().sum()}")
    print(f"📊 Sin valor P_CN: {gdf_merged['P_CN'].isna().sum()}")
    
    # Mostrar algunos valores
    if gdf_merged['P_CN'].notna().sum() > 0:
        print("\n📋 Ejemplo de datos:")
        ejemplos = gdf_merged[gdf_merged['P_CN'].notna()][['nomdep', col_link_gdf, 'P_CN']].head(5)
        print(ejemplos.to_string(index=False))
    
    print("\n✅ ¡LISTO! Podés abrir el GPKG en QGIS/ArcGIS")
    print("="*60)

if __name__ == '__main__':
    generar_gpkg_P_CN()