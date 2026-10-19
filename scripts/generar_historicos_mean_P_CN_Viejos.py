"""
Genera archivos de promedio histórico de Agua Util (AU_mean)
por departamento para P y CN, para cada década (36 archivos).
Salida en: AguaUtil_P_CN/ESTADISTICA2000-2020/mean/
"""

import pandas as pd
import os
import glob
from datetime import datetime

# ========== CONFIGURACIÓN ==========
BASE_DIR = "D:/ORA_proyectos/Scripts_ORA-main/AguaUtil_P_CN"
HISTORICOS_DIR = os.path.join(BASE_DIR, "SALIDA_HISTORICOS")
PESOS_FILE = os.path.join(BASE_DIR, "archivos_guia/centroide_gus_todo_mas.xlsx")
OUTPUT_DIR = os.path.join(BASE_DIR, "ESTADISTICA2000-2020", "mean")

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("="*60)
print("📊 GENERACIÓN DE PROMEDIOS HISTÓRICOS POR DEPARTAMENTO")
print("📁 Entrada (históricos):", HISTORICOS_DIR)
print("📁 Pesos:", PESOS_FILE)
print("📁 Salida:", OUTPUT_DIR)
print("="*60)

# ========== 1. LEER PESOS ==========
df_pesos = pd.read_excel(PESOS_FILE)
df_pesos['link'] = df_pesos['link'].astype(str).str.zfill(5)
df_pesos = df_pesos[['Ctrde_ID', 'link', 'nomprov', 'nomdep', 'PESO_RELATIVO_DEP']].copy()
print(f"✅ Pesos cargados: {len(df_pesos)} registros")

# ========== 2. LEER ARCHIVOS HISTÓRICOS ==========
all_data = []

# Archivos -P
archivos_P = glob.glob(os.path.join(HISTORICOS_DIR, "histdeca_*_P.txt"))
print(f"📄 Archivos P encontrados: {len(archivos_P)}")
for fp in archivos_P:
    basename = os.path.basename(fp)
    centroide = basename.replace('histdeca_', '').replace('_P.txt', '')
    df = pd.read_csv(fp, sep=';', decimal=',', parse_dates=['f_deca_ref'])
    df['Ctrde_ID'] = centroide
    df['Tipo'] = 'P'
    all_data.append(df)

# Archivos -CN
archivos_CN = glob.glob(os.path.join(HISTORICOS_DIR, "histdeca_*_CN.txt"))
print(f"📄 Archivos CN encontrados: {len(archivos_CN)}")
for fp in archivos_CN:
    basename = os.path.basename(fp)
    centroide = basename.replace('histdeca_', '').replace('_CN.txt', '')
    df = pd.read_csv(fp, sep=';', decimal=',', parse_dates=['f_deca_ref'])
    df['Ctrde_ID'] = centroide
    df['Tipo'] = 'CN'
    all_data.append(df)

if not all_data:
    print("❌ No se encontraron archivos históricos. Verifica la ruta.")
    exit()

df_hist = pd.concat(all_data, ignore_index=True)
df_hist.rename(columns={'AU_mean': 'AU_mean', 'f_deca_ref': 'Fecha'}, inplace=True)
print(f"✅ Datos históricos combinados: {len(df_hist)} registros")

# ========== 3. UNIR CON PESOS ==========
df_merged = pd.merge(df_hist, df_pesos, on='Ctrde_ID', how='inner')
print(f"✅ Registros con peso: {len(df_merged)}")
if len(df_merged) == 0:
    print("❌ No hubo coincidencia entre centroides históricos y tabla de pesos.")
    exit()

# ========== 4. CALCULAR PROMEDIO PONDERADO POR FECHA, LINK Y TIPO ==========
df_grouped = df_merged.groupby(['Fecha', 'link', 'Tipo'], as_index=False).apply(
    lambda g: pd.Series({
        'Prov': g['nomprov'].iloc[0],
        'Depto': g['nomdep'].iloc[0],
        'AU_WGT': (g['AU_mean'] * g['PESO_RELATIVO_DEP']).sum()
    })
).reset_index(drop=True)

# Ordenar
df_grouped = df_grouped.sort_values(['Fecha', 'link', 'Tipo'])

# ========== 5. GENERAR ARCHIVOS POR FECHA ==========
fechas = sorted(df_grouped['Fecha'].unique())
print(f"📅 Fechas a procesar: {len(fechas)}")

for fecha in fechas:
    df_fecha = df_grouped[df_grouped['Fecha'] == fecha].copy()
    df_fecha = df_fecha[['Fecha', 'Prov', 'Depto', 'link', 'AU_WGT', 'Tipo']]
    df_fecha.rename(columns={'Tipo': 'Cultivo'}, inplace=True)
    fecha_str = fecha.strftime('%Y%m%d')
    filename = f"PCN_{fecha_str}_resumen_AU_mean.xlsx"
    output_path = os.path.join(OUTPUT_DIR, filename)
    df_fecha.to_excel(output_path, index=False, float_format='%.3f')
    print(f"  ✅ {filename}")

print("\n" + "="*60)
print("✅ PROCESO COMPLETADO")
print(f"📁 Archivos guardados en: {OUTPUT_DIR}")
print("="*60)