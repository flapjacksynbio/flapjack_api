import os
import openpyxl as opxl
import numpy as np
import pandas as pd
from itertools import islice
from .models import *


def synergy_get_signal_names(ws):
    """
    Params
    - ws: openpyxl worksheet object
    Returns
    - signals: List with the signal names
    """
    # first column as Cell objects
    first_col = ws['A']
    # first column as values
    first_col_arr = np.array([c.value for c in first_col])
    # index where signals information starts
    start_index = np.where(first_col_arr=='End Kinetic')[0][0]
    # obtain signals names, including the "Result" cell, if exists
    signal_names = [val for val in first_col_arr[start_index+1:] if val != None]
    return signal_names


def synergy_rows_list(ws, signal_names):
    """
    Params
    - ws: openpyxl worksheet object
    - signal_names: name given to the signal by the user, i.e., "CFP"
    Returns
    - rows: list of tuples, each containing ('signal', signal_row_position)
    """
    rows = [(celda.value, celda.row)
                  for celda in ws['A']
                  if celda.value in signal_names]
    return rows


def synergy_clean_data(signal_names, df, rows):
    """
    Params
    - signal_names: name given to the signal by the user, i.e., "CFP"
    - df: DataFrame containg all data from sheet
    - rows: list of tuples, each containing ('signal', signal_row_position)
    Returs
    - dfs: DataFrame cleaned of data which are not part of the measurements
    """
    dfs = {}
    for i in range(len(rows)):
        if i == 0:
            df2 = pd.DataFrame(df.iloc[0:rows[i][1] - 3])
        else:
            df2 = pd.DataFrame(df.iloc[rows[i-1][1] + 1:rows[i][1] - 3])
        synergy_fix_time(df2)
        df2.index = range(len(df2['Time']))
        dfs[signal_names[i]] = df2
    return dfs


# Changes time's format from datetime to fraction
def synergy_fix_time(df):
    t = np.array([])
    for i, value in enumerate(df['Time']):
        try:
            t = np.append(t, value.day*24 + value.hour + value.minute/60 + value.second/3600)
        except:
            t = np.append(t, value.hour + value.minute/60 + value.second/3600)
    df['Time'] = t


def get_all_tables(ws, columns):
    length = len(ws['A'])
    ntables = (length + 1) // 10
    table_list = []
    names_list = []
    for i in range(ntables):
        name,values = table_values(ws, i*10+1, columns)
        table_list.append(values)
        names_list.append(name)
    return names_list, table_list


def table_values(ws, row, columns):
    name = ws[row][0].value
    vals = []
    for cell_row in range(row + 1, row + 9):
        for cell_col in range (1, 13):
            val = ws[cell_row][cell_col].value
            if not val:
                vals.append(0)
            else:
                vals.append(val)
    return name, dict(zip(columns, vals))


def synergy_load_data(ws, signal_names, signal_map):
    rows_ini = synergy_rows_list(ws, signal_names)
    ws.delete_rows(0, rows_ini[0][1] + 1)
    rows = synergy_rows_list(ws, signal_names)
    data = ws.values
    cols = next(data)[1:]
    data = list(data)
    data = (islice(r, 1, None) for r in data)
    df = pd.DataFrame(data, columns=cols)

    names = [signal_map[rows_ini[i][0]] for i in range(len(rows_ini)-1)]
    dfs = synergy_clean_data(names, df, rows)
    return dfs


def synergy_load_meta(wb, columns):
    meta_dict = {}
    ws_names = ['Strains', 'Media', 'DNA', 'Inducers']
    for ws_name in ws_names:
        if ws_name in ['Strains', 'Media']:
            name, dict_ws = table_values(wb[ws_name], 1, columns)
            meta_dict[name] = dict_ws
        elif ws_name == 'DNA':
            names, dicts_ws = get_all_tables(wb[ws_name], columns)
            for i in range(len(names)):
                meta_dict[names[i]] = dicts_ws[i]
        elif ws_name == 'Inducers':
            if 'Inducers' in wb.sheetnames:
                names, dicts_ws = get_all_tables(wb[ws_name], columns)
                for i in range(len(names)):
                    meta_dict[names[i]+' conc'] = dicts_ws[i]
    return pd.DataFrame(meta_dict).transpose()


