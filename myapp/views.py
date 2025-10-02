import io
import base64
import datetime as dt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates # Importação adicionada para formatação de data
import pandas as pd
import os

from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .scraper.b3 import Scraper
from .serializer import BancoSerializer
from .models import Banco
# IMPORTANTE: Adicionando Ia_Prediction para retreinamento após download
from .models_ia.use_ia import Predict, get_model_performance, Ia_Prediction 
from .api.data_server import Server

# --- VIEWS ---

@api_view(['GET', 'POST'])
def Home(request):
    """
    Exibe a página principal com o gráfico histórico + previsão.
    """
    graphic = None
    prediction_result = None
    ativo = None
    predicted_price = None
    model_accuracy = get_model_performance()
    not_found = False

    # Pega todos os registros salvos no BD (necessário para calcular a data base de treino)
    banco = Banco.objects.all()
    serializer = BancoSerializer(banco, many=True)
    data_list = serializer.data  # lista de dicts com todos os dados

    if request.method == 'POST':
        ativo = (request.POST.get('ativo') or "").strip()

        if ativo:
            # Filtrar os registros usando o campo 'ativo_id'
            registros_ativo = [
                r for r in data_list
                if str(r.get('ativo_id', '')).upper().strip() == ativo.upper().strip()
            ]

            if not registros_ativo:
                not_found = True
            else:
                # converte cada registro para {'data': datetime, 'preco': float}
                dados_para_grafico = []
                for r in registros_ativo:
                    try:
                        data_obj = pd.to_datetime(r.get('data'))
                        # Certifica que o preço é um float
                        preco = float(r.get('price'))
                        dados_para_grafico.append({'data': data_obj, 'preco': preco})
                    except Exception:
                        # pula registros inválidos
                        continue

                # ordena pela data (do mais antigo ao mais recente)
                dados_para_grafico = sorted(dados_para_grafico, key=lambda x: x['data'])

                if dados_para_grafico:
                    # determina data base de treino: usa o menor dia disponível entre todos os registros do BD
                    try:
                        todas_datas = [pd.to_datetime(r.get('data')) for r in data_list if r.get('data')]
                        # Usa a data mínima real do BD, se disponível
                        data_de_treino_base = min(todas_datas).date() if todas_datas else dt.date(2025, 9, 14)
                    except Exception:
                        data_de_treino_base = dt.date(2025, 9, 14)

                    data_de_hoje = dt.datetime.now().date()
                    dias_desde_treino = (data_de_hoje - data_de_treino_base).days
                    if dias_desde_treino < 0:
                        dias_desde_treino = 0

                    
                    # 1. Extrai o último registro completo para obter o preço e o fechamento
                    ultimo_registro_completo = registros_ativo[-1]
                    
                    # 2. Prepara os argumentos para a IA (price e close)
                    # 'ultimo_preco' já é o último 'price' (preço de abertura/atual)
                    ultimo_preco = dados_para_grafico[-1]['preco'] 
                    
                    # 3. Assume que 'close' é o fechamento do dia (campo 'close' do DB)
                    try:
                        # Assumindo que o campo 'close' existe no serializer/DB
                        ultimo_close = float(ultimo_registro_completo.get('close'))
                    except (ValueError, TypeError, KeyError):
                        # Caso 'close' não exista ou seja inválido, usa 'price' como fallback
                        print(f"Aviso: Campo 'close' inválido ou ausente no último registro para {ativo}. Usando 'price' como fallback.")
                        ultimo_close = ultimo_preco # Fallback
                    
                    # Chama a função de predição (CORRIGIDO: Passando ativo_id, price e close)
                    prediction_result = Predict(ativo.upper().strip(), ultimo_preco, ultimo_close)

                    # calcula preço previsto baseado no último preço disponível
                    porcentagem_variacao = 0.03
                    if prediction_result == 1:
                        predicted_price = ultimo_preco * (1 + porcentagem_variacao)
                    elif prediction_result == 0:
                        predicted_price = ultimo_preco * (1 - porcentagem_variacao)
                    else:
                        predicted_price = None

                    # adiciona ponto de previsão no dia seguinte (somente se houver predicted_price)
                    if predicted_price is not None:
                        data_prevista = dados_para_grafico[-1]['data'] + dt.timedelta(days=1)
                        dados_para_grafico.append({'data': data_prevista, 'preco': predicted_price, 'previsao': True})

                    # monta gráfico com datas (linha do tempo)
                    plt.figure(figsize=(10, 5))
                    datas_historico = [d['data'] for d in dados_para_grafico if 'previsao' not in d]
                    precos_historico = [d['preco'] for d in dados_para_grafico if 'previsao' not in d]
                    plt.plot(datas_historico, precos_historico, marker='o', linestyle='-', label='Histórico')

                    # ponto previsão (se existir)
                    if dados_para_grafico and 'previsao' in dados_para_grafico[-1]:
                        ponto_previsao = dados_para_grafico[-1]
                        plt.plot(ponto_previsao['data'], ponto_previsao['preco'], marker='*', markersize=12, color='red', label='Previsão')

                    # --- CORREÇÃO DE FORMATAÇÃO DE DATA DO GRÁFICO ---
                    ax = plt.gca() # Pega o eixo atual
                    # Define o formato como Dia/Mês (ex: 01/10)
                    date_form = mdates.DateFormatter('%d/%m')
                    ax.xaxis.set_major_formatter(date_form)
                    # Força a exibição de um tick para cada dia com dados
                    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                    # --- FIM DA CORREÇÃO ---


                    plt.title(f"HISTÓRICO E PREVISÃO DE PREÇOS - {ativo.upper()}")
                    plt.xlabel("Data")
                    plt.ylabel("Preço")
                    plt.grid(True)
                    plt.legend()
                    plt.xticks(rotation=45)
                    plt.tight_layout()

                    # salva imagem em buffer e converte para base64
                    buffer = io.BytesIO()
                    plt.savefig(buffer, format='png', bbox_inches='tight')
                    buffer.seek(0)
                    image_png = buffer.getvalue()
                    buffer.close()
                    plt.clf()

                    graphic = base64.b64encode(image_png).decode('utf-8')

    # renderiza template com contexto
    return render(request, 'index.html', {
        'graphic': graphic,
        'prediction_result': prediction_result,
        'ativo': ativo,
        'model_accuracy': model_accuracy,
        'predicted_price': predicted_price,
        'not_found': not_found
    })


