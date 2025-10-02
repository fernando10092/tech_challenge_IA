import joblib
import numpy as np
import pandas as pd
import datetime as dt
import os
import traceback 

# Dependências para Treinamento (Ia_Prediction)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# --- Variável Global para o Modelo ---

_modelo_ia_global = None
MODEL_FILE_PATH = 'myapp/models_ia/modelo_treinado.pkl'

try:
    _modelo_ia_global = joblib.load(MODEL_FILE_PATH)
    print("Modelo IA carregado com sucesso.")
except FileNotFoundError:
    print("Aviso: O arquivo 'modelo_treinado.pkl' não foi encontrado. Execute a ação 'Download' para treinar o modelo inicial.")
except Exception as e:
    print(f"Erro ao carregar modelo IA: {e}")


# --- Funções de Treinamento e Predição ---

def Ia_Prediction():
    """
    Carrega todos os dados históricos, treina o modelo de Regressão Logística,
    salva a acurácia no objeto do modelo, salva o modelo em um arquivo .pkl,
    e atualiza a variável global.
    """
    global _modelo_ia_global

    try:
        # 1. Carregar e concatenar todas as planilhas
        files = sorted([f for f in os.listdir("data_extract") if f.endswith(".xlsx")])
        if not files:
            print("Erro: Nenhum arquivo .xlsx encontrado para treinamento.")
            return

        all_dataframes = [pd.read_excel(os.path.join("data_extract", f)) for f in files]
        arquivo = pd.concat(all_dataframes, ignore_index=True)

        # 1.1 AJUSTE DE ROBUSTEZ: Renomeia 'id' para 'ativo_id' para padronizar.
        if 'id' in arquivo.columns:
            arquivo.rename(columns={'id': 'ativo_id'}, inplace=True)
            
        if 'ativo_id' not in arquivo.columns:
            print("Erro: Coluna 'ativo_id' essencial para o treinamento não encontrada.")
            return

        # 2. Pré-processamento dos dados
        arquivo["status"] = arquivo["status"].map({"gain": 1, "loss": 0})

        # --- MANTENDO A COLUNA 'data' PARA USO FUTURO, mas não como feature ---
        arquivo["data"] = pd.to_datetime(arquivo["data"])
        data_minima = arquivo["data"].min()
        # A coluna 'data' não será usada como feature (X), mas a lógica de dias é mantida para o Predict()
        arquivo["data_dias"] = (arquivo["data"] - data_minima).dt.days 

        # Converter coluna "ativo_id" em variáveis dummy (One-Hot Encoding)
        arquivo = pd.get_dummies(arquivo, columns=["ativo_id"], drop_first=True, prefix='ativo_id')
        
        # 3. Treinamento do modelo
        # DEFINIMOS AS COLUNAS A SEREM REMOVIDAS DO CONJUNTO DE FEATURES (X)
        # Removendo 'status' (target), 'data' (objeto datetime) e 'data_dias' (feature temporal não desejada)
        features_to_drop = ["status", "data", "data_dias"] 

        x = arquivo.drop(features_to_drop, axis=1, errors='ignore') 
        y = arquivo["status"]
        
        if len(x) < 2 or len(y) < 2:
            print("Aviso: Dados insuficientes para treinamento. Necessita de mais dados históricos.")
            return

        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=42)
        
        modelo = LogisticRegression(max_iter=1000)
        modelo.fit(x_train, y_train)

        # 4. Avaliação e salvamento
        predict_class = modelo.predict(x_test)
        acuracia = accuracy_score(y_test, predict_class)
        
        print(f"Modelo treinado com sucesso! Acurácia: {acuracia:.2%}")

        # Salva a acurácia como atributo do modelo
        modelo.accuracy = acuracia
        
        # Salva o modelo treinado no disco
        joblib.dump(modelo, MODEL_FILE_PATH)
        
        # --- DIAGNÓSTICO DE SALVAMENTO ---
        if os.path.exists(MODEL_FILE_PATH):
            file_mod_time = dt.datetime.fromtimestamp(os.path.getmtime(MODEL_FILE_PATH))
            print("----------------------------------------------------------------------")
            print(f"CONFIRMAÇÃO: Arquivo 'modelo_treinado.pkl' salvo e ATUALIZADO com sucesso!")
            print(f"Nova data/hora de modificação: {file_mod_time.strftime('%d/%m/%Y %H:%M:%S')}")
            print("----------------------------------------------------------------------")
        else:
            print(f"ERRO CRÍTICO: Falha ao salvar o arquivo PKL em {MODEL_FILE_PATH}. Verifique as permissões.")
        
        # ATUALIZA o objeto global após salvar para uso imediata
        _modelo_ia_global = modelo

    except Exception as e:
        print(f"Ocorreu um erro inesperado durante o treinamento da IA: {e}")
        traceback.print_exc()
        _modelo_ia_global = None


def get_model_performance():
    """
    Retorna a acurácia do modelo de IA carregado.
    """
    if _modelo_ia_global and hasattr(_modelo_ia_global, 'accuracy'):
        # Retorna formatado como porcentagem (ex: 95.00)
        return _modelo_ia_global.accuracy * 100
    return None

def Predict(ativo_id, price, close):
    """
    Realiza a predição para um ativo específico.
    O modelo agora se baseia apenas em 'price', 'close' e 'ativo_id'.
    """
    if _modelo_ia_global is None:
        print("Erro: Modelo de IA não está carregado. Não é possível prever.")
        return None
    
    try:
        colunas_modelo = _modelo_ia_global.feature_names_in_
    except AttributeError:
        print("Erro: Modelo carregado não possui 'feature_names_in_'. Modelo inválido.")
        return None

    # 1. Preparar o input para o modelo, preenchendo todos os recursos
    input_data = {col: 0 for col in colunas_modelo}
    
    # 2. Adicionar as features de preço e fechamento
    if 'price' in input_data:
        input_data['price'] = price
    if 'close' in input_data:
        input_data['close'] = close
    
    # 3. Preenche a coluna dummy correspondente
    ativo_coluna = f'ativo_id_{ativo_id}'
    
    if ativo_coluna in input_data:
        input_data[ativo_coluna] = 1
    
    # 4. Criar e reindexar o DataFrame de entrada
    data_input = pd.DataFrame([input_data])
    data_input = data_input.reindex(columns=colunas_modelo, fill_value=0)

    try:
        prediction = _modelo_ia_global.predict(data_input)
        return prediction[0]
    except Exception as e:
        print(f"Erro durante a predição: {e}")
        return None
