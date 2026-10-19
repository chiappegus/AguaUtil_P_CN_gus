"""
Script de verificación para el cálculo de AU_WGT ponderado
para un departamento y fecha específicos.
Muestra el paso a paso de cómo se combinan los centroides.
"""

import pandas as pd
import os
import glob
from datetime import datetime

# ========== CONFIGURACIÓN (igual que en el script original) ==========
BASE_DIR = "D:/ORA_proyectos/Scripts_ORA-main/AguaUtil_P_CN"
HISTORICOS_DIR = os.path.join(BASE_DIR, "SALIDA_HISTORICOS")
PESOS_FILE = os.path.join(BASE_DIR, "archivos_guia/centroide_gus_todo_mas.xlsx")

# ========== PARÁMETROS DE VERIFICACIÓN ==========
FECHA_OBJETIVO = datetime(2000, 1, 1)  # Fecha a verificar
LINK_OBJETIVO = "06007"                # ADOLFO ALSINA
# Si quieres cambiar de departamento, modifica el link y la fecha.

print("=" * 80)
print(f"🔍 VERIFICACIÓN DE CÁLCULO PARA LINK {LINK_OBJETIVO} EN FECHA {FECHA_OBJETIVO.strftime('%Y-%m-%d')}")
print("=" * 80)

# ========== 1. CARGAR PESOS ==========
df_pesos = pd.read_excel(PESOS_FILE)
df_pesos['link'] = df_pesos['link'].astype(str).str.zfill(5)
# Nos quedamos solo con el departamento objetivo
df_pesos_filtrado = df_pesos[df_pesos['link'] == LINK_OBJETIVO].copy()
print(f"\n📌 Centroides encontrados para link {LINK_OBJETIVO}: {len(df_pesos_filtrado)}")
print(df_pesos_filtrado[['Ctrde_ID', 'PESO_RELATIVO_DEP']].head(10))

# ========== 2. CARGAR DATOS HISTÓRICOS PARA ESA FECHA ==========
# Leer archivos P y CN
all_data = []

# Archivos P
archivos_P = glob.glob(os.path.join(HISTORICOS_DIR, "histdeca_*_P.txt"))
for fp in archivos_P:
    basename = os.path.basename(fp)
    centroide = basename.replace('histdeca_', '').replace('_P.txt', '')
    df = pd.read_csv(fp, sep=';', decimal=',', parse_dates=['f_deca_ref'])
    df['Ctrde_ID'] = centroide
    df['Tipo'] = 'P'
    all_data.append(df)

# Archivos CN
archivos_CN = glob.glob(os.path.join(HISTORICOS_DIR, "histdeca_*_CN.txt"))
for fp in archivos_CN:
    basename = os.path.basename(fp)
    centroide = basename.replace('histdeca_', '').replace('_CN.txt', '')
    df = pd.read_csv(fp, sep=';', decimal=',', parse_dates=['f_deca_ref'])
    df['Ctrde_ID'] = centroide
    df['Tipo'] = 'CN'
    all_data.append(df)

if not all_data:
    print("❌ No se encontraron archivos históricos.")
    exit()

df_hist = pd.concat(all_data, ignore_index=True)
df_hist.rename(columns={'AU_mean': 'AU_mean', 'f_deca_ref': 'Fecha'}, inplace=True)

# Filtrar por fecha objetivo
df_hist_fecha = df_hist[df_hist['Fecha'] == FECHA_OBJETIVO].copy()
print(f"\n📊 Registros históricos para fecha {FECHA_OBJETIVO.strftime('%Y-%m-%d')}: {len(df_hist_fecha)}")

# ========== 3. UNIR CON PESOS PARA EL DEPARTAMENTO OBJETIVO ==========
# Hacemos merge para obtener los pesos de los centroides que están en el departamento
df_merged = pd.merge(df_hist_fecha, df_pesos_filtrado, on='Ctrde_ID', how='inner')
print(f"\n🔗 Centroides del departamento con datos históricos: {len(df_merged)}")

if len(df_merged) == 0:
    print("❌ No hay coincidencia de centroides para ese departamento y fecha.")
    exit()

# ========== 4. MOSTRAR DETALLE POR CENTROIDE ==========
print("\n" + "=" * 80)
print("📋 DETALLE POR CENTROIDE (con PESO y AU_mean)")
print("=" * 80)

# Ordenar para mejor visualización
df_merged = df_merged.sort_values(['Tipo', 'Ctrde_ID'])

# Crear una columna con el producto (contribución)
df_merged['CONTRIBUCION'] = df_merged['AU_mean'] * df_merged['PESO_RELATIVO_DEP']

# Mostrar columnas relevantes
columnas_mostrar = ['Ctrde_ID', 'Tipo', 'AU_mean', 'PESO_RELATIVO_DEP', 'CONTRIBUCION']
print(df_merged[columnas_mostrar].to_string(index=False, float_format='%.4f'))

# ========== 5. CALCULAR EL TOTAL PONDERADO ==========
# Suma de contribuciones (todos los centroides, indistintamente de tipo)
total_ponderado = df_merged['CONTRIBUCION'].sum()

print("\n" + "=" * 80)
print("📊 RESULTADO FINAL")
print("=" * 80)
print(f"✅ AU_WGT ponderado (todos los cultivos combinados): {total_ponderado:.4f}")

# ========== 6. COMPARAR CON EL CÁLCULO SEPARADO POR P Y CN ==========
# Agrupar por Tipo para ver cómo quedaría separado
df_por_tipo = df_merged.groupby('Tipo').apply(
    lambda g: pd.Series({
        'AU_WGT': (g['AU_mean'] * g['PESO_RELATIVO_DEP']).sum(),
        'Cantidad_centroides': len(g)
    })
).reset_index()

print("\n🔹 Desglose por cultivo (P y CN):")
print(df_por_tipo.to_string(index=False, float_format='%.4f'))

# Suma de ambos (debería ser igual al total_ponderado)
suma_por_tipo = df_por_tipo['AU_WGT'].sum()
print(f"\n🔹 Suma de P + CN: {suma_por_tipo:.4f} (coincide con total: {total_ponderado:.4f})")

# ========== 7. MOSTRAR CÓMO QUEDARÍA EL ARCHIVO FINAL ==========
# Si quisiéramos tener un solo valor por departamento (sin distinguir cultivo)
print("\n" + "=" * 80)
print("📁 FORMATO DE SALIDA PROPUESTO (UN SOLO VALOR POR DEPARTAMENTO)")
print("=" * 80)
print(f"Fecha: {FECHA_OBJETIVO.strftime('%Y-%m-%d')}")
print(f"Provincia: {df_merged['nomprov'].iloc[0]}")
print(f"Departamento: {df_merged['nomdep'].iloc[0]}")
print(f"Link: {LINK_OBJETIVO}")
print(f"AU_WGT (combinado): {total_ponderado:.4f}")
print("\n✅ Este sería el valor que se guardaría en el archivo resumen.")