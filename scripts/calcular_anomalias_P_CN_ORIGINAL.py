"""
Cálculo de anomalías de Agua Util para P y CN.
ANOMALIA = AU_WGT_actual - AU_WGT_historico_promedio_para_la_decada
"""

import pandas as pd
import os
import datetime as dt
from funciones_auxiliares import parse_config

def clas_decada(fecha):
    """Clasifica una fecha en década (01, 11 o 21) según el día."""
    dia = fecha.day
    if dia <= 10:
        return fecha.replace(day=1)
    elif dia <= 20:
        return fecha.replace(day=11)
    else:
        return fecha.replace(day=21)

def main():
    # Leer configuración
    nml = parse_config('./namelist_agua_util_P_CN.txt')
    fecha_str = nml.get('deca')  # '2026-03-01'
    fecha_actual = dt.datetime.strptime(fecha_str, '%Y-%m-%d')
    fecha_hist = clas_decada(fecha_actual)  # misma fecha pero con día 01, 11 o 21
    fecha_hist_str = fecha_hist.strftime('%Y%m%d')

    # Carpetas
    out_final = nml.get('carpeta_out_final')
    carpeta_historicos = "D:/ORA_proyectos/Scripts_ORA-main/AguaUtil_P_CN/ESTADISTICA2000-2020/mean/"
    fecha_hist_2000 = fecha_hist.replace(year=2000)
    fecha_hist_str = fecha_hist_2000.strftime('%Y%m%d')
    # Archivos
    archivo_actual = os.path.join(out_final, f"{fecha_actual.strftime('%Y%m%d')}", f"Tabla_P_CN_{fecha_actual.strftime('%Y%m%d')}.xlsx")
    archivo_historico = os.path.join(carpeta_historicos, f"PCN_{fecha_hist_str}_resumen_AU_mean.xlsx")
    archivo_salida = os.path.join(out_final, f"{fecha_actual.strftime('%Y%m%d')}", f"Anomalias_P_CN_{fecha_actual.strftime('%Y%m%d')}.xlsx")

    print("="*60)
    print("📊 CÁLCULO DE ANOMALÍAS PARA P/CN")
    print("📅 Fecha actual:", fecha_actual.strftime('%Y-%m-%d'))
    print("📅 Década histórica correspondiente:", fecha_hist.strftime('%Y-%m-%d'))
    print("📁 Tabla actual:", archivo_actual)
    print("📁 Histórico:", archivo_historico)
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

    # 2. Leer histórico
    if not os.path.exists(archivo_historico):
        print(f"❌ No se encontró el histórico: {archivo_historico}")
        return
    df_hist = pd.read_excel(archivo_historico)
    df_hist['link'] = df_hist['link'].astype(str).str.zfill(5)
    df_hist.rename(columns={'AU_WGT': 'AU_WGT_historico'}, inplace=True)
    print(f"✅ Histórico cargado: {len(df_hist)} registros")

    # 3. Merge por link y Cultivo
    # En df_actual la columna de cultivo no existe, solo tenemos 'PROVINCIA', 'DEPTO', 'LINK', 'P_CN'
    # Necesitamos agregar una columna 'Cultivo' para distinguir P y CN.
    # Pero la tabla actual tiene un solo valor por departamento (P_CN combinado?).
    # En realidad, la tabla actual generada tiene una sola fila por departamento, con el valor de AU_WGT.
    # Sin embargo, para P y CN hay valores separados. En la tabla actual, la columna 'P_CN' es el valor.
    # Pero no distingue entre P y CN. Por eso necesitamos otra fuente.
    # En la tabla actual, cada fila es un departamento con un solo valor (el ponderado de P y CN juntos?).
    # Según el script anterior, la tabla final tiene una columna 'P_CN' que es el AU_WGT para ese departamento.
    # Pero no indica si es P o CN. En la tabla de históricos sí hay separación por 'Cultivo'.
    # Por lo tanto, para calcular anomalías, necesitamos tener los valores separados para P y CN.
    # La tabla actual generada por 2_0_proc_final_P_CN_V1.py tiene una sola fila por departamento y un solo valor.
    # Eso significa que ese valor es la combinación ponderada de P y CN? O es solo uno de ellos?
    # Revisando el script 2_0_proc_final_P_CN_V1.py, veo que toma la última fila del archivo por departamento,
    # pero no distingue entre P y CN. Cada archivo por departamento contiene una columna AU_WGT que ya es el ponderado
    # de todos los centroides de ese departamento (tanto P como CN). Pero el archivo por departamento contiene ambas columnas
    # (P y CN) en el mismo archivo. Pero la tabla final solo toma un valor por departamento (el AU_WGT).
    # Eso significa que la tabla actual no distingue entre P y CN.
    # Para calcular anomalías por separado, necesitamos la tabla actual con separación.
    # La solución: usar la tabla intermedia que generamos en el script 1resumen_AguaUtil_depto_P_CNV2.py
    # que genera archivos por departamento con una columna AU_WGT (que es el ponderado de todos los centroides,
    # sin distinguir P y CN). Pero en los históricos, tenemos separación por Cultivo.
    # Para hacer la anomalía, necesitamos los valores actuales separados por P y CN.

    # Dado que la tabla actual no separa P y CN, vamos a calcular la anomalía como:
    # ANOMALIA = AU_WGT_actual - AU_WGT_historico_promedio (para la misma combinación de P y CN?).
    # Pero el histórico tiene separado, así que vamos a promediar el histórico de P y CN para cada departamento,
    # y luego restar del actual.

    # Esto es una aproximación. La mejor manera sería tener el actual separado.
    # Sin embargo, los archivos por departamento generados por 1resumen_AguaUtil_depto_P_CNV2.py sí contienen
    # una columna AU_WGT que es el ponderado de todos los centroides (sin separar P y CN).
    # Así que podemos usar ese valor directamente.

    # Pero para la anomalía, necesitamos el valor actual y el valor histórico.
    # El valor histórico debe ser el promedio de P y CN (ponderado de la misma manera que el actual).
    # En el histórico, tenemos P y CN separados. Podemos combinarlos en un solo valor por departamento
    # (promedio simple o ponderado según la proporción de P y CN). O podemos calcular la anomalía por separado
    # y luego promediar. Pero eso sería complicado.

    # Lo más simple es considerar que el valor actual es el AU_WGT (que ya es el ponderado de todos los centroides,
    # independientemente de si son P o CN). Entonces el valor histórico debe ser el promedio histórico de AU_WGT
    # para ese departamento (que sería el promedio de P y CN si tuviéramos los pesos separados).

    # Dado que en la tabla actual no tenemos separación, vamos a calcular la anomalía como:
    # ANOMALIA = AU_WGT_actual - AU_WGT_historico_promedio (promediando P y CN en el histórico).

    # Pero el histórico tiene dos filas por departamento (una para P y otra para CN).
    # Vamos a promediar ambas para obtener un valor histórico único por departamento.
    df_hist_avg = df_hist.groupby('link', as_index=False)['AU_WGT_historico'].mean()
    df_hist_avg.rename(columns={'AU_WGT_historico': 'AU_WGT_historico_promedio'}, inplace=True)

    # Merge
    df_merged = pd.merge(df_actual, df_hist_avg, on='link', how='inner')
    df_merged['ANOMALIA'] = df_merged['AU_WGT_actual'] - df_merged['AU_WGT_historico_promedio']

    # Agregar columnas de provincia y depto
    df_merged = df_merged[['PROVINCIA', 'DEPTO', 'LINK', 'AU_WGT_actual', 'AU_WGT_historico_promedio', 'ANOMALIA']]

    # Guardar
    os.makedirs(os.path.dirname(archivo_salida), exist_ok=True)
    df_merged.to_excel(archivo_salida, index=False, float_format='%.3f')
    print(f"✅ Anomalías guardadas en: {archivo_salida}")

    # Mostrar resumen
    print("\n📊 Resumen de anomalías:")
    print(f"📈 Promedio de anomalía: {df_merged['ANOMALIA'].mean():.3f}")
    print(f"📉 Mínimo: {df_merged['ANOMALIA'].min():.3f}")
    print(f"📈 Máximo: {df_merged['ANOMALIA'].max():.3f}")
    print(f"📊 Departamentos con anomalía negativa: {(df_merged['ANOMALIA'] < 0).sum()}")
    print(f"📊 Departamentos con anomalía positiva: {(df_merged['ANOMALIA'] > 0).sum()}")

if __name__ == '__main__':
    main()