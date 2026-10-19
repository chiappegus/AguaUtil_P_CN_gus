"""
Verificación de los promedios históricos por departamento.
Compara los valores generados en los archivos PCN_* con un recálculo directo.
"""

import pandas as pd
import os
import glob

# ========== CONFIGURACIÓN ==========
BASE_DIR = "D:/ORA_proyectos/Scripts_ORA-main/AguaUtil_P_CN"
PESOS_FILE = os.path.join(BASE_DIR, "archivos_guia/centroide_gus_todo_mas.xlsx")
HISTORICOS_DIR = os.path.join(BASE_DIR, "SALIDA_HISTORICOS")
OUT_DIR = os.path.join(BASE_DIR, "ESTADISTICA2000-2020", "mean")

print("="*60)
print("🔍 VERIFICACIÓN DE PROMEDIOS HISTÓRICOS")
print("📁 Pesos:", PESOS_FILE)
print("📁 Históricos:", HISTORICOS_DIR)
print("📁 Archivos generados:", OUT_DIR)
print("="*60)

# 1. Leer tabla de pesos
df_pesos = pd.read_excel(PESOS_FILE)
df_pesos['link'] = df_pesos['link'].astype(str).str.zfill(5)
df_pesos = df_pesos[['Ctrde_ID', 'link', 'PESO_RELATIVO_DEP']]
print(f"✅ Pesos cargados: {len(df_pesos)} registros")

# 2. Leer todos los históricos
all_hist = []
for f in glob.glob(os.path.join(HISTORICOS_DIR, "histdeca_*.txt")):
    basename = os.path.basename(f)
    if '_P.txt' in basename:
        tipo = 'P'
        ctr = basename.replace('histdeca_', '').replace('_P.txt', '')
    elif '_CN.txt' in basename:
        tipo = 'CN'
        ctr = basename.replace('histdeca_', '').replace('_CN.txt', '')
    else:
        continue
    df = pd.read_csv(f, sep=';', decimal=',', parse_dates=['f_deca_ref'])
    df['Ctrde_ID'] = ctr
    df['Tipo'] = tipo
    all_hist.append(df)

df_hist = pd.concat(all_hist, ignore_index=True)
df_hist.rename(columns={'AU_mean': 'AU_mean', 'f_deca_ref': 'Fecha'}, inplace=True)
print(f"✅ Históricos cargados: {len(df_hist)} registros")

# 3. Unir con pesos
merged = pd.merge(df_hist, df_pesos, on='Ctrde_ID', how='inner')
print(f"✅ Registros con peso: {len(merged)}")

# 4. Calcular AU_WGT ponderado por fecha, link y Tipo
merged['AU_WGT_calc'] = merged['AU_mean'] * merged['PESO_RELATIVO_DEP']
result = merged.groupby(['Fecha', 'link', 'Tipo'], as_index=False)['AU_WGT_calc'].sum()
result.rename(columns={'Tipo': 'Cultivo'}, inplace=True)
print(f"✅ Cálculo ponderado listo: {len(result)} filas")

# 5. Comparar con los archivos generados
archivos_generados = glob.glob(os.path.join(OUT_DIR, "PCN_*.xlsx"))
print(f"\n📄 Archivos a verificar: {len(archivos_generados)}")

diferencias = []

for archivo in archivos_generados:
    fecha_str = os.path.basename(archivo).replace('PCN_', '').replace('_resumen_AU_mean.xlsx', '')
    df_gen = pd.read_excel(archivo)
    df_gen.rename(columns={'link': 'link', 'AU_WGT': 'AU_WGT_gen'}, inplace=True)
    df_gen['link'] = df_gen['link'].astype(str).str.zfill(5)
    
    df_calc = result[result['Fecha'].dt.strftime('%Y%m%d') == fecha_str].copy()
    df_calc.rename(columns={'AU_WGT_calc': 'AU_WGT_calc'}, inplace=True)
    
    merged_check = pd.merge(df_gen, df_calc, on=['link', 'Cultivo'], how='outer')
    merged_check['diff'] = merged_check['AU_WGT_gen'] - merged_check['AU_WGT_calc']
    
    problemas = merged_check[merged_check['diff'].abs() > 0.01]
    if not problemas.empty:
        diferencias.append((fecha_str, problemas))
        print(f"⚠️  {fecha_str}: {len(problemas)} diferencias > 0.01")
    else:
        print(f"✅ {fecha_str}: OK")

if diferencias:
    print("\n" + "="*60)
    print("❌ SE ENCONTRARON DIFERENCIAS")
    for fecha, df_problemas in diferencias:
        print(f"\n📅 Fecha: {fecha}")
        cols = ['link', 'Cultivo', 'AU_WGT_gen', 'AU_WGT_calc', 'diff']
        cols_existentes = [c for c in cols if c in df_problemas.columns]
        print(df_problemas[cols_existentes].to_string(index=False))
else:
    print("\n" + "="*60)
    print("✅ TODOS LOS ARCHIVOS SON CORRECTOS")
    print("="*60)