def upload_data(assay_id, meta_dict, dfs, dna_map):
    print(f"assay_id: {assay_id}")
    columns = list(meta_dict.columns)
    meta_dnas = [k for k in list(meta_dict.index) if 'DNA' in k]
    meta_inds = [k for k in list(meta_dict.index) if 'conc' in k]
    for well_idx, well in enumerate(columns):
        existing_dna = [i.names for i in Dna.objects.all()]
        existing_med = [i.name for i in Media.objects.all()]
        existing_str = [i.name for i in Strain.objects.all()]
        existing_ind = [(i.names, i.concentrations) for i in Inducer.objects.all()]

        # Metadata value for each well (sample): strain and media
        s_media = meta_dict.loc['Media'][well]
        s_strain = meta_dict.loc['Strains'][well]

        if s_media.upper() != 'NONE':
            if s_media not in existing_med:
                media = Media(name=s_media, description='')
                media.save()
            else:
                media = Media.objects.filter(name__exact=s_media)[0]

            if s_strain not in existing_str:
                strain = Strain(name=s_strain, description='')
                strain.save()
            else:
                strain = Strain.objects.filter(name__exact=s_strain)[0]

            dnas = []
            for meta_dna in meta_dnas:
                s_dna = meta_dict.loc[meta_dna][well]
                dnas.append(s_dna)
            # Get unique DNA names
            dnas = list(set(dnas))
            # If we have a real DNA, remove the 'None's
            if len(dnas)>1 and 'None' in dnas:
                dnas.remove('None')

            dnas.sort()

            # When dna_map = {} (all dnas already in DB), no dna_map[dna] to get
            # BUg: When dnas = ['None] error
            try:
                sboluris = [dna_map[dna] for dna in dnas]
            except:
                sboluris = []

            if dnas not in existing_dna:
                d = Dna(names=dnas, sboluris=sboluris)
                d.save()
            else:
                d = Dna.objects.filter(names__exact=dnas)[0]


            if len(meta_inds) > 0:
                inds = [ind.split(' ')[0] for ind in meta_inds]
                concs = [meta_dict.loc[meta_ind][well] for meta_ind in meta_inds]
                concs = list(map(float, concs))
                # Removes not present inducers
                ind_non_zero = np.where(np.array(concs) != 0.)
                inds = list(np.array(inds)[ind_non_zero])
                concs = [float(c) for c in list(np.array(concs)[ind_non_zero])]

                if (inds, concs) not in existing_ind:
                    i = Inducer(names=inds, concentrations=concs)
                    i.save()
                else:
                    i = Inducer.objects.filter(names__exact=inds).filter(concentrations__exact=concs)[0]
            else:
                if ([], []) not in existing_ind:
                    i = Inducer(names=[], concentrations=[])
                    i.save()
                else:
                    i = Inducer.objects.filter(names__exact=[]).filter(concentrations__exact=[])[0]

            s = Sample(assay=Assay.objects.get(id=assay_id), media=media, strain=strain, dna=d, inducer=i, row=well[0], col=well[1:])
            s.save()


            # status update
            #process_percent = (96*file_idx+(well_idx+1))/(96*files_number)
            #current_task.update_state(state=process_percent)


            # Data value for each well
            measurements = []
            for key, dfm in dfs.items():
                for i, value in enumerate(dfm[well]):
                    signal = Signal.objects.get(name=key)
                    #m_name = key
                    m_value = value
                    m_time = dfm['Time'].iloc[i]
                    m = Measurement(sample=s, signal=signal, value=m_value, time=m_time)
                    measurements.append(m)
            Measurement.objects.bulk_create(measurements)

        else:
            print("I'm None")
