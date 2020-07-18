import os
import openpyxl as opxl
import numpy as np
import pandas as pd
from itertools import islice


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