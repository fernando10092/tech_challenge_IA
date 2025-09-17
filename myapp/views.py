from django.shortcuts import render
from django.http import HttpResponse
import matplotlib.pyplot as plt
import io
import urllib, base64
import pandas as pd
import datetime as dt
from rest_framework.decorators import api_view
# Importa a função de predição do seu script de IA
from .models_ia.use_ia import Predict

import matplotlib
matplotlib.use('Agg') # This line must be added before importing pyplot

# ... (imports) ...

# ... (imports) ...

@api_view(['GET', 'POST'])
def Home(request):
    graphic = None
    prediction_result = None
    ativo = None

    if request.method == 'POST':
        ativo = request.POST.get('ativo')

        if ativo:
            # 1. Carregar os dados dos 3 dias e filtrar pelo ativo
            try:
                plan1 = pd.read_excel("data_extract/2025-09-14.xlsx")
                plan2 = pd.read_excel("data_extract/2025-09-15.xlsx")
                plan3 = pd.read_excel("data_extract/2025-09-16.xlsx")
            except FileNotFoundError:
                # Se um arquivo não for encontrado, a lista de dados estará vazia.
                return render(request, 'index.html', {
                    'graphic': None,
                    'prediction_result': "Erro: Arquivos de dados não encontrados.",
                    'ativo': ativo
                })

            data_frames = [plan1, plan2, plan3]
            dados_para_grafico = []

            # 2. Iterar sobre os DataFrames e coletar os dados válidos
            for i, df in enumerate(data_frames):
                df_ativo = df[df['id'] == ativo]
                if not df_ativo.empty:
                    # Coleta o preço do ativo, o dia do mês e a data completa.
                    dia = 14 + i
                    preco = int(df_ativo['price'].iloc[0])
                    dados_para_grafico.append({'dia': dia, 'preco': preco})

            # 3. Gerar o gráfico apenas se houver dados para plotar
            if len(dados_para_grafico) >= 2: # Precisa de pelo menos 2 pontos para uma linha
                dias = [d['dia'] for d in dados_para_grafico]
                precos = [d['preco'] for d in dados_para_grafico]

                plt.figure(figsize=(6, 4))
                plt.plot(dias, precos, marker="o")
                plt.title(f"HISTÓRICO DE PREÇOS - {ativo}")
                plt.xlabel("Dia de Setembro")
                plt.ylabel("Preço")
                plt.grid(True) # Adiciona uma grade para melhor visualização

                buffer = io.BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                image_png = buffer.getvalue()
                buffer.close()

                graphic = base64.b64encode(image_png).decode('utf-8')

            # Chama a função de predição da IA
            data_de_hoje = dt.datetime.now().date()
            data_de_treino_base = dt.datetime.strptime('2025-09-14', '%Y-%m-%d').date()
            dias_desde_treino = (data_de_hoje - data_de_treino_base).days
            
            prediction_result = Predict(ativo, dias_desde_treino)

    return render(request, 'index.html', {
        'graphic': graphic,
        'prediction_result': prediction_result,
        'ativo': ativo
    })