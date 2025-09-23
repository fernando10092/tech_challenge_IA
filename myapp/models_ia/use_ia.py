import joblib
import numpy as np
import pandas as pd
import datetime as dt
import os

# Carrega o modelo treinado uma única vez na inicialização do servidor.
# Isso garante que a predição seja rápida.
try:
    modelo = joblib.load('modelo_treinado.pkl')
except FileNotFoundError:
    print("Erro: O arquivo 'modelo_treinado.pkl' não foi encontrado. Por favor, execute o script de treinamento primeiro.")
    modelo = None

def Predict(ativo_id, data_dias):
    if modelo is None:
        return None
    
    # Carregar a lista de IDs do arquivo de treino.
    files = sorted([f for f in os.listdir("data_extract") if f.endswith(".xlsx")])
    if not files:
        print("Erro: Nenhum arquivo .xlsx encontrado para obter a lista de IDs.")
        return None

    # Lê apenas um arquivo para obter todos os IDs únicos usados no treinamento
    treino_df = pd.read_excel(os.path.join("data_extract", files[0]))
    todos_os_ids = sorted(treino_df['id'].unique())
    
    # 1. Preparar o input para o modelo, recriando as colunas dummy
    colunas = ['data'] + [f'id_{i}' for i in todos_os_ids if i != todos_os_ids[0]]
    
    # Cria uma linha de dados com o formato correto.
    linha_dados = [data_dias]
    
    # Preenche o vetor com zeros para as colunas dummy.
    # O tamanho é o total de colunas - 1 (a coluna 'data').
    ativo_vector = [0] * (len(colunas) - 1)
    
    try:
        idx_ativo = todos_os_ids.index(ativo_id)
        # Se o ativo não é o primeiro da lista, define a posição correspondente para 1.
        if idx_ativo > 0:
            ativo_vector[idx_ativo - 1] = 1
    except ValueError:
        print(f"Aviso: O ativo {ativo_id} não estava no conjunto de dados de treino.")
        return None

    linha_dados += ativo_vector
    data_input = pd.DataFrame([linha_dados], columns=colunas)

    # Reordena as colunas para a mesma ordem do treino, garantindo compatibilidade
    data_input = data_input.reindex(columns=modelo.feature_names_in_, fill_value=0)

    # Realiza a predição. O resultado é 0 para 'loss' e 1 para 'gain'.
    prediction = modelo.predict(data_input)
    
    return prediction[0]