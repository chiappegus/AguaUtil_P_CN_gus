"""calcular_anomalias_P_CN_promedio_desvio_v4.py
Cálculo de anomalías de Agua Util para P y CN.
- ANOMALIA = AU_WGT_actual - AU_WGT_historico_promedio
- ANOMALIA_STD = ANOMALIA / AU_WGT_std_historico
Incluye mapeo desde archivo de pesos para asegurar nombres correctos de provincia/departamento.
"""

import pandas as pd
import os
import datetime as dt
from funciones_auxiliares import parse_config

def clas_decada(fecha):
    dia = fecha.day
    if dia <= 10:
        return fecha.replace(day=1)
    elif dia <= 20:
        return fecha.replace(day=11)
    else:
        return fecha.replace(day=21)

def main():
    nml = parse_config('./namelist_agua_util_P_CN.txt')
    
    # Priorizar fecha especial
    fecha_str = nml.get('deca_especial')
    if not fecha_str:
        fecha_str = nml.get('deca')
    if not fecha_str:
        print("❌ No se encontró 'deca' ni 'deca_especial'.")
        return
    
    fecha_actual = dt.datetime.strptime(fecha_str, '%Y-%m-%d')
    fecha_hist = clas_decada(fecha_actual)
    fecha_hist_2000 = fecha_hist.replace(year=2000)
    fecha_hist_str = fecha_hist_2000.strftime('%Y%m%d')

    out_final = nml.get('carpeta_out_final')
    carpeta_historicos = "D:/ORA_proyectos/Scripts_ORA-main/AguaUtil_P_CN/ESTADISTICA2000-2020/mean_std/"
    
    # Archivos
    archivo_actual = os.path.join(out_final, f"{fecha_actual.strftime('%Y%m%d')}", f"Tabla_P_CN_{fecha_actual.strftime('%Y%m%d')}.xlsx")
    archivo_historico = os.path.join(carpeta_historicos, f"PCN_{fecha_hist_str}_resumen_AU_mean_std.xlsx")
    archivo_salida = os.path.join(out_final, f"{fecha_actual.strftime('%Y%m%d')}", f"Anomalias_P_CN_{fecha_actual.strftime('%Y%m%d')}.xlsx")
    
    # --- MAPEO de links (archivo de pesos) ---
    PESOS_FILE = "D:/ORA_proyectos/Scripts_ORA-main/AguaUtil_P_CN/archivos_guia/centroide_gus_todo_mas.xlsx"
    df_pesos = pd.read_excel(PESOS_FILE)
    df_pesos['link'] = df_pesos['link'].astype(str).str.zfill(5)
    # Mapeo único: un link -> provincia, departamento (usamos nomprov y nomdep del archivo)
    mapeo = df_pesos[['link', 'nomprov', 'nomdep']].drop_duplicates(subset=['link'])
    mapeo.rename(columns={'nomprov': 'PROVINCIA_SHP', 'nomdep': 'DEPTO_SHP'}, inplace=True)
    print(f"✅ Mapeo de links cargado: {len(mapeo)} departamentos")

    print("="*60)
    print("📊 CÁLCULO DE ANOMALÍAS (media y estandarizada) PARA P/CN")
    print("📅 Fecha actual:", fecha_actual.strftime('%Y-%m-%d'))
    print("📅 Década histórica:", fecha_hist.strftime('%Y-%m-%d'))
    print("📁 Tabla actual:", archivo_actual)
    print("📁 Histórico (media+std):", archivo_historico)
    print("📁 Salida:", archivo_salida)
    print("="*60)

    # --- 1. Leer tabla actual ---
    if not os.path.exists(archivo_actual):
        print(f"❌ No se encontró la tabla actual: {archivo_actual}")
        return
    df_actual = pd.read_excel(archivo_actual)
    # Renombrar columna de valor
    if 'P_CN' in df_actual.columns:
        df_actual.rename(columns={'P_CN': 'AU_WGT_actual'}, inplace=True)
    elif 'AU_WGT' in df_actual.columns:
        df_actual.rename(columns={'AU_WGT': 'AU_WGT_actual'}, inplace=True)
    else:
        print("❌ No se encontró columna de valor (P_CN o AU_WGT) en la tabla actual.")
        return
    # Formatear link
    if 'LINK' in df_actual.columns:
        df_actual['link'] = df_actual['LINK'].astype(str).str.zfill(5)
    elif 'link' in df_actual.columns:
        df_actual['link'] = df_actual['link'].astype(str).str.zfill(5)
    else:
        print("❌ No se encontró columna de link (LINK o link) en la tabla actual.")
        return
    print(f"✅ Tabla actual cargada: {len(df_actual)} registros")

    # --- 2. Leer histórico combinado (media + std) ---
    if not os.path.exists(archivo_historico):
        print(f"❌ No se encontró el histórico: {archivo_historico}")
        return
    df_hist = pd.read_excel(archivo_historico)
    df_hist['link'] = df_hist['link'].astype(str).str.zfill(5)

    # Renombrar columnas del histórico
    if 'AU_WGT_mean' in df_hist.columns and 'AU_WGT_std' in df_hist.columns:
        df_hist.rename(columns={'AU_WGT_mean': 'AU_WGT_historico', 'AU_WGT_std': 'AU_WGT_std'}, inplace=True)
    elif 'AU_WGT' in df_hist.columns and 'AU_WGT_std' in df_hist.columns:
        df_hist.rename(columns={'AU_WGT': 'AU_WGT_historico'}, inplace=True)
    else:
        print("❌ El histórico no tiene las columnas esperadas (media y std).")
        return
    print(f"✅ Histórico combinado cargado: {len(df_hist)} registros")

    # --- 3. Agrupar histórico por link (promedio de media y std) ---
    df_hist_avg = df_hist.groupby('link', as_index=False).agg({
        'AU_WGT_historico': 'mean',
        'AU_WGT_std': 'mean'
    })
    df_hist_avg.rename(columns={'AU_WGT_historico': 'AU_WGT_historico_promedio'}, inplace=True)

    # --- 4. Merge con actual ---
    df_merged = pd.merge(df_actual, df_hist_avg, on='link', how='inner')

    # --- 5. Agregar mapeo de provincia/departamento desde el archivo de pesos ---
    df_merged = df_merged.merge(mapeo, on='link', how='left')

    # --- 6. Calcular anomalías ---
    df_merged['ANOMALIA'] = df_merged['AU_WGT_actual'] - df_merged['AU_WGT_historico_promedio']
    df_merged['ANOMALIA_STD'] = df_merged['ANOMALIA'] / df_merged['AU_WGT_std']
    df_merged.replace([float('inf'), float('-inf')], float('nan'), inplace=True)

    # --- 7. Seleccionar columnas finales ---
    # Usamos PROVINCIA_SHP y DEPTO_SHP como nombres definitivos
    df_merged['PROVINCIA'] = df_merged['PROVINCIA_SHP']
    df_merged['DEPTO'] = df_merged['DEPTO_SHP']
    # Asegurar que LINK tenga 5 dígitos
    df_merged['LINK'] = df_merged['LINK'].astype(str).str.zfill(5)

    # Columnas finales
    columnas_finales = ['PROVINCIA', 'DEPTO', 'LINK', 
                        'AU_WGT_actual', 'AU_WGT_historico_promedio', 'AU_WGT_std', 
                        'ANOMALIA', 'ANOMALIA_STD']
    df_final = df_merged[columnas_finales].copy()

    # --- 8. Guardar ---
    os.makedirs(os.path.dirname(archivo_salida), exist_ok=True)
    df_final.to_excel(archivo_salida, index=False, float_format='%.3f')
    print(f"✅ Anomalías guardadas en: {archivo_salida}")

    # --- 9. Resumen ---
    print("\n📊 Resumen de anomalías:")
    print(f"📈 Promedio de ANOMALIA: {df_final['ANOMALIA'].mean():.3f}")
    print(f"📈 Promedio de ANOMALIA_STD: {df_final['ANOMALIA_STD'].mean():.3f}")
    print(f"📊 Departamentos con ANOMALIA_STD > 2: {(df_final['ANOMALIA_STD'] > 2).sum()}")
    print(f"📊 Departamentos con ANOMALIA_STD < -2: {(df_final['ANOMALIA_STD'] < -2).sum()}")

    # (Opcional) Mostrar algunos registros para verificar
    print("\n📋 Muestra de los primeros 5 registros:")
    print(df_final.head(5).to_string(index=False))

if __name__ == '__main__':
    main()