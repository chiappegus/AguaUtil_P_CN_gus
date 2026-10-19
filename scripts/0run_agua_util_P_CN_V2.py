"""
Script ESPECÍFICO para procesar PASTURAS (-P) y CAMPO NATURAL (-CN)
Basado en lista de centroides desde archivo Excel.
No procesa cultivos anuales (maíz, soja, trigo, etc.)
"""

import datetime as dt
import pandas as pd
import numpy as np
import os
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

############
from funciones_auxiliares import parse_config
#from AguaUtil import proccessing_decadal_paralelo_P_CN  # Vamos a crear esta función
from AguaUtil import verifica_fecha
from AguaUtil import get_divpol_file
##############################


# def buscar_archivos_P_CN(carpeta, centroides_permitidos):
#     """
#     Busca archivos -P.txt y -CN.txt que coincidan con los centroides permitidos
#     """
#     archivos_encontrados = []
    
#     for centroide in centroides_permitidos:
#         for sufijo in ['-P', '-CN']:
#             nombre_archivo = f"{centroide}{sufijo}.txt"
#             ruta_completa = os.path.join(carpeta, nombre_archivo)
            
#             if os.path.isfile(ruta_completa):
#                 archivos_encontrados.append(nombre_archivo)
#                 print(f"  ✅ Encontrado: {nombre_archivo}")
    
#     return archivos_encontrados


# def buscar_archivos_P_CN(carpeta, centroides_permitidos):
#     """
#     Busca archivos -P.txt y -CN.txt que coincidan con los centroides permitidos.
#     SOLO archivos que NO sean decadales (que no empiecen con 'decadales_')
#     """
#     archivos_encontrados = []
    
#     for centroide in centroides_permitidos:
#         for sufijo in ['-P', '-CN']:
#             nombre_archivo = f"{centroide}{sufijo}.txt"
#             ruta_completa = os.path.join(carpeta, nombre_archivo)
            
#             # Verificar que existe y que NO es un archivo decadal
#             if os.path.isfile(ruta_completa):
#                 # Asegurarse de que no empiece con 'decadales_'
#                 if not nombre_archivo.startswith('decadales_'):
#                     archivos_encontrados.append(nombre_archivo)
#                     print(f"  ✅ Encontrado: {nombre_archivo}")
    
#     return archivos_encontrados



def buscar_archivos_P_CN(carpeta, centroides_permitidos, sufijo_buscar):
    """
    Busca archivos con un sufijo específico (-P o -CN)
    """
    archivos_encontrados = []
    
    for centroide in centroides_permitidos:
        nombre_archivo = f"{centroide}{sufijo_buscar}.txt"
        ruta_completa = os.path.join(carpeta, nombre_archivo)
        
        if os.path.isfile(ruta_completa):
            archivos_encontrados.append(nombre_archivo)
            print(f"  ✅ Encontrado: {nombre_archivo}")
    
    return archivos_encontrados


def proccessing_decadal_P_CN(lfiles, dic, sufijo):
    """
    Versión específica para P y CN del procesamiento de archivos decadales
    """
    f = open(dic['lfile'], 'a')
    f.write(f'Trabajando en {len(lfiles)} archivos (PROCESAMIENTO PARALELO P/CN)\n')
    f.write('--------------------------------------------------\n')
    f.close()
    
    # Determinamos cuántos procesos usar
    num_cores = max(1, multiprocessing.cpu_count() - 1)
    print(f"Usando {num_cores} núcleos para procesamiento paralelo de P/CN")
    
    # Preparamos la configuración
    config = {
        'pfiles': dic['pfiles'],
        'decafolder': dic['decafolder']
    }
    
    resultados_totales = []
    
    with ProcessPoolExecutor(max_workers=num_cores) as executor:
        futures = {executor.submit(procesar_un_archivo_P_CN, arc, config, sufijo): arc 
                   for arc in lfiles}
        
        for i, future in enumerate(as_completed(futures), 1):
            arc = futures[future]
            try:
                resultado = future.result()
                resultados_totales.extend(resultado)
                
                if i % 50 == 0:
                    print(f"Procesados {i}/{len(lfiles)} archivos...")
                    
            except Exception as e:
                print(f"Error procesando {arc}: {e}")
                resultados_totales.append(f'ERROR CRÍTICO en {arc}: {str(e)}')
    
    f = open(dic['lfile'], 'a')
    for linea in resultados_totales:
        f.write(linea + '\n')
    
    f.write(' #######################################################################################\n')
    f.write(' ################ TERMINO CALCULO DE ARCHIVOS DECADIALES P/CN ##########################\n')
    f.write(' #######################################################################################\n')
    f.close()
    
    print(f"✅ Procesamiento paralelo P/CN completado. Procesados {len(lfiles)} archivos.")


