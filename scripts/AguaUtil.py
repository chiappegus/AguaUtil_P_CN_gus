"""
Funciones para trabajar con los archivos de porcentaje
de Agua Util por cultivo.
Tareas que hay que realizar:
- Lectura de TXT con los datos diarios
- Calculo de medias decadales (1-10; 11-20; 21-Fin de Mes)
- Union de estos datos con superficies por departamento y por cuartel
"""
import os
import pandas as pd
import numpy as np
import datetime as dt
import calendar
import matplotlib.pyplot as plt

def clas_decada(fechas):
    """
    Funcion para crear array que clasifica las fechas
    por decada diaria mensual.
    """
    #
    r_i = np.zeros(np.shape(fechas))
    r_d = []  #np.zeros(np.shape(fechas))
    years = np.unique([i.year for i in fechas])
    #print(len(years)*12*3)
    nindex = 1
    for yr in years:
        for mo in np.arange(1,13):
            i1 = np.logical_and(fechas >= dt.datetime(yr,mo,1),
                                fechas <= dt.datetime(yr,mo,10))
            i2 = np.logical_and(fechas >= dt.datetime(yr,mo,11),
                                fechas <= dt.datetime(yr,mo,20))
            u_day = calendar.monthrange(yr, mo)[1]
            i3 = np.logical_and(fechas >= dt.datetime(yr,mo,21),
                                fechas <= dt.datetime(yr,mo,u_day))
            r_i[i1] = nindex
            r_i[i2] = nindex + 1
            r_i[i3] = nindex + 2
            r_d.append(dt.datetime(yr,mo,1))
            r_d.append(dt.datetime(yr,mo,11))
            r_d.append(dt.datetime(yr,mo,21))
            nindex = nindex + 3

    a = int(r_i[0]) - 1
    b = int(r_i[-1])
    return r_i, r_d[a:b]

def get_file_data(archivo):
    """
    Separa del nombre del archivo y extrae nombre de Centroide (ctrd)
    y cultivo (clt)
    """
    diccionario = {}
    l0 = archivo.split('.')  # ultimo valor es 'txt'
    str1 = ''.join(l0[:-1])  # Elimina los puntos (e.g M1.1 queda M11)
    l1 = str1.split('-')  # el ultimo debiera ser el cultivo
    if 'S1' in l1:
        diccionario['ctrd'] = '-'.join(l1[:-2])
        diccionario['clt'] = '-'.join(l1[-2::])
    else:
        diccionario['ctrd'] = '-'.join(l1[:-1])
        diccionario['clt'] = l1[-1]

    return diccionario


def verifica_fecha(fbal, fecha_d):
    '''
    Recibe UN archivo de Balance y una fecha y verifica si se puede
    calcular el valor decadico para la fecha indicada
    '''
    dateparse = lambda x: dt.datetime.strptime(x, '%d/%m/%Y')
    df = pd.read_csv(fbal, sep=';', decimal=',',
                     parse_dates=['Fecha'], date_format='%d/%m/%Y',
                     encoding='ISO-8859-1')
    # Renomobramos las columnas
    df.columns = ['Fecha', 'ALM', 'ETR', 'ETC', 'AU', 'ED', 'EA']
    fe_d = df.Fecha
    yr = fecha_d.year
    mo = fecha_d.month
    dev_valor = False
    if fecha_d.day == 1:
        i1 = np.logical_and(fe_d >= dt.datetime(yr, mo, 1),
                            fe_d <= dt.datetime(yr, mo, 10))
        conteos = np.sum(i1)
        if conteos == 10:
            dev_valor = True

    elif fecha_d.day == 11:
        i1 = np.logical_and(fe_d >= dt.datetime(yr,mo,11),
                            fe_d <= dt.datetime(yr,mo,20))
        conteos = np.sum(i1)
        if conteos == 10:
            dev_valor = True
    elif fecha_d.day == 21:
        u_day = calendar.monthrange(yr, mo)[1]

        i1 = np.logical_and(fe_d >= dt.datetime(yr,mo,21),
                            fe_d <= dt.datetime(yr,mo,u_day))
        conteos = np.sum(i1)
        ind_feb0 = np.logical_and(mo == 2, u_day == 28)
        ind_feb1 = np.logical_and(mo == 2, u_day == 29)
        if (u_day == 30 and conteos == 10):
            dev_valor = True
        elif (u_day == 31 and conteos == 11):
            dev_valor = True
        elif (ind_feb0 and conteos == 8):
            print('Febrero No Bisiesto')
            dev_valor = True
        elif (ind_feb1 and conteos == 9):
            print('Febrero Bisiesto')
            dev_valor = True

    return dev_valor


