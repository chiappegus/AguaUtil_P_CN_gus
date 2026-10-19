"""
Genera archivos de promedio histórico de Agua Util (AU_mean y AU_std)
por departamento, combinando todos los centroides (P y CN) en un solo valor ponderado.
Salida en: AguaUtil_P_CN/ESTADISTICA2000-2020/mean_std/
"""

import pandas as pd
import os
import glob

# ========== CONFIGURACIÓN ==========
BASE_DIR = "D:/ORA_proyectos/Scripts_ORA-main/AguaUtil_P_CN"
HISTORICOS_DIR = os.path.join(BASE_DIR, "SALIDA_HISTORICOS")
PESOS_FILE = os.path.join(BASE_DIR, "archivos_guia/centroide_gus_todo_mas.xlsx")
OUTPUT_DIR = os.path.join(BASE_DIR, "ESTADISTICA2000-2020", "mean_std")

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("="*60)
print("📊 GENERACIÓN DE PROMEDIOS HISTÓRICOS (MEAN Y STD) POR DEPARTAMENTO")
print("📁 Entrada (históricos):", HISTORICOS_DIR)
print("📁 Pesos:", PESOS_FILE)
print("📁 Salida:", OUTPUT_DIR)
print("="*60)

# ========== 1. LEER PESOS ==========
df_pesos = pd.read_excel(PESOS_FILE)
df_pesos['link'] = df_pesos['link'].astype(str).str.zfill(5)
df_pesos = df_pesos[['Ctrde_ID', 'link', 'nomprov', 'nomdep', 'PESO_RELATIVO_DEP']].copy()
print(f"✅ Pesos cargados: {len(df_pesos)} registros")

# ========== 2. LEER ARCHIVOS HISTÓRICOS (P y CN juntos) ==========
all_data = []

# Archivos -P y -CN se leen por igual, sin distinguir tipo
patron_P = os.path.join(HISTORICOS_DIR, "histdeca_*_P.txt")
archivos_P = glob.glob(patron_P)
print(f"📄 Archivos P encontrados: {len(archivos_P)}")
for fp in archivos_P:
    basename = os.path.basename(fp)
    centroide = basename.replace('histdeca_', '').replace('_P.txt', '')
    df = pd.read_csv(fp, sep=';', decimal=',', parse_dates=['f_deca_ref'])
    df['Ctrde_ID'] = centroide
    all_data.append(df)

patron_CN = os.path.join(HISTORICOS_DIR, "histdeca_*_CN.txt")
archivos_CN = glob.glob(patron_CN)
print(f"📄 Archivos CN encontrados: {len(archivos_CN)}")
for fp in archivos_CN:
    basename = os.path.basename(fp)
    centroide = basename.replace('histdeca_', '').replace('_CN.txt', '')
    df = pd.read_csv(fp, sep=';', decimal=',', parse_dates=['f_deca_ref'])
    df['Ctrde_ID'] = centroide
    all_data.append(df)

if not all_data:
    print("❌ No se encontraron archivos históricos. Verifica la ruta.")
    exit()

df_hist = pd.concat(all_data, ignore_index=True)
df_hist.rename(columns={'f_deca_ref': 'Fecha'}, inplace=True)
print(f"✅ Datos históricos combinados: {len(df_hist)} registros")

# ========== 3. UNIR CON PESOS ==========
df_merged = pd.merge(df_hist, df_pesos, on='Ctrde_ID', how='inner')
print(f"✅ Registros con peso: {len(df_merged)}")
if len(df_merged) == 0:
    print("❌ No hubo coincidencia entre centroides históricos y tabla de pesos.")
    exit()

# ========== 4. CALCULAR PROMEDIO PONDERADO POR FECHA Y LINK ==========
# Para el mean: promedio ponderado de AU_mean
# Para el std: promedio ponderado de AU_std (ponderado por el mismo peso)
df_grouped = df_merged.groupby(['Fecha', 'link'], as_index=False).apply(
    lambda g: pd.Series({
        'Prov': g['nomprov'].iloc[0],
        'Depto': g['nomdep'].iloc[0],
        'AU_WGT_mean': (g['AU_mean'] * g['PESO_RELATIVO_DEP']).sum(),
        'AU_WGT_std': (g['AU_std'] * g['PESO_RELATIVO_DEP']).sum()
    })
).reset_index(drop=True)

# Ordenar
df_grouped = df_grouped.sort_values(['Fecha', 'link'])

# ========== 5. GENERAR ARCHIVOS POR FECHA ==========
fechas = sorted(df_grouped['Fecha'].unique())
print(f"📅 Fechas a procesar: {len(fechas)}")

for fecha in fechas:
    df_fecha = df_grouped[df_grouped['Fecha'] == fecha].copy()
    df_fecha = df_fecha[['Fecha', 'Prov', 'Depto', 'link', 'AU_WGT_mean', 'AU_WGT_std']]
    fecha_str = fecha.strftime('%Y%m%d')
    filename = f"PCN_{fecha_str}_resumen_AU_mean_std.xlsx"
    output_path = os.path.join(OUTPUT_DIR, filename)
    df_fecha.to_excel(output_path, index=False, float_format='%.3f')
    print(f"  ✅ {filename}")

print("\n" + "="*60)
print("✅ PROCESO COMPLETADO")
print(f"📁 Archivos guardados en: {OUTPUT_DIR}")
print("="*60)