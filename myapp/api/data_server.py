import pandas as pd
import os

lista = []
def Server():
    for i, dados in enumerate(os.listdir("data_extract")):
        if dados.endswith(".xlsx"):
            arquivo = pd.read_excel(f"data_extract/{dados}")
            lista.append(arquivo)
    return lista

Server()