"""calcular_anomalias_P_CN_promedio_desvio.py
Cálculo de anomalías de Agua Util para P y CN.
- ANOMALIA = AU_WGT_actual - AU_WGT_historico_promedio
- ANOMALIA_STD = ANOMALIA / AU_WGT_std_historico
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
    
    # Priorizar fecha especial; si no, usar deca normal
    fecha_str = nml.get('deca_especial')
    if not fecha_str:
        fecha_str = nml.get('deca')
    if not fecha_str:
        print("❌ No se encontró 'deca' ni 'deca_especial'.")
        return
    
    fecha_actual = dt.datetime.strptime(fecha_str, '%Y-%m-%d')
    fecha_hist = clas_decada(fecha_actual)          # 01, 11 o 21
    fecha_hist_2000 = fecha_hist.replace(year=2000)
    fecha_hist_str = fecha_hist_2000.strftime('%Y%m%d')

    # Carpetas (ajusta según tu estructura)
    out_final = nml.get('carpeta_out_final')
    carpeta_historicos = "D:/ORA_proyectos/Scripts_ORA-main/AguaUtil_P_CN/ESTADISTICA2000-2020/mean_std/"

    # Archivos
    archivo_actual = os.path.join(out_final, f"{fecha_actual.strftime('%Y%m%d')}", f"Tabla_P_CN_{fecha_actual.strftime('%Y%m%d')}.xlsx")
    archivo_historico = os.path.join(carpeta_historicos, f"PCN_{fecha_hist_str}_resumen_AU_mean_std.xlsx")
    archivo_salida = os.path.join(out_final, f"{fecha_actual.strftime('%Y%m%d')}", f"Anomalias_P_CN_{fecha_actual.strftime('%Y%m%d')}.xlsx")

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
    # Media: puede llamarse 'AU_WGT_mean' o 'AU_WGT'
    # Std: 'AU_WGT_std'
    if 'AU_WGT_mean' in df_hist.columns and 'AU_WGT_std' in df_hist.columns:
        df_hist.rename(columns={'AU_WGT_mean': 'AU_WGT_historico', 'AU_WGT_std': 'AU_WGT_std'}, inplace=True)
    elif 'AU_WGT' in df_hist.columns and 'AU_WGT_std' in df_hist.columns:
        df_hist.rename(columns={'AU_WGT': 'AU_WGT_historico'}, inplace=True)
    else:
        print("❌ El histórico no tiene las columnas esperadas (media y std).")
        return

    # Renombrar provincia y departamento (pueden llamarse 'Prov'/'Depto' o 'PROVINCIA'/'DEPTO')
    if 'Prov' in df_hist.columns and 'Depto' in df_hist.columns:
        df_hist.rename(columns={'Prov': 'PROVINCIA', 'Depto': 'DEPTO'}, inplace=True)
    elif 'PROVINCIA' in df_hist.columns and 'DEPTO' in df_hist.columns:
        pass  # ya están bien
    else:
        print("⚠️ El histórico no tiene columnas de provincia y departamento. Se dejarán vacías.")
        df_hist['PROVINCIA'] = ''
        df_hist['DEPTO'] = ''

    print(f"✅ Histórico combinado cargado: {len(df_hist)} registros")

    # --- 3. Agrupar por link (por si hay duplicados) ---
    df_hist_avg = df_hist.groupby('link', as_index=False).agg({
        'AU_WGT_historico': 'mean',
        'AU_WGT_std': 'mean',
        'PROVINCIA': 'first',
        'DEPTO': 'first'
    })
    df_hist_avg.rename(columns={'AU_WGT_historico': 'AU_WGT_historico_promedio'}, inplace=True)

    # --- 4. Merge ---
    df_merged = pd.merge(df_actual, df_hist_avg, on='link', how='inner')

    # --- 5. Calcular anomalías ---
    df_merged['ANOMALIA'] = df_merged['AU_WGT_actual'] - df_merged['AU_WGT_historico_promedio']
    df_merged['ANOMALIA_STD'] = df_merged['ANOMALIA'] / df_merged['AU_WGT_std']
    # Reemplazar infinitos por NaN (por si algún std es 0)
    df_merged.replace([float('inf'), float('-inf')], float('nan'), inplace=True)

    # --- 6. Seleccionar columnas finales ---
    # Usamos PROVINCIA y DEPTO del histórico (que ya están en df_merged)
    df_final = df_merged[['PROVINCIA', 'DEPTO', 'LINK', 
                          'AU_WGT_actual', 'AU_WGT_historico_promedio', 'AU_WGT_std', 
                          'ANOMALIA', 'ANOMALIA_STD']].copy()

    # (Opcional) Volver a formatear LINK por si acaso
    df_final['LINK'] = df_final['LINK'].astype(str).str.zfill(5)

    # --- 7. Guardar ---
    os.makedirs(os.path.dirname(archivo_salida), exist_ok=True)
    df_final.to_excel(archivo_salida, index=False, float_format='%.3f')
    print(f"✅ Anomalías guardadas en: {archivo_salida}")

    # --- 8. Resumen ---
    print("\n📊 Resumen de anomalías:")
    print(f"📈 Promedio de ANOMALIA: {df_final['ANOMALIA'].mean():.3f}")
    print(f"📈 Promedio de ANOMALIA_STD: {df_final['ANOMALIA_STD'].mean():.3f}")
    print(f"📊 Departamentos con ANOMALIA_STD > 2: {(df_final['ANOMALIA_STD'] > 2).sum()}")
    print(f"📊 Departamentos con ANOMALIA_STD < -2: {(df_final['ANOMALIA_STD'] < -2).sum()}")

if __name__ == '__main__':
    main()