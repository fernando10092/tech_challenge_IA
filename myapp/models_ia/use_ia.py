import joblib
import numpy as np
import pandas as pd
import datetime as dt

# Carrega o modelo treinado
modelo = joblib.load('modelo_treinado.pkl')

def Predict(ativo_id, data_dias):
    """
    Realiza a predição para um ativo específico de forma otimizada.
    Args:
        ativo_id (str): O ID do ativo (ex: "ABEV3").
        data_dias (int): A data em dias desde a data de referência do treino.
    Returns:
        int: A predição (1 para gain, 0 para loss).
    """
    # 1. Carregar a lista de IDs do arquivo de treino.
    treino_df = pd.read_excel("data_extract/2025-09-14.xlsx")
    todos_os_ids = sorted(treino_df['id'].unique())
    
    # 2. Criar um DataFrame com todas as colunas necessárias de uma só vez.
    #    Começa com a coluna 'data' e adiciona todas as colunas dummy.
    #    O `reindex` já lida com a ordem das colunas e preenche com 0.
    colunas = ['data'] + [f'id_{i}' for i in todos_os_ids if i != todos_os_ids[0]]
    
    # 3. Criar uma linha de dados com o formato correto.
    linha_dados = [data_dias]
    
    # Encontrar a posição do ativo_id na lista ordenada de IDs
    try:
        idx_ativo = todos_os_ids.index(ativo_id)
        # O one-hot encoding para o ativo de entrada
        if idx_ativo > 0:
            # Se o ativo não é o primeiro da lista, o dummy correspondente é 1.
            # Os demais são 0.
            ativo_vector = [0] * (len(colunas) - 1)
            ativo_vector[idx_ativo - 1] = 1
            linha_dados += ativo_vector
        else:
            # Se o ativo é o primeiro, todas as colunas dummy são 0 (drop_first).
            linha_dados += [0] * (len(colunas) - 1)

    except ValueError:
        # Lidar com ativos que não estavam no conjunto de treino.
        print(f"Aviso: O ativo {ativo_id} não estava no conjunto de dados de treino.")
        return None # Ou algum outro valor padrão

    # 4. Criar o DataFrame final para a predição.
    data_input = pd.DataFrame([linha_dados], columns=colunas)

    # Reordena as colunas para a mesma ordem do treino, garantindo compatibilidade
    data_input = data_input.reindex(columns=modelo.feature_names_in_, fill_value=0)

    # Realiza a predição
    prediction = modelo.predict(data_input)
    
    return prediction[0]

# Exemplo de uso
data_de_previsao = (dt.datetime.now().date() - dt.datetime.strptime('2025-09-14', '%Y-%m-%d').date()).days
previsao_abev3 = Predict("ABEV3", data_de_previsao)

if previsao_abev3 is not None:
    print(f"Previsão para ABEV3 em {dt.datetime.now().date()}: {'Gain' if previsao_abev3 == 1 else 'Loss'}")
else:
    print("Não foi possível fazer a previsão para ABEV3.")