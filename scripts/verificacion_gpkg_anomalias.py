import geopandas as gpd
gdf = gpd.read_file("D:/ORA_proyectos/Scripts_ORA-main/AguaUtil_P_CN/salidas/0ResumenDepto/20260611/Anomalias_P_CN_20260611.gpkg")
print(gdf.columns.tolist())
#print(gdf[['nomdep', 'ANOMALIA', 'Cultivo']].head())
print(gdf[['PROVINCIA', 'DEPTO', 'ANOMALIA']].head(10))