def sum_wgt_table(Resumen, nctr, ntotal):
    """
    Funcion para sumar
    """
    pesos = [valor/ntotal for valor in nctr]
    arr_out = np.zeros(Resumen.shape[0])
    for ic, column in enumerate(Resumen):
        if column != 'Fecha':
            arr_out = arr_out + Resumen[column].values * pesos[ic - 1]

    return arr_out


def get_df_deca(df_val, fecha_col):
    '''
    A partir deL DataFrame de valores diarios, calcula un DataFrame
    con las medias decadiales.
    En este caso, se calculan
    '''
    # Agrupamos y calculamos media y conteo de valores usados en la media
    df1 = df_val.groupby('i_deca').mean()  # Media por decada dias
    df2 = df_val.groupby('i_deca').count()  # Conteo de datos
    # Agrupamos en un nuevo DataFrame
    col = ['i_deca', 'AU', 'c_AU']  # Nombre de columnas
    list_of_series = [df1.index, df1.AU, df2.AU]  # Datos a considerar
    deca = pd.DataFrame({'AU':df1.AU, 'c_AU':df2.AU})
    deca = deca.assign(f_deca=fecha_col)  # Nueva columna con la fecha inicial
    #deca.to_excel('./prueba2.xlsx')
    if (deca['c_AU'].iloc[-1] < 10 and deca['f_deca'].iloc[-1].month != 2):
        # Si el ultimo no tiene la decada completa, NO se incluye!
        deca.drop(deca.tail(1).index, inplace=True)
    elif (deca['c_AU'].iloc[-1] < 8 and deca['f_deca'].iloc[-1].month == 2):
        deca.drop(deca.tail(1).index, inplace=True)
    # No hacer nada en caso que estos casos no se cumplan
    #print(deca)
    cols_to_convert = ['AU', 'c_AU']
    deca[cols_to_convert] = deca[cols_to_convert].apply(pd.to_numeric, errors='coerce')
    #deca = deca.apply(pd.to_numeric, errors='ignore')

    #
    return deca


def get_file_deca(decafiles, d_c, centroide):
    '''
    Obtiene string con nombre de archivo de centroide de medias decadiales
    '''
    if d_c['clt'] == 'TL':
            ndecafile1 = 'decadales_' + centroide + '_' + d_c['clt']
            ndecafile2 = 'decadales_' + centroide + '_' + 'TS(' + d_c['clt'] + ')'
            f_ctr = [s for s in decafiles
                     if ndecafile1 in s or ndecafile2 in s]
    elif d_c['clt'] == 'S2':
        ndecafile = 'decadales_' + centroide + '_' + 'TS(' + d_c['clt'] + ')'
        f_ctr = [s for s in decafiles if ndecafile in s]
    else:
        ndecafile = 'decadales_' + centroide + '_' + d_c['clt']
        f_ctr = [s for s in decafiles if ndecafile in s]
    #
    if f_ctr:
        return f_ctr[0]
    else:
        return ''

def gen_dataframe_depto(dic, deca_file):
    '''
    '''
    dateparse = lambda x: dt.datetime.strptime(x, '%Y-%m-%d')
    df = pd.read_csv(dic['decafolder'] + '/' + deca_file, sep=';', decimal=',',
                     parse_dates=['f_deca'], date_format='%Y-%m-%d',
                     encoding='ISO-8859-1')
    df_R = pd.DataFrame(index=np.arange(0, len(df)))
    # Supone que todos los archivos decadiales tienen el mismo largo!
    df_R = df_R.assign(Fecha=df['f_deca'])
    #
    return df_R

def get_points_per_centroide(df_s, item, ctrd, tipo):
    '''
    '''
    if tipo == 'departamento':
        df_c = df_s[np.logical_and(df_s['PRDPT'] == item,
                                   df_s['centroide'] == ctrd)]
        Cpt = df_c.sum()['DEPTO'] # Puntos del centroide en el depto
        #
    elif tipo == 'cuartel':
        df_c = df_s[np.logical_and(df_s['Distrito'] == item,
                                   df_s['centroide'] == ctrd)]
        Cpt = df_c.sum()['DEPTO'] # Puntos del centroide en el depto
        #
    return Cpt


