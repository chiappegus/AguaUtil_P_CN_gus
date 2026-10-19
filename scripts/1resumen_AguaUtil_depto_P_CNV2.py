"""
Script para procesar PASTURAS (-P) y CAMPO NATURAL (-CN)
Etapa 2: Agregación por departamento con formato estilo "cultivos anuales"
- Un archivo Excel por departamento: {provincia}_{departamento}_{link}_P_CN.xlsx
- Solapa "Agua Util" con valores por década y AU_WGT
- Solapa "PESOS" con los pesos de cada centroide
"""

import os
import pandas as pd
import numpy as np
import datetime as dt
import time
from funciones_auxiliares import parse_config

def get_tipo_from_filename(nombre_archivo):
    """Extrae el tipo (P o CN) del nombre del archivo decadal"""
    if '_P.txt' in nombre_archivo:
        return 'P'
    elif '_CN.txt' in nombre_archivo:
        return 'CN'
    return None

def limpiar_nombre(texto):
    """Limpia el texto para usarlo en nombres de archivo"""
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'Ñ': 'N', ' ': '_'
    }
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    return texto

def generar_excel_depto(provincia, depto_nombre, depto_link, df_valores, dict_pesos, tipo, output_folder):
    """
    Genera un archivo Excel por departamento con nombre: {provincia}_{departamento}_{link}_{tipo}.xlsx
    """
    provincia_clean = limpiar_nombre(provincia)
    depto_clean = limpiar_nombre(depto_nombre)
    
    nombre_archivo = os.path.join(output_folder, f"{provincia_clean}_{depto_clean}_{depto_link}_{tipo}.xlsx")
    
    with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
        # Solapa 1: Agua Util
        df_valores.to_excel(writer, sheet_name='Agua Util', index=False, float_format='%.3f')
        
        # Solapa 2: Pesos
        if dict_pesos:
            df_pesos = pd.DataFrame([dict_pesos])
            df_pesos.to_excel(writer, sheet_name='PESOS', index=False, float_format='%.6f')
    
    return nombre_archivo

