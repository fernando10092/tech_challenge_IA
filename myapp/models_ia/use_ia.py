import joblib
import numpy as np
import pandas as pd
import datetime as dt
import os

# Carrega o modelo treinado uma única vez na inicialização do módulo.
try:
    _modelo_ia_global = joblib.load('myapp/models_ia/modelo_treinado.pkl')
except FileNotFoundError:
    print("Erro: O arquivo 'modelo_treinado.pkl' não foi encontrado. Por favor, execute o script de treinamento primeiro.")
    _modelo_ia_global = None

def get_model_performance():
    """
    Retorna a acurácia do modelo de IA carregado.
    """
    if _modelo_ia_global and hasattr(_modelo_ia_global, 'accuracy'):
        return _modelo_ia_global.accuracy
    return None

def Predict(ativo_id, data_dias):
    """
    Realiza a predição para um ativo específico de forma otimizada.
    Args:
        ativo_id (str): O ID do ativo (ex: "ABEV3").
        data_dias (int): A data em dias desde a data de referência do treino.
    Returns:
        int: A predição (1 para gain, 0 para loss), ou None se houver erro.
    """
    if _modelo_ia_global is None:
        return None
    
    # Carregar a lista de IDs do arquivo de treino (do primeiro arquivo encontrado).
    files = sorted([f for f in os.listdir("data_extract") if f.endswith(".xlsx")])
    if not files:
        print("Erro: Nenhum arquivo .xlsx encontrado para obter a lista de IDs.")
        return None

    # Lê apenas o primeiro arquivo para obter todos os IDs únicos usados no treinamento
    # Isso assume que todos os arquivos têm o mesmo conjunto de IDs para One-Hot Encoding
    treino_df = pd.read_excel(os.path.join("data_extract", files[0]))
    todos_os_ids = sorted(treino_df['id'].unique())
    
    # 1. Preparar o input para o modelo, recriando as colunas dummy
    colunas = ['data'] + [f'id_{i}' for i in todos_os_ids if i != todos_os_ids[0]]
    
    # Cria uma linha de dados com o formato correto.
    linha_dados = [data_dias]
    
    # Preenche o vetor com zeros para as colunas dummy.
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
    data_input = data_input.reindex(columns=_modelo_ia_global.feature_names_in_, fill_value=0)

    # Realiza a predição. O resultado é 0 para 'loss' e 1 para 'gain'.
    prediction = _modelo_ia_global.predict(data_input)
    
    return prediction[0]

# --- Exemplo de uso (apenas para teste direto do script use_ia.py) ---
if __name__ == "__main__":
    # Certifique-se de que Ia_Prediction() foi executado pelo menos uma vez
    # para criar 'modelo_treinado.pkl' antes de rodar este bloco.
    data_de_previsao = (dt.datetime.now().date() - dt.datetime.strptime('2025-09-14', '%Y-%m-%d').date()).days
    previsao_ativo = Predict("WEST3", data_de_previsao) # Altere "WEST3" para um ativo existente nos seus dados
    
    if previsao_ativo is not None:
        print(f"Previsão para WEST3 em {dt.datetime.now().date()}: {'Gain' if previsao_ativo == 1 else 'Loss'}")
    else:
        print("Não foi possível fazer a previsão.")

    acuracia_modelo = get_model_performance()
    if acuracia_modelo is not None:
        print(f"Acurácia do modelo: {acuracia_modelo:.2%}")
    else:
        print("Não foi possível obter a acurácia do modelo.")