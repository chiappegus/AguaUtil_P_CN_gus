"""
Script de depuración para verificar el cálculo de un departamento específico.
Muestra centroide, AU_mean, peso y producto para MAR CHIQUITA en 2000-01-01.
"""

import pandas as pd
import os

BASE_DIR = "D:/ORA_proyectos/Scripts_ORA-main/AguaUtil_P_CN"
PESOS_FILE = os.path.join(BASE_DIR, "archivos_guia/centroide_gus_todo_mas.xlsx")
HISTORICOS_DIR = os.path.join(BASE_DIR, "SALIDA_HISTORICOS")

# Cargar pesos
df_pesos = pd.read_excel(PESOS_FILE)
df_pesos['link'] = df_pesos['link'].astype(str).str.zfill(5)

# Filtrar Mar Chiquita (link 06518)
link_buscado = "06518"
df_pesos_mar = df_pesos[df_pesos['link'] == link_buscado].copy()
print(f"Centroides para Mar Chiquita (link {link_buscado}):")
print(df_pesos_mar[['Ctrde_ID', 'PESO_RELATIVO_DEP']])

# Leer archivos históricos para esos centroides (solo P)
resultados = []
for ctr in df_pesos_mar['Ctrde_ID']:
    archivo = os.path.join(HISTORICOS_DIR, f"histdeca_{ctr}_P.txt")
    if os.path.exists(archivo):
        df = pd.read_csv(archivo, sep=';', decimal=',', parse_dates=['f_deca_ref'])
        # Buscar la fila de 2000-01-01
        fila = df[df['f_deca_ref'] == '2000-01-01']
        if not fila.empty:
            au_mean = fila['AU_mean'].iloc[0]
            peso = df_pesos_mar[df_pesos_mar['Ctrde_ID'] == ctr]['PESO_RELATIVO_DEP'].iloc[0]
            producto = au_mean * peso
            resultados.append({
                'Ctrde_ID': ctr,
                'AU_mean': au_mean,
                'PESO': peso,
                'Producto': producto
            })
        else:
            print(f"⚠️ No se encontró 2000-01-01 para {ctr}")
    else:
        print(f"❌ Archivo no encontrado: {archivo}")

# Crear DataFrame
df_detalle = pd.DataFrame(resultados)
print("\n📊 Detalle del cálculo:")
print(df_detalle.to_string(index=False))

# Total ponderado
total = df_detalle['Producto'].sum()
print(f"\n✅ AU_WGT calculado = {total:.3f}")

# Comparar con el archivo generado
out_file = os.path.join(BASE_DIR, "ESTADISTICA2000-2020/mean/PCN_20000101_resumen_AU_mean.xlsx")
if os.path.exists(out_file):
    df_gen = pd.read_excel(out_file)
    df_gen['link'] = df_gen['link'].astype(str).str.zfill(5)
    valor_gen = df_gen[(df_gen['link'] == link_buscado) & (df_gen['Cultivo'] == 'P')]['AU_WGT'].iloc[0]
    print(f"📄 Valor en archivo generado: {valor_gen:.3f}")
    print(f"✅ Diferencia: {total - valor_gen:.6f} (debe ser ~0)")
else:
    print("⚠️ No se encontró el archivo generado para comparar.")