import pandas as pd
import numpy as np

guide_clt = ['A1', 'A2', 'G1', 'G2', 'M11', 'M12', 'M21', 'M22', 'S1', 'S2', 'TL', 'TC']
cultivos = ['A11', 'A12', 'G11', 'G12', 'M11', 'M12', 'M21', 'M22', 'S1', 'S2', 'TL', 'TS(TC)']

def change_col_clt(df):
    df0 = df.copy()
    for clt0, clt1 in zip(cultivos, guide_clt):
        df0.loc[df.Cultivo == clt0,'Cultivo'] = clt1
    return df0

def calc_AU(fdato, Se1, m_d):
    df0 = pd.read_excel(fdato, index_col=0)
    df01 = change_col_clt(df0)
    ix = df01.LINK == int(Se1['LINK'])
    df = df01.loc[ix,['AU_WGT', 'Cultivo']]
    cult = df.Cultivo.values
    val = df.AU_WGT.values
    Se2 = Se1.copy()
    Se2[cult] = val
    sf = Se2[guide_clt]
    # Chequeamos si se hace el cultivo en la decada
    #ind_clt = pd.read_csv('./clt_indicador.csv', sep=';', index_col='clt_c')
    archivo_indicador = './clt_indicador.csv'
    ind_clt = pd.read_csv(archivo_indicador, sep=';', index_col='clt_c')
    se_hace = ind_clt.loc[guide_clt,m_d].to_numpy()
    if np.sum(se_hace == 0) > 0:
        icult = se_hace == 0
        sf.iloc[icult] = -998
    # Chequeamos si el cultivo se hace en el departamento
    or_val = Se1[guide_clt].to_numpy()
    if np.sum(or_val == -999) > 0:
        sf.iloc[or_val == -999] = -999
    '''
    # Chequear si quedo algun dato faltante
    if np.sum(sf.to_numpy() == 1) > 0:
        if Se1['DEPTO'] == 'FRAY JUSTO SANTA MARIA DE ORO':
            print('Trabajando en: ', Se1['PROVINCIA'], Se1['DEPTO'])
            print(u'Cultivos que se hacen en el departamento y década pero estan sin datos: ')
            print(u'Decada: ', m_d)
            print(sf.iloc[sf.to_numpy() == 1].index.values)
            print(sf)
            print(df)
            exit()
        sf.iloc[sf.to_numpy() == 1] = -1001
    '''
    return sf.to_numpy()

def calc_AnomAU_diff(fdato, fmean, Se1, m_d):
    df0 = pd.read_excel(fdato, index_col=0)
    df01 = change_col_clt(df0)
    ix = df01.LINK == int(Se1['LINK'])
    df1 = df01.loc[ix,['AU_WGT', 'Cultivo']]
    df2 = df1.set_index('Cultivo')
    #
    Mean = pd.read_excel(fmean, index_col=0)
    Mean0 = change_col_clt(Mean)
    ix1 = (Mean0.LINK == int(Se1['LINK']))
    Mean1 = Mean0.loc[ix1, ['AU_WGT', 'Cultivo']]
    Mean2 = Mean1.set_index('Cultivo')
    #
    cult = df2.index.values
    val = df2.AU_WGT.values
    media = Mean2.loc[cult, 'AU_WGT'].values
    Se2 = Se1.copy()
    Se2[cult] = val - media
    sf = Se2[guide_clt]
    # Chequear si se hace el cultivo en la fecha
    #archivo_indicador = 'c:/Felix/ORA/python_scripts/AguaUtil_operativo/clt_indicador.csv'
    archivo_indicador = './clt_indicador.csv'
    ind_clt = pd.read_csv(archivo_indicador, sep=';', index_col='clt_c')
    se_hace = ind_clt.loc[guide_clt,m_d].to_numpy()
    if np.sum(se_hace == 0) > 0:
        icult = se_hace == 0
        sf.iloc[icult] = -998
    # Chequear si se hace el cultivo en el departamento
    or_val = Se1[guide_clt].to_numpy()
    if np.sum(or_val == -999) > 0:
        sf.iloc[or_val == -999] = -999
    '''
    # Chequear si quedo algun dato faltante
    if np.sum(sf.to_numpy() == 1) > 0:
        sf.iloc[sf.to_numpy() == 1] = -1001
    '''
    return sf.to_numpy()