def get_df_weights(df_R, nctr, ntotal):
    '''
    '''
    pesos = [valor/ntotal for valor in nctr]
    columnas = df_R.columns[1::]
    df_t = pd.DataFrame(columns=columnas,
                              index=['PESO', 'PTS_CTR', 'PTS_TOTAL'])
    df_t.loc[['PESO'], :] = pesos
    df_t.loc[['PTS_CTR'], :] = nctr
    df_t.loc[['PTS_TOTAL'], :] = ntotal*np.ones(len(columnas))
    #
    return df_t


def save_output_depto(dic, df_R, df_t, item, tipo):
    '''
    '''
    # Carpeta segun resolucion
    if dic['resol'] == '50':
        ofolder = dic['s50']
    elif dic['resol'] == '500':
        ofolder = dic['s500']
    # Nombre de archivo segun tipo de calculo: departamento o cuartel
    if tipo == 'departamento':
        name_file = ofolder + item + '_' + dic['clt'] + '.xlsx'
    elif tipo == 'cuartel':
        name_file = ofolder + item + '_' + dic['prov'] +\
                    '_' + dic['clt'] + '.xlsx'
    writer = pd.ExcelWriter(name_file, engine = 'openpyxl')
    df_R.to_excel(writer, float_format = '%.3f', sheet_name = 'Agua Util')
    df_t.to_excel(writer, sheet_name = 'PESOS')
    writer.close()
    #
    return name_file


def get_divpol_file(resol, ret_folder, ret_f50, ret_f500, tipo):
    if resol == '50':
        dp_file = ret_folder + ret_f50
        fdivpol = ret_folder + 'resumen_divpol_50.csv'
        dp = pd.read_csv(dp_file, sep=';', encoding='ISO-8859-1')
        pr_dp = dp['PROVINCIA'].values.squeeze() + '-' +\
                dp['DEPTO'].values.squeeze()
        dp = dp.assign(PRDPT=pr_dp)
        if tipo == 'cuartel':
            dp1 = dp.groupby(['Distrito', 'PRDPT','centroide']).count()
        elif tipo == 'departamento':
            dp1 = dp.groupby(['PRDPT','centroide']).count()
        else:
            print('ERROR colocaste un ' + tipo + ' que no existe')
            print('Actualmente son validos: departamento y cuartel')
        dp1.to_csv(fdivpol, sep=';')
    elif resol == '500':
        dp_file = ret_folder + ret_f500
        fdivpol = ret_folder + 'resumen_divpol_500.csv'
        dp = pd.read_csv(dp_file, sep=';', encoding='ISO-8859-1')
        dp.columns = ['COD_PROV', 'COD_DEPTO', 'LINK', 'DEPTO', 'PROVINCIA',
                      'centroide']
        pr_dp = dp['PROVINCIA'].values.squeeze() + '-' +\
                dp['DEPTO'].values.squeeze()
        dp = dp.assign(PRDPT=pr_dp)
        dp1 = dp.groupby(['PRDPT','centroide']).count()
        dp1.to_csv(fdivpol, sep=';')
    return fdivpol


