"""
Script para unir la tabla de ANOMALÍAS con el shapefile de departamentos
y generar un archivo GPKG con todas las columnas de anomalía.
"""

import datetime as dt
import os

import geopandas as gpd
import pandas as pd
from funciones_auxiliares import parse_config


def generar_gpkg_anomalias():
    nml = parse_config("./namelist_agua_util_P_CN.txt")
    fecha = nml.get("deca")
    fecha_f = dt.datetime.strptime(fecha, "%Y-%m-%d")

    shapefile_loc = nml.get("shapefile_loc")
    out_final_folder = nml.get("carpeta_out_final")
    out_folder = out_final_folder + fecha_f.strftime("%Y%m%d") + "/"

    # ultimo Cambio
    out_final_QGIS_GPKG = nml.get("carpeta_out_Anomalias_P_CN_gpkg_QGIS")

    # Leer el archivo de anomalías (ya tiene todas las columnas)
    archivo_anom = os.path.join(
        out_folder, f"Anomalias_P_CN_{fecha_f.strftime('%Y%m%d')}.xlsx"
    )
    archivo_gpkg = os.path.join(
        out_folder, f"Anomalias_P_CN_{fecha_f.strftime('%Y%m%d')}.gpkg"
    )
    archivo_gpkg_GIS = os.path.join(out_final_QGIS_GPKG, "Anomalias_P_CN.gpkg")

    print("=" * 60)
    print("🗺️ GENERANDO GPKG DE ANOMALÍAS P/CN")
    print("📅 Fecha:", fecha)
    print("📁 Shapefile base:", shapefile_loc)
    print("📁 Archivo anomalías:", archivo_anom)
    print("📁 GPKG salida:", archivo_gpkg)
    print("📁 GPKG_QGIS salida:", archivo_gpkg_GIS)
    print("=" * 60)

    # 1. Leer shapefile
    # gdf = gpd.read_file(shapefile_loc, layer='PARTIDOS')
    gdf = gpd.read_file(shapefile_loc, layer="parti2")
    print(f"✅ Shapefile cargado: {len(gdf)} departamentos")

    # Renombrar columnas para evitar duplicados
    columnas_a_renombrar = {
        "gid": "gid_shp",
        "__gid": "id_shp",
        "prov": "provincia_id",
        "depto": "depto_id",
        "link": "link_shp",
        "ENLACE_PROV": "enlace_prov",
        "ENLACE_DEP": "enlace_dep",
        "LINKDEP1": "linkdep1",
    }
    for col_old, col_new in columnas_a_renombrar.items():
        if col_old in gdf.columns:
            gdf = gdf.rename(columns={col_old: col_new})

    # Asegurar link_shp como string de 5 dígitos
    gdf["link_shp"] = gdf["link_shp"].astype(str).str.zfill(5)

    # 2. Leer anomalías
    df_anom = pd.read_excel(archivo_anom)
    df_anom["LINK"] = df_anom["LINK"].astype(str).str.zfill(5)
    print(f"✅ Anomalías cargadas: {len(df_anom)} registros")

    # 3. Unir (left join) por link
    gdf_merged = gdf.merge(df_anom, left_on="link_shp", right_on="LINK", how="left")

    # Eliminar la columna duplicada 'LINK'
    if "LINK" in gdf_merged.columns:
        gdf_merged = gdf_merged.drop(columns=["LINK"])

    # 4. Guardar GPKG
    gdf_merged.to_file(archivo_gpkg, driver="GPKG")
    print(f"✅ GPKG guardado: {archivo_gpkg}")

    gdf_merged.to_file(archivo_gpkg_GIS, driver="GPKG")
    print(f"✅ GPKG guardado: {archivo_gpkg_GIS}")

    print(f"   Columnas incluidas: {gdf_merged.columns.tolist()}")

    print("\n✅ ¡LISTO! Abrí el GPKG en QGIS/ArcGIS para visualizar:")
    print("   - AU_WGT_actual")
    print("   - AU_WGT_historico_promedio")
    print("   - AU_WGT_std")
    print("   - ANOMALIA")
    print("   - ANOMALIA_STD")


if __name__ == "__main__":
    generar_gpkg_anomalias()
