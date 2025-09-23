from django.shortcuts import render
from django.http import HttpResponse
import matplotlib.pyplot as plt
import io
import urllib, base64
import pandas as pd
import datetime as dt
from rest_framework.decorators import api_view
from .models_ia.use_ia import Predict
import matplotlib
from .api.data_server import Server
from rest_framework.response import Response
from .models_ia.linear_regression import Ia_Prediction

matplotlib.use('Agg')

@api_view(['GET', 'POST'])
def Home(request):
    graphic = None
    prediction_result = None
    ativo = None

    data_list = Server()

    if request.method == 'POST':
        ativo = request.POST.get('ativo')

        if ativo:
            dados_para_grafico = []
            
            for df in data_list:
                df_ativo = df[df['id'] == ativo]
                if not df_ativo.empty:
                    data_obj = pd.to_datetime(df_ativo['data'].iloc[0])
                    dia = data_obj.day
                    preco = float(df_ativo['price'].iloc[0])
                    dados_para_grafico.append({'dia': dia, 'preco': preco})

            if len(dados_para_grafico) >= 2:
                dias = [d['dia'] for d in dados_para_grafico]
                precos = [d['preco'] for d in dados_para_grafico]

                plt.figure(figsize=(6, 4))
                plt.plot(dias, precos, marker="o")
                plt.title(f"HISTÓRICO DE PREÇOS - {ativo.upper()}")
                plt.xlabel("Dia do Mês")
                plt.ylabel("Preço")
                plt.grid(True)
                plt.xticks(dias)
                
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                image_png = buffer.getvalue()
                buffer.close()
                plt.clf()

                graphic = base64.b64encode(image_png).decode('utf-8')

            data_de_hoje = dt.datetime.now().date()
            data_de_treino_base = pd.to_datetime(data_list[0]['data'].iloc[0]).date()
            dias_desde_treino = (data_de_hoje - data_de_treino_base).days
            
            if dias_desde_treino < 0:
                 dias_desde_treino = 0

            prediction_result = Predict(ativo, dias_desde_treino)

    return render(request, 'index.html', {
        'graphic': graphic,
        'prediction_result': prediction_result,
        'ativo': ativo
    })
    
@api_view(['GET', 'POST'])
def Server_View(request):
    dados = Server()
    dados_dict = [df.to_dict('records') for df in dados]
    return Response({"dados": dados_dict})
    
# Esta view está duplicada e não está sendo usada, pode ser removida se não for necessária
@api_view(['GET', 'POST'])
def Server_View(request):
    dados = Server()
    # A resposta deve ser serializável (lista de dicionários)
    # Convertendo os DataFrames para dicionários
    dados_dict = [df.to_dict('records') for df in dados]
    return Response({"dados": dados_dict})