# def procesar_un_archivo_P_CN(arc, config, sufijo):
#     """
#     Procesa UN SOLO archivo de balance para P o CN
#     """
#     import pandas as pd
#     import numpy as np
#     import os
#     from AguaUtil import clas_decada, get_df_deca, get_file_data
    
#     resultados_log = []
    
#     try:
#         bfile = config['pfiles'] + arc
#         df = pd.read_csv(bfile, sep=';', decimal=',',
#                          parse_dates=['Fecha'], date_format='%d/%m/%Y',
#                          encoding='ISO-8859-1')
        
#         if df.empty:
#             return [f'Archivo: {arc} NO TIENE DATOS!']
        
#         df.columns = ['Fecha', 'ALM', 'ETR', 'ETC', 'AU', 'ED', 'EA']
        
#         i_col, f_col = clas_decada(df.Fecha)
#         df = df.assign(i_deca=i_col)
#         deca = get_df_deca(df, f_col)
        
#         # Extraer el nombre del centroide (sin el sufijo)
#         # Ej: "01baMTE_7-P.txt" -> centroide = "01baMTE_7"
#         centroide = arc.replace(f'{sufijo}.txt', '')
        
#         # Guardamos archivo decadal
#         d_file = config['decafolder'] + f'decadales_{centroide}_{sufijo.replace("-", "")}'
#         deca.to_csv(d_file + '.txt', sep=';', decimal=',', 
#                    float_format='%.3f', encoding='ISO-8859-1')
#         resultados_log.append(f'Archivo con datos decadales: {d_file}.txt')
#         resultados_log.append('--------------------------------------------------')
            
#     except Exception as e:
#         resultados_log.append(f'ERROR en archivo {arc}: {str(e)}')
    
#     return resultados_log


def procesar_un_archivo_P_CN(arc, config, sufijo):
    """
    Procesa UN SOLO archivo de balance para P o CN
    """
    import pandas as pd
    import numpy as np
    import os
    from AguaUtil import clas_decada, get_df_deca, get_file_data
    
    resultados_log = []
    
    try:
        bfile = config['pfiles'] + arc
        df = pd.read_csv(bfile, sep=';', decimal=',',
                         parse_dates=['Fecha'], date_format='%d/%m/%Y',
                         encoding='ISO-8859-1')
        
        if df.empty:
            return [f'Archivo: {arc} NO TIENE DATOS!']
        
        df.columns = ['Fecha', 'ALM', 'ETR', 'ETC', 'AU', 'ED', 'EA']
        
        i_col, f_col = clas_decada(df.Fecha)
        df = df.assign(i_deca=i_col)
        deca = get_df_deca(df, f_col)
        
        # Extraer el nombre del centroide (sin el sufijo)
        centroide = arc.replace(f'{sufijo}.txt', '')
        
        # # 👇👇👇 ACA VA EL PRINT DE DEBUG 👇👇👇
        # print(f"Debug: arc={arc}, sufijo={sufijo}, centroide={centroide}")
        # # 👆👆👆 HASTA ACA 👆👆👆
        
        # Guardamos archivo decadal
        d_file = config['decafolder'] + f'decadales_{centroide}_{sufijo.replace("-", "")}'
        deca.to_csv(d_file + '.txt', sep=';', decimal=',', 
                   float_format='%.3f', encoding='ISO-8859-1')
        resultados_log.append(f'Archivo con datos decadales: {d_file}.txt')
        resultados_log.append('--------------------------------------------------')
            
    except Exception as e:
        resultados_log.append(f'ERROR en archivo {arc}: {str(e)}')
    
    return resultados_log


#############################
########## MAIN ############
#############################

