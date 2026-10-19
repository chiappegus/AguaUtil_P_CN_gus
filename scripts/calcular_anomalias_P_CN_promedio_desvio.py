"""WGT_actual
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
    carpeta_historicos = "D:/ORA_proyectos/Scripts_ORA-main/AguaUtil_P_CN/ESTADISTICA2000-2020/mean_std/"   # <--- Cambio: usamos mean_std

    archivo_actual = os.path.join(out_final, f"{fecha_actual.strftime('%Y%m%d')}", f"Tabla_P_CN_{fecha_actual.strftime('%Y%m%d')}.xlsx")
    # Archivo combinado (media + std)
    archivo_historico_combinado = os.path.join(carpeta_historicos, f"PCN_{fecha_hist_str}_resumen_AU_mean_std.xlsx")
    # Si no existe, intentar con los separados (por si acaso)
    archivo_historico_mean = archivo_historico_combinado.replace('_mean_std', '_mean')  # para buscar en mean/ si existe
    archivo_historico_std  = archivo_historico_combinado.replace('_mean_std', '_std')   # para buscar en mean_std/

    archivo_salida = os.path.join(out_final, f"{fecha_actual.strftime('%Y%m%d')}", f"Anomalias_P_CN_{fecha_actual.strftime('%Y%m%d')}.xlsx")

    print("="*60)
    print("📊 CÁLCULO DE ANOMALÍAS (media y estandarizada) PARA P/CN")
    print("📅 Fecha actual:", fecha_actual.strftime('%Y-%m-%d'))
    print("📅 Década histórica correspondiente:", fecha_hist.strftime('%Y-%m-%d'))
    print("📁 Tabla actual:", archivo_actual)
    print("📁 Histórico (combinado):", archivo_historico_combinado)
    print("📁 Salida:", archivo_salida)
    print("="*60)

    # 1. Leer tabla actual
    if not os.path.exists(archivo_actual):
        print(f"❌ No se encontró la tabla actual: {archivo_actual}")
        return
    df_actual = pd.read_excel(archivo_actual)
    df_actual.rename(columns={'P_CN': 'AU_WGT_actual'}, inplace=True)
    df_actual['link'] = df_actual['LINK'].astype(str).str.zfill(5)
    print(f"✅ Tabla actual cargada: {len(df_actual)} registros")

    # 2. Leer histórico combinado (media + std)
    if os.path.exists(archivo_historico_combinado):
        df_hist = pd.read_excel(archivo_historico_combinado)
        df_hist['link'] = df_hist['link'].astype(str).str.zfill(5)
        # Renombrar columnas según los nombres que tenga
        if 'AU_WGT_mean' in df_hist.columns and 'AU_WGT_std' in df_hist.columns:
            df_hist.rename(columns={'AU_WGT_mean': 'AU_WGT_historico', 'AU_WGT_std': 'AU_WGT_std'}, inplace=True)
        elif 'AU_WGT' in df_hist.columns and 'AU_WGT_std' in df_hist.columns:
            # Si el archivo tiene 'AU_WGT' (media) y 'AU_WGT_std'
            df_hist.rename(columns={'AU_WGT': 'AU_WGT_historico'}, inplace=True)
        else:
            print("❌ El archivo combinado no tiene las columnas esperadas.")
            return
        print(f"✅ Histórico combinado cargado: {len(df_hist)} registros")
    else:
        # Si no existe el combinado, intentar con los separados (por compatibilidad)
        print("⚠️ No se encontró el archivo combinado. Intentando con separados...")
        if os.path.exists(archivo_historico_mean) and os.path.exists(archivo_historico_std):
            df_mean = pd.read_excel(archivo_historico_mean)
            df_std  = pd.read_excel(archivo_historico_std)
            df_mean['link'] = df_mean['link'].astype(str).str.zfill(5)
            df_std['link']  = df_std['link'].astype(str).str.zfill(5)
            df_hist = pd.merge(df_mean, df_std[['link', 'AU_WGT_std']], on='link', how='inner')
            df_hist.rename(columns={'AU_WGT': 'AU_WGT_historico'}, inplace=True)
            print(f"✅ Históricos separados cargados: {len(df_hist)} registros")
        else:
            print(f"❌ No se encontró el histórico en ninguna ubicación.")
            return

    # 3. Agrupar por link (por si hay duplicados, aunque no debería)
    df_hist_avg = df_hist.groupby('link', as_index=False).agg({
        'AU_WGT_historico': 'mean',
        'AU_WGT_std': 'mean'
    })
    df_hist_avg.rename(columns={'AU_WGT_historico': 'AU_WGT_historico_promedio'}, inplace=True)

    # 4. Merge con actual
    df_merged = pd.merge(df_actual, df_hist_avg, on='link', how='inner')

    # 5. Calcular anomalías
    df_merged['ANOMALIA'] = df_merged['AU_WGT_actual'] - df_merged['AU_WGT_historico_promedio']
    df_merged['ANOMALIA_STD'] = df_merged['ANOMALIA'] / df_merged['AU_WGT_std']
    df_merged.replace([float('inf'), float('-inf')], float('nan'), inplace=True)

    # 6. Seleccionar columnas finales
    df_merged = df_merged[['PROVINCIA', 'DEPTO', 'LINK', 
                           'AU_WGT_actual', 'AU_WGT_historico_promedio', 'AU_WGT_std', 
                           'ANOMALIA', 'ANOMALIA_STD']]

    # 7. Guardar
    os.makedirs(os.path.dirname(archivo_salida), exist_ok=True)
    df_merged.to_excel(archivo_salida, index=False, float_format='%.3f')
    print(f"✅ Anomalías guardadas en: {archivo_salida}")

    print("\n📊 Resumen de anomalías:")
    print(f"📈 Promedio de ANOMALIA: {df_merged['ANOMALIA'].mean():.3f}")
    print(f"📈 Promedio de ANOMALIA_STD: {df_merged['ANOMALIA_STD'].mean():.3f}")

if __name__ == '__main__':
    main()