"""
Script para generar tablas finales y shapefiles de PASTURAS (P) y CAMPO NATURAL (CN)
Similar a 2proc_final_depto.py pero adaptado para P/CN
"""

import os
import pandas as pd
import numpy as np
import datetime as dt
import time
from funciones_auxiliares import parse_config
from funciones_auxiliares import get_shapefile_AU

def formatear_link(link):
    """
    Formatea el LINK a 5 dígitos (agrega cero a la izquierda si es necesario)
    Ej: 6518 -> 06518
    """
    link_str = str(link).strip()
    return link_str.zfill(5)

def generar_tabla_P_CN():
    """
    Genera tabla por departamento para P y CN
    Y crea los shapefiles correspondientes
    """
    start_time = time.time()
    
    # Leer configuración
    nml = parse_config('./namelist_agua_util_P_CN.txt')
    fecha = nml.get('deca')
    fecha_f = dt.datetime.strptime(fecha, '%Y-%m-%d')
    
    # Carpetas
    wrk_folder = nml.get('carpeta_out')  # Carpeta con los archivos P_CN_por_depto
    out_final_folder = nml.get('carpeta_out_final')
    shapefile_loc = nml.get('shapefile_loc')
    
    # Carpeta de salida
    out_folder = out_final_folder + fecha_f.strftime('%Y%m%d') + '/'
    shape_outfolder = out_folder + 'shapefiles/'
    os.makedirs(out_folder, exist_ok=True)
    os.makedirs(shape_outfolder, exist_ok=True)
    
    print("="*60)
    print("📊 GENERANDO TABLA FINAL PARA P/CN")
    print("="*60)
    print(f"📅 Fecha: {fecha}")
    print(f"📁 Carpeta de trabajo: {wrk_folder}")
    print(f"📁 Carpeta de salida: {out_folder}")
    print(f"📁 Shapefiles: {shape_outfolder}")
    print("="*60)
    
    # Buscar la carpeta con los archivos por departamento
    patron_busqueda = f"P_CN_por_depto_{fecha_f.strftime('%Y%m%d')}"
    carpeta_deptos = None
    
    for item in os.listdir(wrk_folder):
        if patron_busqueda in item and os.path.isdir(os.path.join(wrk_folder, item)):
            carpeta_deptos = os.path.join(wrk_folder, item)
            break
    
    if not carpeta_deptos:
        print(f"❌ No se encontró la carpeta: {patron_busqueda}")
        print(f"📁 Buscando en: {wrk_folder}")
        return
    
    print(f"📁 Carpeta de departamentos encontrada: {carpeta_deptos}")
    
    # Leer todos los archivos Excel de departamentos
    archivos = [f for f in os.listdir(carpeta_deptos) if f.endswith('_P_CN.xlsx')]
    print(f"📋 Encontrados {len(archivos)} archivos de departamentos")
    
    # Recolectar datos para la tabla final
    datos_tabla = []  # Para Tabla_P_CN (valores actuales)
    
    for archivo in archivos:
        # Extraer información del nombre del archivo
        # Formato esperado: PROVINCIA_DEPARTAMENTO_LINK_P_CN.xlsx
        nombre_sin_ext = archivo.replace('_P_CN.xlsx', '')
        partes = nombre_sin_ext.split('_')
        
        # El LINK es la última parte
        if len(partes) >= 3:
            provincia = '_'.join(partes[:-2])  # Puede tener guiones bajos
            depto = partes[-2]
            link_raw = partes[-1]
            link_formateado = formatear_link(link_raw)
        else:
            print(f"⚠️ Formato inesperado: {archivo}")
            continue
        
        # Leer el archivo Excel del departamento
        ruta_excel = os.path.join(carpeta_deptos, archivo)
        
        ''' nuevo ve si hay en la fecha especial '''
        try:
            
            df_au = pd.read_excel(ruta_excel, sheet_name='Agua Util')
            
            # Convertir la columna 'Fecha' a datetime si no lo está (para comparar bien)
            df_au['Fecha'] = pd.to_datetime(df_au['Fecha'])
            
            fecha_especial_str = nml.get('deca_especial')
            
            if fecha_especial_str:
                # Convertir la fecha especial a datetime
                fecha_buscar = pd.to_datetime(fecha_especial_str, format='%Y-%m-%d')
                
                # Buscar la fila que coincida con esa fecha (puede haber varias, tomamos la primera)
                mascara = df_au['Fecha'] == fecha_buscar
                if mascara.any():
                    fila = df_au[mascara].iloc[0]   # primera coincidencia
                else:
                    # Si no se encuentra, usamos la última (o puedes lanzar error)
                    print(f"⚠️ No se encontró la fecha {fecha_especial_str}, usando la última.")
                    fila = df_au.iloc[-1]
            else:
                # Sin fecha especial: usar la última fila
                fila = df_au.iloc[-1]
            
            # Ahora sí, obtenemos fecha y peso de la fila seleccionada
            fecha_decada = fila['Fecha']
            au_wgt = fila['AU_WGT']

            datos_tabla.append({
                'PROVINCIA': provincia,
                'DEPTO': depto,
                'LINK': link_formateado,
                'P_CN': au_wgt,
                'Fecha': fecha_decada
            })
            
        except Exception as e:
            print(f"❌ Error procesando {archivo}: {e}")
        
        # try:
        #     # Leer la solapa "Agua Util"
        #     df_au = pd.read_excel(ruta_excel, sheet_name='Agua Util')
            
        #     # Tomar la última fila (década más reciente)
        #     ultima_fila = df_au.iloc[-1]
        #     fecha_decada = ultima_fila['Fecha']
        #     au_wgt = ultima_fila['AU_WGT']
            
        #     # Guardar en la tabla
        #     datos_tabla.append({
        #         'PROVINCIA': provincia,
        #         'DEPTO': depto,
        #         'LINK': link_formateado,
        #         'P_CN': au_wgt,
        #         'Fecha': fecha_decada
        #     })
            
        # except Exception as e:
        #     print(f"❌ Error procesando {archivo}: {e}")
    
    # Crear DataFrame final
    if datos_tabla:
        df_final = pd.DataFrame(datos_tabla)
        
        # Ordenar por LINK
        df_final = df_final.sort_values('LINK').reset_index(drop=True)
        
        # =============================================
        # 1. Guardar Tabla de AU (valores actuales)
        # =============================================
        archivo_au = os.path.join(out_folder, f'Tabla_P_CN_{fecha_f.strftime("%Y%m%d")}.xlsx')
        df_au_final = df_final[['PROVINCIA', 'DEPTO', 'LINK', 'P_CN']].copy()
        df_au_final.to_excel(archivo_au, index=False, float_format='%.3f')
        print(f"\n✅ Guardado: {archivo_au}")
        
        # Generar shapefile para AU
        try:
            get_shapefile_AU(df_au_final, type_AU='P_CN', 
                           shapefile_loc=shapefile_loc, 
                           outfolder=shape_outfolder)
            print(f"✅ Shapefile generado para P_CN")
        except Exception as e:
            print(f"⚠️ No se pudo generar shapefile: {e}")
        
        # =============================================
        # NOTA: Para anomalías se necesitan datos históricos
        # Si tenés estadísticas históricas para P/CN, podemos calcularlas
        # =============================================
        print("\n" + "="*60)
        print("📊 COMPLETADO")
        print("="*60)
        print(f"📊 Departamentos procesados: {len(df_final)}")
        print(f"📁 Resultados guardados en: {out_folder}")
        print(f"📁 Shapefiles guardados en: {shape_outfolder}")
        
        # Mostrar un resumen
        print("\n📋 Resumen de LINKs (verificar formato 5 dígitos):")
        print(df_final[['PROVINCIA', 'DEPTO', 'LINK']].head(10).to_string(index=False))
        
    else:
        print("❌ No se pudieron recolectar datos")

if __name__ == '__main__':
    generar_tabla_P_CN()