def proccessing_decadal(lfiles, dic):
    """
    """
    dateparse = lambda x: dt.datetime.strptime(x, '%d/%m/%Y')
    f = open(dic['lfile'], 'a')
    for arc in lfiles:
        f.write('Trabajando en el archivo: ' + arc + '\n')
        # print(arc)
        bfile = dic['pfiles'] + arc
        df = pd.read_csv(bfile, sep=';', decimal=',',
                         parse_dates=['Fecha'], date_format='%d/%m/%Y',
                         encoding='ISO-8859-1')
        # Chequeamos que no este vacio y trabajamos con ese archivo:
        if df.empty:
            f.write('Archivo: ' + arc + ' NO TIENE DATOS! \n')
            print('Archivo: ' + arc + ' NO TIENE DATOS!')
        else:
            # Renomobramos las columnas
            df.columns = ['Fecha', 'ALM', 'ETR', 'ETC', 'AU', 'ED', 'EA']
            # Clasificamos los dias si pertenecen a cada decada.
            i_col, f_col = clas_decada(df.Fecha)
            df = df.assign(i_deca=i_col)
            # Obtenemos DataFrame con medias decadiales
            deca = get_df_deca(df, f_col) #[0:int(i_col[-1])]
            # Obtenemos datos de archivo (Centroide y Cultivo)
            f_d = get_file_data(arc)
            if f_d['clt'] != 'QUE':
            # Guardamos siempre que sepamos a que cultivo nos referimos:
                d_file = dic['decafolder'] + 'decadales_' + f_d['ctrd'] +\
                        '_' + f_d['clt']
                deca.to_csv(d_file + '.txt', sep=';', decimal=',', float_format='%.3f',
                            encoding='ISO-8859-1')
                # ----- LOGFILE -------
                f.write('Archivo con datos decadales: ' + d_file + '.txt \n')
                f.write('--------------------------------------------------\n')
                # ---------------------
            df = None
    # --- End of LOOP ------------------------
    f.write(' #######################################################################################\n')
    f.write(' ################ TERMINO CALCULO DE ARCHIVOS DECADIALES X CENTROIDE ###################\n')
    f.write(' #######################################################################################\n')
    f.close()


def processing_departamento(dic):
    """
    """
    f = open(dic['lfile'], 'a')
    f.write('Trabajando en archivos de division politica \n')
    div_pol = pd.read_csv(dic['divpol'], sep=';', encoding='ISO-8859-1')
    f.write('--------------------------------------------------\n')
    # ################################################
    # Read decadal files
    # ################################################
    dfiles = [i for i in os.listdir(dic['decafolder'])
              if os.path.isfile(os.path.join(dic['decafolder'], i))]
    # Get all Single DPTO
    departamentos = np.unique(div_pol['PRDPT'].values)
    print('#### Trabajando en ', len(departamentos), ' departamentos ####')
    # ################################################
    # Calculos por DEPARTAMENTO
    # Parametros para leer bien los distintos archivos
    # ################################################
    for depto in departamentos:
        f.write(u'Trabajando en el departamento: ' + depto + '\n')
        df_s = div_pol[div_pol['PRDPT'] == depto]
        centroides = np.unique(df_s['centroide'].values)
        # Generamos dataframe para resultado por departamento
        Resumen = gen_dataframe_depto(dic, dfiles[0])
        # Variables para el resumen
        npts = []
        N_PT = 0.
        for ctr in centroides:
            f.write(u'Trabajando en el centroide: ' + ctr + '\n')
            # Archivos decadales e.g: decadales_F100-30_3_TL
            deca_file_ctr = get_file_deca(dfiles, dic, ctr)
            if deca_file_ctr:
                if dic['debug']:
                    print(deca_file_ctr)
                # Vamos sumando para obtener el total de puntos
                Cpt = get_points_per_centroide(df_s, depto, ctr, 'departamento')
                N_PT = N_PT + Cpt # Total de puntos
                npts.append(Cpt)
                dateparse = lambda x: dt.datetime.strptime(x, '%Y-%m-%d')
                df_deca = pd.read_csv(dic['decafolder'] + '/' + deca_file_ctr,
                                      sep=';', decimal=',',
                                      parse_dates=['f_deca'],
                                      date_format='%Y-%m-%d',
                                      encoding='ISO-8859-1')
                ########### Guardamos la columna de valores decadicos ##########
                n_str = u'AU_' + ctr
                if ctr == u'CAÑUELAS':
                    n_str = 'AU_CANUELAS'
                kwargs = {n_str: df_deca.AU}
                Resumen = Resumen.assign(**kwargs)
                ####################################################################
            else:
                txt = u'No hay decadal para cultivo ' + dic['clt'] +\
                    ' en el centroide: ' + ctr + '\n'
                f.write(txt)
        # End LOOP en los centroides para el departamento
        if npts:  # Si se guardaron elementos en npts, calculamos los pesos:
            # Tabla de Pesos
            tabla_peso = get_df_weights(Resumen, npts, N_PT)
            # Calculamos columna con la SUMA y sus respectivos pesos
            Resumen = Resumen.assign(AU_WGT=sum_wgt_table(Resumen, npts, N_PT))
            cols = list(Resumen.columns.values)
            cols_new = [cols[0], cols[-1]]
            for ncol in cols[1:-1]:
                cols_new.append(ncol)
            Resumen = Resumen[cols_new]
            cols_to_convert = Resumen.columns[1:]
            Resumen[cols_to_convert] = Resumen[cols_to_convert].apply(pd.to_numeric, errors='coerce')
            # -------------------------------------------------------------
            nombre = save_output_depto(dic, Resumen, tabla_peso,
                                       depto, 'departamento')
            f.write(u'Archivo resumen por departamento en: ' + nombre + '\n')
            f.write('--------------------------------------------------\n')
        else:
            txt = u'No se cultiva ' + dic['clt'] +\
                ' departamento: ' + depto + '\n'
            f.write(txt)
            f.write('--------------------------------------------------\n')
    # End Loop en cada departamento
    f.close()


