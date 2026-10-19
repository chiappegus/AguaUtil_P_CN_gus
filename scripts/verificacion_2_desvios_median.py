"""
Verificación puntual del cálculo de promedio ponderado y desvío estándar
para el departamento ADOLFO ALSINA, fecha 2000-01-01.
"""

import pandas as pd
import os
import glob

# ========== CONFIGURACIÓN ==========
BASE_DIR = "D:/ORA_proyectos/Scripts_ORA-main/AguaUtil_P_CN"
HISTORICOS_DIR = os.path.join(BASE_DIR, "SALIDA_HISTORICOS")
PESOS_FILE = os.path.join(BASE_DIR, "archivos_guia/centroide_gus_todo_mas.xlsx")

# ========== 1. LEER PESOS ==========
df_pesos = pd.read_excel(PESOS_FILE)
df_pesos['link'] = df_pesos['link'].astype(str).str.zfill(5)

# Filtramos solo el departamento que nos interesa (Adolfo Alsina, link 06007)
link_buscar = '06007'
df_pesos_filt = df_pesos[df_pesos['link'] == link_buscar].copy()
print(f"Centroides para Adolfo Alsina (link {link_buscar}): {len(df_pesos_filt)}")
print(df_pesos_filt[['Ctrde_ID', 'PESO_RELATIVO_DEP']])

# ========== 2. LEER ARCHIVOS HISTÓRICOS DE ESOS CENTROIDES ==========
# Vamos a buscar los archivos de cada centroide, tanto P como CN
centroides = df_pesos_filt['Ctrde_ID'].tolist()
all_data = []

for cid in centroides:
    # Buscar archivos que coincidan con el centroide (tanto _P como _CN)
    patron_P = os.path.join(HISTORICOS_DIR, f"histdeca_{cid}_P.txt")
    patron_CN = os.path.join(HISTORICOS_DIR, f"histdeca_{cid}_CN.txt")
    
    for patron in [patron_P, patron_CN]:
        if os.path.exists(patron):
            df = pd.read_csv(patron, sep=';', decimal=',', parse_dates=['f_deca_ref'])
            df['Ctrde_ID'] = cid
            all_data.append(df)
        # Si no existe el archivo, simplemente lo ignoramos (puede que no todos los centroides tengan ambos cultivos)

if not all_data:
    print("❌ No se encontraron archivos históricos para esos centroides.")
    exit()

df_hist = pd.concat(all_data, ignore_index=True)
df_hist.rename(columns={'AU_mean': 'AU_mean', 'AU_std': 'AU_std', 'f_deca_ref': 'Fecha'}, inplace=True)

# Filtramos por la fecha específica (2000-01-01)
fecha_buscar = pd.Timestamp('2000-01-01')
df_fecha = df_hist[df_hist['Fecha'] == fecha_buscar].copy()

print(f"\nRegistros para fecha {fecha_buscar.date()}: {len(df_fecha)}")

# ========== 3. UNIR CON PESOS ==========
df_merged = pd.merge(df_fecha, df_pesos_filt, on='Ctrde_ID', how='inner')
print(f"Registros con peso: {len(df_merged)}")

# Mostrar los valores antes del ponderado
print("\n📊 Detalle por centroide:")
print(df_merged[['Ctrde_ID', 'AU_mean', 'AU_std', 'PESO_RELATIVO_DEP']])

# ========== 4. CALCULAR MEDIA PONDERADA ==========
# Media ponderada: suma( AU_mean * peso )
media_ponderada = (df_merged['AU_mean'] * df_merged['PESO_RELATIVO_DEP']).sum()

# Desvío estándar ponderado: sqrt( suma( peso * (AU_std)^2 ) )  (suponiendo independencia)
# Ojo: no es exactamente la fórmula de desvío poblacional, sino que se pondera el desvío de cada centroide.
# Si los datos son independientes, la varianza ponderada es suma(peso^2 * varianza), pero aquí usamos una aproximación más simple:
# desvio_ponderado = sqrt( suma( peso * AU_std^2 ) )
# También se puede usar la fórmula de desvío ponderado de la media, pero en este contexto se suele usar la primera.
varianza_ponderada = (df_merged['PESO_RELATIVO_DEP'] * (df_merged['AU_std'] ** 2)).sum()
desvio_ponderado = varianza_ponderada ** 0.5

print("\n📈 RESULTADOS:")
print(f"  Media ponderada (AU_WGT) = {media_ponderada:.3f}")
print(f"  Desvío ponderado (AU_WGT_STD) = {desvio_ponderado:.3f}")

# Verificar que la suma de pesos = 1 (aproximadamente)
suma_pesos = df_merged['PESO_RELATIVO_DEP'].sum()
print(f"  Suma de pesos = {suma_pesos:.6f} (debe ser ~1)")


# $ py 'd:/ORA_proyectos/Scripts_ORA-main/AguaUtil_P_CN/scripts/verificacion_2_desvios_median.py'
# Centroides para Adolfo Alsina (link 06007): 15
#            Ctrde_ID  PESO_RELATIVO_DEP
# 157      F100-40_15           0.308246
# 234      F100-40_10           0.004236
# 1619   m-FA100-30_6           0.019821
# 2004     FA100-35_4           0.015342
# 2151    FA100-35_37           0.010181
# 2155    FA100-35_34           0.044559
# 2233    FA100-35_12           0.028525
# 2249    FA100-30_10           0.042435
# 2278  m-FAr100-40_1           0.020353
# 2294    FA100-35_51           0.062719
# 2395     FA100-30_2           0.253099
# 2416     FA100-30_3           0.100518
# 2428      FA30-35_2           0.030646
# 2598      FL50-40_6           0.049513
# 3129    FL100-55_32           0.009808

# Registros para fecha 2000-01-01: 15
# Registros con peso: 15

# 📊 Detalle por centroide:
#          Ctrde_ID  AU_mean  AU_std  PESO_RELATIVO_DEP
# 0      F100-40_15     5.86   35.15           0.308246
# 1      F100-40_10    25.12   39.74           0.004236
# 2    m-FA100-30_6     6.06   29.72           0.019821
# 3      FA100-35_4    22.14   22.66           0.015342
# 4     FA100-35_37     3.93   29.80           0.010181
# 5     FA100-35_34     5.45   29.22           0.044559
# 6     FA100-35_12     5.49   23.89           0.028525
# 7     FA100-30_10    22.09   31.22           0.042435
# 8   m-FAr100-40_1    34.05   32.15           0.020353
# 9     FA100-35_51     6.91   28.77           0.062719
# 10     FA100-30_2    -2.61   26.62           0.253099
# 11     FA100-30_3    18.81   24.16           0.100518
# 12      FA30-35_2   -14.03   36.59           0.030646
# 13      FL50-40_6    -7.62   34.45           0.049513
# 14    FL100-55_32     7.21   29.35           0.009808

# 📈 RESULTADOS:
#   Media ponderada (AU_WGT) = 5.369
#   Desvío ponderado (AU_WGT_STD) = 30.608
#   Suma de pesos = 1.000001 (debe ser ~1)
# (env) 