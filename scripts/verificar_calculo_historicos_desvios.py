# debug_std.py
import pandas as pd
import glob
import os

# Leer pesos
df_pesos = pd.read_excel("D:/ORA_proyectos/Scripts_ORA-main/AguaUtil_P_CN/archivos_guia/centroide_gus_todo_mas.xlsx")
df_pesos['link'] = df_pesos['link'].astype(str).str.zfill(5)

# Filtrar link 06007
df_pesos = df_pesos[df_pesos['link'] == '06007']

# Leer histórico de un centroide de ejemplo (todos los que pertenecen a 06007)
# Supongamos que los centroides de ese link son varios, listarlos
print("Centroides para 06007:", df_pesos['Ctrde_ID'].tolist())

# Para cada centroide, leer su archivo histórico y extraer AU_std para 2000-01-01
for ctr in df_pesos['Ctrde_ID'].tolist():
    archivo = f"D:/ORA_proyectos/Scripts_ORA-main/AguaUtil_P_CN/SALIDA_HISTORICOS/histdeca_{ctr}_P.txt"  # o _CN
    if not os.path.exists(archivo):
        archivo = f"D:/ORA_proyectos/Scripts_ORA-main/AguaUtil_P_CN/SALIDA_HISTORICOS/histdeca_{ctr}_CN.txt"
    if os.path.exists(archivo):
        df = pd.read_csv(archivo, sep=';', decimal=',', parse_dates=['f_deca_ref'])
        df_fecha = df[df['f_deca_ref'] == '2000-01-01']
        if not df_fecha.empty:
            std = df_fecha['AU_std'].iloc[0]
            peso = df_pesos[df_pesos['Ctrde_ID'] == ctr]['PESO_RELATIVO_DEP'].iloc[0]
            print(f"Centroide {ctr}: std={std:.3f}, peso={peso:.4f}, contribución={std*peso:.3f}")