def calc_AnomAU_std(fdato, fmean, fstd, Se1, m_d):
    df0 = pd.read_excel(fdato, index_col=0)
    df01 = change_col_clt(df0)
    ix = df01.LINK == int(Se1['LINK'])
    df1 = df01.loc[ix,['AU_WGT', 'Cultivo']]
    df2 = df1.set_index('Cultivo')
    #
    Mean = pd.read_excel(fmean, index_col=0)
    Mean0 = change_col_clt(Mean)
    ix1 = (Mean0.LINK == int(Se1['LINK']))
    Mean1 = Mean0.loc[ix1, ['AU_WGT', 'Cultivo']]
    Mean2 = Mean1.set_index('Cultivo')
    #
    Std = pd.read_excel(fstd, index_col=0)
    Std0 = change_col_clt(Std)
    ix1 = (Std0.LINK == int(Se1['LINK']))
    Std1 = Std0.loc[ix1, ['AU_WGT', 'Cultivo']]
    Std2 = Std1.set_index('Cultivo')
    #
    cult = df2.index.values
    val = df2.AU_WGT.values
    media = Mean2.loc[cult, 'AU_WGT'].values
    std = Std2.loc[cult, 'AU_WGT'].values
    Se2 = Se1.copy()
    Se2[cult] = (val - media)/std
    sf = Se2[guide_clt]
    # Chequear si se hace el cultivo en la fecha
    #archivo_indicador = 'c:/Felix/ORA/python_scripts/AguaUtil_operativo/clt_indicador.csv'
    archivo_indicador = './clt_indicador.csv'
    ind_clt = pd.read_csv(archivo_indicador, sep=';', index_col='clt_c')
    se_hace = ind_clt.loc[guide_clt,m_d].to_numpy()
    if np.sum(se_hace == 0) > 0:
        icult = se_hace == 0
        sf.iloc[icult] = -998
    # Chequeamos si se hace el cultivo en el depto
    or_val = Se1[guide_clt].to_numpy()
    if np.sum(or_val == -999) > 0:
        sf.iloc[or_val == -999] = -999
    '''
    # Chequear si quedo algun dato faltante
    if np.sum(sf.to_numpy() == 1) > 0:
        sf.iloc[sf.to_numpy() == 1] = -1001
    '''
    return sf.to_numpy()


def parse_config(file_path):
    import re
    config = {}
    with open(file_path, 'r') as file:
        for line in file:
            # Use regex to match the variable name and value
            match = re.match(r'(\w+)\s*=\s*"(.*)"', line.strip())
            if match:
                config[match.group(1)] = match.group(2)
    return config

def get_shapefile_AU(df, type_AU,
                     shapefile_loc='C:/Felix/ORA/Proyectos_ArcGIS/CAPAS_SIG/IGN/departamentoPolygon.shp',
                     outfolder = 'C:/Felix/ORA/Proyectos_ArcGIS/PublicacionDecadiales/'):
    '''
    This function get the dataframe from AU, AUdiff y AUsd
    and make the join with the department shapefile to get the shapefile
    to be used in the ArcGis project.
    '''    

    try:
        import geopandas as gpd
        print(f"The package 'geopandas' is installed.")
        gdf = gpd.read_file(shapefile_loc)
        merged_gdf = gdf.merge(df, left_on='link', right_on='LINK', how='right')
        merged_gdf = merged_gdf.drop(columns=['link'])
        print(merged_gdf.columns)
    
        if type_AU == 'AU':
            merged_gdf.to_file(outfolder + 'AU.shp')
            print('Archivo shapefile generado en:', outfolder + 'AU.shp' )
        elif type_AU == 'AU-AAdif':
            merged_gdf.to_file(outfolder + 'AU-AAdif.shp')
            print('Archivo shapefile generado en:', outfolder +  'AU-AAdif.shp')
        elif type_AU == 'AU-AAsd':
            merged_gdf.to_file(outfolder + 'AU-AAsd.shp')
            print('Archivo shapefile generado en:', outfolder +  'AU-AAsd.shp')
    except:
        print(f"The package 'geopandas' is not installed.")
        return []

    

    

    
