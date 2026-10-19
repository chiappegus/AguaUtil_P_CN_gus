import warnings

import geopandas as gpd

# Ignorar advertencias de formato de geometría si las hubiera
warnings.filterwarnings("ignore", category=UserWarning)

# 1. Definir las rutas de los archivos
shapefile_principal = r"D:/ORA_proyectos/Decadiales_-_AU_gus1/layers/Dptos_geo2.gpkg"
secundaria = r"D:/documentos/mariano_laburo/Convenios_mapas/QConsolidate_aca/MapasVigentes_3-4-2020/layers/PARTIDOS.gpkg"
output_gpkg = r"D:/ORA_proyectos/Decadiales_-_AU_gus1/layers/Dptos_geo2_unido.gpkg"

# 2. Leer los archivos con GeoPandas
print("Leyendo archivos...")
gdf_principal = gpd.read_file(shapefile_principal)
gdf_secundaria = gpd.read_file(secundaria)

# 3. Eliminar la geometría del archivo secundario (nos quedamos solo con la tabla de atributos)
# Como no nos interesa su geom, lo convertimos a un DataFrame normal
if "geometry" in gdf_secundaria.columns:
    df_secundaria = gdf_secundaria.drop(columns="geometry")
else:
    df_secundaria = gdf_secundaria

# 4. Asegurar que las columnas de unión sean texto (string) de 5 dígitos
# El .zfill(5) asegura que si hay un número "1", lo convierta a "00001"
gdf_principal["in1"] = gdf_principal["in1"].astype(str).str.zfill(5)
df_secundaria["link"] = df_secundaria["link"].astype(str).str.zfill(5)

# 5. Realizar la unión (merge)
# how='left' asegura que mantenemos todos los registros del principal y su geometría
print("Uniendo tablas...")
# gdf_unido = gdf_principal.merge(
#     df_secundaria, left_on="in1", right_on="link", how="left"
# )
gdf_unido = gdf_principal.merge(
    df_secundaria, left_on="in1", right_on="link", how="left"
)


# (Opcional) Si querés eliminar la columna 'link' porque ya tenés 'in1' y es redundante:
# if "link" in gdf_unido.columns:
#     gdf_unido = gdf_unido.drop(columns=["link"])

# 6. Guardar el resultado en un nuevo archivo GeoPackage
print(f"Guardando el nuevo archivo en: {output_gpkg}")
gdf_unido.to_file(output_gpkg, layer="capa_unida", driver="GPKG")

print("¡Proceso terminado con éxito!")