def procesar_P_CN():
    """
    Procesa archivos decadales de P y CN usando tabla de pesos precalculada
    Genera un archivo Excel por departamento con formato similar a cultivos anuales
    """
    start_time = time.time()
    
    # Leer configuración
    nml = parse_config('./namelist_agua_util_P_CN.txt')
    deca = nml.get('deca')
    dt_deca = dt.datetime.strptime(deca, '%Y-%m-%d')
    
    # Carpetas
    deca_folder = nml.get('carpeta_deca')
    out_folder = nml.get('carpeta_out')
    archivo_pesos = nml.get('archivo_pesos', './archivos_guia/pesos_centroides_P_CN.xlsx')
    
    # Carpeta de salida por departamento
    salida_deptos = out_folder + f'P_CN_por_depto_{dt_deca.strftime("%Y%m%d")}/'
    os.makedirs(salida_deptos, exist_ok=True)
    
    print("="*60)
    print("📊 PROCESAMIENTO DE PASTURAS (P) Y CAMPO NATURAL (CN)")
    print("📁 Formato: un archivo Excel por departamento (similar a cultivos anuales)")
    print("="*60)
    print(f"📅 Fecha: {deca}")
    print(f"📁 Carpeta decadales: {deca_folder}")
    print(f"📁 Carpeta salida: {salida_deptos}")
    print(f"📋 Archivo pesos: {archivo_pesos}")
    print("="*60)
    
    # 1. Leer tabla de pesos
    print("\n📋 Leyendo tabla de pesos...")
    df_pesos = pd.read_excel(archivo_pesos)
    
    # Verificar columnas necesarias
    columnas_necesarias = ['Ctrde_ID', 'depto', 'prov', 'PESO_RELATIVO_DEP']
    for col in columnas_necesarias:
        if col not in df_pesos.columns:
            print(f"❌ Error: No se encuentra la columna '{col}' en el archivo de pesos")
            return
    
    # Buscar columna LINK (puede llamarse 'link' o 'LINK')
    col_link = 'link' if 'link' in df_pesos.columns else 'LINK' if 'LINK' in df_pesos.columns else None
    if not col_link:
        print("⚠️ No se encuentra columna 'link' o 'LINK'. Usando 'depto' como identificador.")
    
    # Crear estructura para almacenar datos
    pesos_por_depto = {}      # clave: (link, nombre, provincia) -> {centroide: peso}
    valores_por_depto_ctr = {} # clave: (link, nombre, provincia) -> {centroide: {fecha: valor}}
    
    for _, row in df_pesos.iterrows():
        depto_nombre = row['nomdep']
        provincia = row['nomprov']
        centroide = row['Ctrde_ID']
        peso = row['PESO_RELATIVO_DEP']
        
        # Obtener link (si no existe, usar el nombre del departamento)
        if col_link:
            depto_link = str(row[col_link])
        else:
            depto_link = limpiar_nombre(depto_nombre)
        
        key = (depto_link, depto_nombre, provincia)
        
        if key not in pesos_por_depto:
            pesos_por_depto[key] = {}
        
        pesos_por_depto[key][centroide] = peso
    
    print(f"✅ Cargados {len(pesos_por_depto)} departamentos con pesos")
    
    # 2. Leer archivos decadales
    print("\n📁 Buscando archivos decadales...")
    archivos = [f for f in os.listdir(deca_folder) 
                if os.path.isfile(os.path.join(deca_folder, f)) 
                and ('_P.txt' in f or '_CN.txt' in f)]
    
    print(f"✅ Encontrados {len(archivos)} archivos decadales")
    
    # 3. Organizar datos
    for archivo in archivos:
        tipo = get_tipo_from_filename(archivo)
        if not tipo:
            continue
        
        # Extraer centroide (ej: "decadales_FL50-40_18_P.txt" -> "FL50-40_18")
        nombre_base = archivo.replace('decadales_', '').replace(f'_{tipo}.txt', '')
        
        # Leer archivo decadal
        ruta = os.path.join(deca_folder, archivo)
        df_deca = pd.read_csv(ruta, sep=';', decimal=',', parse_dates=['f_deca'])
        
        # Buscar en qué departamentos aparece este centroide
        for key, pesos_dict in pesos_por_depto.items():
            if nombre_base in pesos_dict:
                if key not in valores_por_depto_ctr:
                    valores_por_depto_ctr[key] = {}
                if nombre_base not in valores_por_depto_ctr[key]:
                    valores_por_depto_ctr[key][nombre_base] = {}
                
                # Guardar valores por fecha
                for _, row in df_deca.iterrows():
                    fecha = row['f_deca']
                    valor = row['AU']
                    valores_por_depto_ctr[key][nombre_base][fecha] = valor
    
    # 4. Generar archivos Excel por departamento
    print("\n💾 Generando archivos Excel por departamento...")
    
    for key, ctrs_dict in valores_por_depto_ctr.items():
        depto_link, depto_nombre, provincia = key
        
        # Obtener pesos de este departamento
        pesos_dict = pesos_por_depto.get(key, {})
        
        # Recolectar todas las fechas únicas
        todas_fechas = set()
        for ctr, fechas_dict in ctrs_dict.items():
            todas_fechas.update(fechas_dict.keys())
        todas_fechas = sorted(todas_fechas)
        
        # Armar DataFrame con columnas por centroide
        df_resultado = pd.DataFrame()
        df_resultado['Fecha'] = todas_fechas
        
        # Agregar columna por cada centroide
        for ctr, fechas_dict in ctrs_dict.items():
            col_name = f'AU_{ctr}'
            valores = [fechas_dict.get(fecha, np.nan) for fecha in todas_fechas]
            df_resultado[col_name] = valores
        
        # Calcular AU_WGT (promedio ponderado)
        pesos_lista = []
        for ctr in ctrs_dict.keys():
            peso = pesos_dict.get(ctr, 0)
            pesos_lista.append(peso)
        
        suma_pesos = sum(pesos_lista)
        
        # Calcular ponderado para cada fila
        au_wgt = []
        for idx, row in df_resultado.iterrows():
            valores = [row[f'AU_{ctr}'] if not pd.isna(row[f'AU_{ctr}']) else 0 
                      for ctr in ctrs_dict.keys()]
            ponderado = sum(v * p for v, p in zip(valores, pesos_lista)) / suma_pesos if suma_pesos > 0 else np.nan
            au_wgt.append(ponderado)
        
        # Insertar AU_WGT al principio
        df_resultado.insert(1, 'AU_WGT', au_wgt)
        
        # Generar archivo Excel
        nombre_archivo = generar_excel_depto(provincia, depto_nombre, depto_link, 
                                              df_resultado, pesos_dict, 'P_CN', 
                                              salida_deptos)
        print(f"  ✅ {provincia}_{depto_nombre}_{depto_link}_P_CN.xlsx")
    
    # Resumen final
    print("\n" + "="*60)
    print("✅ PROCESAMIENTO COMPLETADO")
    print("="*60)
    print(f"📊 Departamentos procesados: {len(valores_por_depto_ctr)}")
    print(f"📁 Resultados guardados en: {salida_deptos}")
    print("="*60)


if __name__ == '__main__':
    procesar_P_CN()