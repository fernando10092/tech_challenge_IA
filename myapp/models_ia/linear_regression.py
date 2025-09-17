import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import seaborn as sns
import joblib


def Ia_Prediction():
    # Carregar planilha
    arquivo = pd.read_excel("data_extract/2025-09-14.xlsx")

    # Converter coluna "data" para datetime
    arquivo["data"] = pd.to_datetime(arquivo["data"])

    # Transformar data em número (ex: dias desde a primeira data)
    arquivo["data"] = (arquivo["data"] - arquivo["data"].min()).dt.days

    # One-Hot Encoding para id
    arquivo = pd.get_dummies(arquivo, columns=["id"], drop_first=True)

    # Codificar status (target)
    arquivo["status"] = arquivo["status"].map({"gain": 1, "loss": 0})

    # Features e target
    x = arquivo.drop("status", axis=1)
    y = arquivo["status"]

    # Treino e teste
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=42)

    # Modelo de classificação
    modelo = LogisticRegression(max_iter=1000)
    modelo.fit(x_train, y_train)

    # Predição
    predict_class = modelo.predict(x_test)

    # Avaliação
    acuracia = accuracy_score(y_test, predict_class)
    print(f"Acurácia: {acuracia:.2%}")
    print("\nRelatório de Classificação:")
    print(classification_report(y_test, predict_class))

    # Salvar o modelo treinado para uso posterior
    joblib.dump(modelo, 'modelo_treinado.pkl')

   
Ia_Prediction()