def processing_cuartel(dic):
    """
    """
    f = open(dic['lfile'], 'a')
    f.write('Trabajando en archivos de division politica \n')
    div_pol = pd.read_csv(dic['divpol'], sep=';', encoding='ISO-8859-1')
    f.write('--------------------------------------------------\n')
    # ################################################
    # Read decadal files
    # ################################################
    dfiles = [i for i in os.listdir(dic['decafolder'])
              if os.path.isfile(os.path.join(dic['decafolder'], i))]
    # Get all Single Distrito (o cuartel)
    cuartel = np.unique(np.unique(div_pol['Distrito'].values))
    print('#### Trabajando en ', len(cuartel), ' cuarteles ####')
    for item in cuartel:
        f.write(u'Trabajando en el Cuartel: ' + item + '\n')
        df_s = div_pol[div_pol['Distrito'] == item]
        prov = df_s['PRDPT'].iloc[0]
        centroides = np.unique(df_s['centroide'].values)
        # Generamos dataframe para resultado por departamento
        Resumen = gen_dataframe_depto(dic, dfiles[0])
        # Variables para el resumen
        npts = []
        N_PT = 0.
        for ctr in centroides:
            f.write('Trabajando en el centroide: ' + ctr + '\n')
            # Leemos el archivo decadal de centroide y cultivo
            deca_file_ctr = get_file_deca(dfiles, dic, ctr)
            if deca_file_ctr:
                if dic['debug']:
                    print(deca_file_ctr)
                # Vamos sumando para obtener el total de puntos
                Cpt = get_points_per_centroide(df_s, item, ctr, 'cuartel')
                N_PT = N_PT + Cpt # Total de puntos
                npts.append(Cpt)
                dateparse = lambda x: dt.datetime.strptime(x, '%Y-%m-%d')
                df_deca = pd.read_csv(dic['decafolder'] + '/' + deca_file_ctr,
                                      sep=';', decimal=',',
                                      parse_dates=['f_deca'],
                                      date_format='%Y-%m-%d')
                ########### Guardamos la columna de valores decadicos ##########
                n_str = 'AU_' + ctr
                kwargs = {n_str: df_deca.AU}
                Resumen = Resumen.assign(**kwargs)
                ################################################################
            else:
                txt = u'No hay decadal para cultivo ' + dic['clt'] +\
                    ' en el centroide: ' + ctr + '\n'
                f.write(txt)
            ###########
        # End LOOP for centroides
        # ################################################
        if npts:
            tabla_peso = get_df_weights(Resumen, npts, N_PT)
            # Calculamos columna con la SUMA y sus respectivos pesos
            Resumen = Resumen.assign(AU_WGT=sum_wgt_table(Resumen, npts, N_PT))
            cols = list(Resumen.columns.values)
            cols_new = [cols[0], cols[-1]]
            for ncol in cols[1:-1]:
                cols_new.append(ncol)
            Resumen = Resumen[cols_new]
            cols_to_convert = Resumen.columns[1:]
            Resumen[cols_to_convert] = Resumen[cols_to_convert].apply(pd.to_numeric, errors='coerce')
            # -------------------------------------------------------------
            dic['prov'] = prov
            nombre = save_output_depto(dic, Resumen, tabla_peso,
                                       item, 'cuartel')
            f.write('Archivo resumen por cuartel en: ' + nombre + '\n')
            f.write('--------------------------------------------------\n')
        else:
            txt = u'No se cultiva ' + dic['clt'] +\
                ' cuartel: ' + item + '\n'
            f.write(txt)
            f.write('--------------------------------------------------\n')
    f.close()
