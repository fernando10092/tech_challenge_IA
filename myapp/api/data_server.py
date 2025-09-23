import pandas as pd
import os

def Server():
    """
    Carrega todos os arquivos .xlsx do diretório 'data_extract'
    e retorna uma lista de DataFrames.
    """
    dataframes = []
    # Usamos o 'sorted' para garantir que os arquivos sejam lidos na ordem correta
    for filename in sorted(os.listdir("data_extract")):
        if filename.endswith(".xlsx"):
            filepath = os.path.join("data_extract", filename)
            df = pd.read_excel(filepath)
            dataframes.append(df)
    return dataframes