if __name__ == '__main__':
    start_time = time.time()
    
    # Leer configuración
    nml = parse_config('./namelist_agua_util_P_CN.txt')
    deca = nml.get('deca')
    dt_deca = dt.datetime.strptime(deca, '%Y-%m-%d')
    path = nml.get('carpeta_bal')
    opath = nml.get('carpeta_ppal')
    deca_folder = nml.get('carpeta_deca')
    ret_folder = nml.get('carpeta_ret')
    out_folder = nml.get('carpeta_out')
    ret_f50 = nml.get('archivo_ret_50')
    ret_f500 = nml.get('archivo_ret_500')
    calcula_deca = nml.get('calcula_deca')
    calculo_por = nml.get('calculo_por')
    
    # Leer lista de centroides permitidos para P y CN
    archivo_centroides = nml.get('archivo_centroides', './archivos_guia/centroides_P_CN.xlsx')
    if os.path.exists(archivo_centroides):
        df_centroides = pd.read_excel(archivo_centroides, sheet_name='centroides')
        centroides_permitidos = df_centroides['Ctrde_ID'].astype(str).tolist()
        print(f"📋 Cargados {len(centroides_permitidos)} centroides desde {archivo_centroides}")
    else:
        print(f"❌ No se encontró el archivo: {archivo_centroides}")
        exit()
    
    # Verificar fecha
    lfiles_temp = [i for i in os.listdir(path) if os.path.isfile(os.path.join(path, i))]
    if lfiles_temp:
        verificador = verifica_fecha(path + lfiles_temp[0], dt_deca)
        if not verificador:
            print('ERROR: NO se puede calcular el valor decadico para la fecha indicada.')
            exit()
    
    # Crear carpetas
    # os.makedirs(opath, exist_ok=True)
    # os.makedirs(deca_folder, exist_ok=True)
    # Crear carpetas (con verificación)
    if opath:
        os.makedirs(opath, exist_ok=True)
    else:
        print("❌ ERROR: carpeta_ppal no definida en namelist")
        exit()

    if deca_folder:
        os.makedirs(deca_folder, exist_ok=True)
    else:
        print("❌ ERROR: carpeta_deca no definida en namelist")
        exit()
    # Configurar carpetas de salida
    salida_50 = out_folder + '50_' + dt_deca.strftime('%Y%m%d') + '/'
    salida_500 = out_folder + '500_' + dt_deca.strftime('%Y%m%d') + '/'
    os.makedirs(salida_50, exist_ok=True)
    os.makedirs(salida_500, exist_ok=True)
    
    logfolder = out_folder + 'LOGFILES/'
    os.makedirs(logfolder, exist_ok=True)
    
    fhoy = dt.datetime.today().strftime('%Y%m%d')
    
    # Procesar para P y CN
    for sufijo in ['-P', '-CN']:
        tipo = sufijo.replace('-', '')
        print(f"\n{'='*60}")
        print(f"🔍 Procesando archivos {sufijo}")
        print(f"{'='*60}")
        
        # Buscar archivos para este sufijo
        lfiles = buscar_archivos_P_CN(path, centroides_permitidos,sufijo)
        
        if not lfiles:
            print(f"⚠️ No se encontraron archivos {sufijo}")
            continue
        
        print(f"📁 Encontrados {len(lfiles)} archivos {sufijo}")
        
        # Log file específico
        lfile = logfolder + f'{fhoy}_{tipo}_logfile.txt'
        
        # Configuración para este procesamiento
        d = {
            'opath': opath,
            'decafolder': deca_folder,
            'pfiles': path,
            'clt': tipo,
            'lfile': lfile,
            'resol': '50',
            's50': salida_50,
            's500': salida_500,
            'debug': False
        }
        
        # Escribir encabezado del log
        f = open(lfile, 'w')
        f.write(f'--------------------------------------------------\n')
        f.write(f'Script específico para {tipo}\n')
        f.write(f'Fecha: {deca}\n')
        f.write(f'Cantidad de archivos: {len(lfiles)}\n')
        f.write(f'--------------------------------------------------\n')
        f.close()
        
        # Procesar
        if calcula_deca == 'SI':
            print(f"###### Procesando {len(lfiles)} archivos {sufijo} ######")
            proccessing_decadal_P_CN(lfiles, d, sufijo)
            print(f"###### Fin Calculo decadales para {tipo} ######")
    
    print(f"\n{'='*60}")
    print('✅ PROCESAMIENTO COMPLETADO')
    print(f"{'='*60}")
    print("--- %s seconds ---" % (time.time() - start_time))