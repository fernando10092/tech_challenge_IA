import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import io
import base64
import urllib
import matplotlib
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render
from django.http import HttpResponse

from .models_ia.use_ia import Predict, get_model_performance
from .api.data_server import Server

matplotlib.use('Agg')

@api_view(['GET', 'POST'])
def Home(request):
    graphic = None
    prediction_result = None
    ativo = None
    predicted_price = None  # Adicione esta variável
    model_accuracy = get_model_performance() # Carrega a acurácia do modelo uma vez

    data_list = Server()

    if request.method == 'POST':
        ativo = request.POST.get('ativo')

        if ativo:
            # Lógica para gerar o gráfico
            dados_para_grafico = []
            
            for df in data_list:
                df_ativo = df[df['id'] == ativo.upper().strip()] # Normaliza a entrada do usuário
                if not df_ativo.empty:
                    data_obj = pd.to_datetime(df_ativo['data'].iloc[0])
                    dia = data_obj.day
                    preco = float(df_ativo['price'].iloc[0])
                    dados_para_grafico.append({'dia': dia, 'preco': preco})

            # Chama a função de predição antes de gerar o gráfico
            data_de_hoje = dt.datetime.now().date()
            if data_list: # Garante que há dados para pegar a data de treino base
                data_de_treino_base = pd.to_datetime(data_list[0]['data'].iloc[0]).date()
            else: # Caso não haja arquivos de dados, use uma data padrão
                data_de_treino_base = dt.datetime.strptime('2025-09-14', '%Y-%m-%d').date() # Data de referência
            
            dias_desde_treino = (data_de_hoje - data_de_treino_base).days
            if dias_desde_treino < 0:
                 dias_desde_treino = 0

            prediction_result = Predict(ativo.upper().strip(), dias_desde_treino) # Normaliza a entrada

            if len(dados_para_grafico) >= 1 and prediction_result is not None: # Precisa de pelo menos 1 ponto e uma previsão
                # Adiciona o ponto de previsão ao gráfico
                ultimo_preco = dados_para_grafico[-1]['preco']
                
                # Para visualização, assume uma variação percentual para a previsão
                porcentagem_variacao = 0.03 # Exemplo: 3% de variação para o gráfico
                if prediction_result == 1: # GAIN
                    predicted_price = ultimo_preco * (1 + porcentagem_variacao)
                else: # LOSS
                    predicted_price = ultimo_preco * (1 - porcentagem_variacao)
                    
                dia_previsto = dados_para_grafico[-1]['dia'] + 1
                dados_para_grafico.append({'dia': dia_previsto, 'preco': predicted_price, 'previsao': True})


                dias = [d['dia'] for d in dados_para_grafico]
                precos = [d['preco'] for d in dados_para_grafico]

                plt.figure(figsize=(6, 4))
                
                # Plota a linha do histórico de preços
                dias_historico = [d['dia'] for d in dados_para_grafico if 'previsao' not in d]
                precos_historico = [d['preco'] for d in dados_para_grafico if 'previsao' not in d]
                plt.plot(dias_historico, precos_historico, marker="o", color='blue', label='Histórico')
                
                # Plota o ponto de previsão
                ponto_previsao = dados_para_grafico[-1]
                plt.plot(ponto_previsao['dia'], ponto_previsao['preco'], marker="*", color='red', markersize=12, label='Previsão')
                
                plt.title(f"HISTÓRICO E PREVISÃO DE PREÇOS - {ativo.upper()}")
                plt.xlabel("Dia do Mês")
                plt.ylabel("Preço")
                plt.grid(True)
                # Ajusta os ticks do eixo X para incluir o dia previsto
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
        'model_accuracy': model_accuracy, # Passa a acurácia para o template
        'predicted_price': predicted_price # Passa o valor previsto
    })
    
@api_view(['GET', 'POST'])
def Server_View(request):
    dados = Server()
    dados_dict = [df.to_dict('records') for df in dados]
    return Response({"dados": dados_dict})
