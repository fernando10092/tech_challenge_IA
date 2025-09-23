import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

def Ia_Prediction():
    """
    Carrega todos os dados históricos, treina o modelo de Regressão Logística,
    salva a acurácia e o relatório de classificação no objeto do modelo e o salva
    em um arquivo .pkl.
    """
    try:
        # 1. Carregar e concatenar todas as planilhas
        files = sorted([f for f in os.listdir("data_extract") if f.endswith(".xlsx")])
        if not files:
            print("Erro: Nenhum arquivo .xlsx encontrado para treinamento.")
            return

        all_dataframes = [pd.read_excel(os.path.join("data_extract", f)) for f in files]
        arquivo = pd.concat(all_dataframes, ignore_index=True)

        # 2. Pré-processamento dos dados
        # Mapeamento do status para valores numéricos, seguindo a lógica do scraper
        # 'gain' (variacao negativa) -> 1
        # 'loss' (variacao positiva) -> 0
        arquivo["status"] = arquivo["status"].map({"gain": 1, "loss": 0})

        # Transformar a data em número de dias para a IA.
        arquivo["data"] = pd.to_datetime(arquivo["data"])
        arquivo["data"] = (arquivo["data"] - arquivo["data"].min()).dt.days

        # Converter coluna "id" em variáveis dummy (one-hot encoding)
        arquivo = pd.get_dummies(arquivo, columns=["id"], drop_first=True)
        
        # 3. Treinamento do modelo
        x = arquivo.drop("status", axis=1)
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
        print("\nRelatório de Classificação:")
        print(classification_report(y_test, predict_class))

        # Salva a acurácia e o relatório como atributos do modelo antes de salvá-lo
        modelo.accuracy = acuracia
        modelo.classification_report_str = classification_report(y_test, predict_class)

        joblib.dump(modelo, 'myapp/models_ia/modelo_treinado.pkl')
        print("Arquivo 'modelo_treinado.pkl' salvo com sucesso!")

    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
        import traceback
        traceback.print_exc()

# Adicione a chamada para a função de treinamento aqui, se ainda não estiver presente
if __name__ == '__main__':
    Ia_Prediction()