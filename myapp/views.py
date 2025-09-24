import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import io
import base64
import urllib
import matplotlib
import requests
import os
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect  
from django.http import HttpResponse

from .models_ia.use_ia import Predict, get_model_performance
from .api.data_server import Server

matplotlib.use('Agg')

@api_view(['GET', 'POST'])
def Home(request):
    graphic = None
    prediction_result = None
    ativo = None
    predicted_price = None
    model_accuracy = get_model_performance()

    data_list = Server()

    if request.method == 'POST':
        ativo = request.POST.get('ativo')

        if ativo:
            dados_para_grafico = []
            
            for df in data_list:
                df_ativo = df[df['id'] == ativo.upper().strip()] 
                if not df_ativo.empty:
                    data_obj = pd.to_datetime(df_ativo['data'].iloc[0])
                    dia = data_obj.day
                    preco = float(df_ativo['price'].iloc[0])
                    dados_para_grafico.append({'dia': dia, 'preco': preco})

            data_de_hoje = dt.datetime.now().date()
            if data_list:
                data_de_treino_base = pd.to_datetime(data_list[0]['data'].iloc[0]).date()
            else:
                data_de_treino_base = dt.datetime.strptime('2025-09-14', '%Y-%m-%d').date()
            
            dias_desde_treino = (data_de_hoje - data_de_treino_base).days
            if dias_desde_treino < 0:
                 dias_desde_treino = 0

            prediction_result = Predict(ativo.upper().strip(), dias_desde_treino)

            if len(dados_para_grafico) >= 1 and prediction_result is not None:
                ultimo_preco = dados_para_grafico[-1]['preco']
                
                porcentagem_variacao = 0.03
                if prediction_result == 1:
                    predicted_price = ultimo_preco * (1 + porcentagem_variacao)
                else:
                    predicted_price = ultimo_preco * (1 - porcentagem_variacao)
                    
                dia_previsto = dados_para_grafico[-1]['dia'] + 1
                dados_para_grafico.append({'dia': dia_previsto, 'preco': predicted_price, 'previsao': True})


                dias = [d['dia'] for d in dados_para_grafico]
                precos = [d['preco'] for d in dados_para_grafico]

                plt.figure(figsize=(6, 4))
                
                dias_historico = [d['dia'] for d in dados_para_grafico if 'previsao' not in d]
                precos_historico = [d['preco'] for d in dados_para_grafico if 'previsao' not in d]
                plt.plot(dias_historico, precos_historico, marker="o", color='blue', label='Histórico')
                
                ponto_previsao = dados_para_grafico[-1]
                plt.plot(ponto_previsao['dia'], ponto_previsao['preco'], marker="*", color='red', markersize=12, label='Previsão')
                
                plt.title(f"HISTÓRICO E PREVISÃO DE PREÇOS - {ativo.upper()}")
                plt.xlabel("Dia do Mês")
                plt.ylabel("Preço")
                plt.grid(True)
                plt.xticks(sorted(list(set(dias)))) 
                plt.legend()
                
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                image_png = buffer.getvalue()
                buffer.close()
                plt.clf()

                graphic = base64.b64encode(image_png).decode('utf-8')

    return render(request, 'index.html', {
        'graphic': graphic,
        'prediction_result': prediction_result,
        'ativo': ativo,
        'model_accuracy': model_accuracy,
        'predicted_price': predicted_price
    })
    
@api_view(['GET', 'POST'])
def Server_View(request):
    dados = Server()
    dados_dict = [df.to_dict('records') for df in dados]
    return Response({"dados": dados_dict})


@api_view(['POST'])
def Download(request):
    Scraper()
    return redirect('home')
    
def Scraper():
    date = str(dt.datetime.now().date())

    try:
        response = requests.get("https://ledev.com.br/api/cotacoes")
        stocks_data = response.json()
    except requests.RequestException as e:
        print(f"Erro ao buscar dados da API: {e}")
        exit()

    data = []

    for dados in stocks_data:
        try:
            variacao = float(dados["close"]) - float(dados["price"])
            recomendacao = "gain" if variacao < 0 else "loss"
            
            data.append({
                "id": dados["id"],
                "price": dados["price"],
                "close": dados["close"],
                "status": recomendacao,
                "data": date
            })
        except (KeyError, ValueError) as e:
            print(f"Aviso: Dados incompletos ou inválidos para um ativo. Pulando... Erro: {e}")
            continue

    frame = pd.DataFrame(data)

    if not os.path.exists("data_extract"):
        os.makedirs("data_extract")

    excel_file = f"data_extract/{date}.xlsx"
    parquet_file = f"data_extract/{date}.parquet"

    frame.to_excel(excel_file, index=False)
    frame.to_parquet(parquet_file, index=False)

    print(f"Dados salvos com sucesso em: {excel_file} e {parquet_file}")