@api_view(['GET', 'POST'])
def Server_View(request):
    """
    Roda a função Server() (sua API interna) e retorna uma estrutura serializável.
    """
    try:
        dados = Server()
        dados_dict = []
        for df in dados:
            try:
                # Converte o DataFrame para lista de dicionários
                dados_dict.append(df.to_dict('records'))
            except Exception:
                # se já for dicts/listas, adiciona direto
                dados_dict.append(df)
        return Response({"dados": dados_dict})
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['POST', 'GET'])
def Download(request):
    """
    Executa o Scraper para baixar dados e salvar, e DEPOIS retreina a IA,
    e por fim redireciona para home.
    """
    try:
        # 1. Executa o Scraper para atualizar os dados em 'data_extract'
        Scraper()
        
        # 2. Retreina o modelo de IA com os dados recém-coletados.
        # Isso atualiza o arquivo 'modelo_treinado.pkl'.
        Ia_Prediction()
        
    except Exception as e:
        # registra erro no console do servidor
        print(f"Erro ao executar Scraper/Treinamento: {e}")
    
    # 3. Redireciona para home
    return redirect('home')


@api_view(['GET'])
def DB_View(request):
    """
    Retorna todos os registros do BD.
    """
    banco = Banco.objects.all()
    serializer = BancoSerializer(banco, many=True)
    return Response(serializer.data, status=200)


@api_view(['GET', 'POST'])
def Teste_View(request):
    banco = Banco.objects.all()
    serializer = BancoSerializer(banco, many=True)
    print(serializer.data)
    return Response({"message": "Dados impressos no console do servidor."}, status=200)
