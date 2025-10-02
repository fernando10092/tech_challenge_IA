import requests
import pandas as pd
import datetime as dt
import os
from myapp.models import Banco

def Scraper():
    """
    Função principal do Scraper que busca dados, salva no banco de dados e em arquivos.
    Usa update_or_create para evitar o erro de UNIQUE constraint failed.
    """
    date = str(dt.datetime.now().date())
    print(f"Executando Scraper para data: {date}")

    try:
        response = requests.get("https://ledev.com.br/api/cotacoes")
        stocks_data = response.json()
    except requests.RequestException as e:
        print(f"Erro ao buscar dados da API: {e}")
        return 

    data = []

    for dados in stocks_data:
        try:
            variacao = float(dados["close"]) - float(dados["price"])
            recomendacao = "gain" if variacao < 0 else "loss"
            
            # Estrutura para salvar nos arquivos Excel/Parquet
            data.append({
                "id": dados["id"],
                "price": dados["price"],
                "close": dados["close"],
                "status": recomendacao,
                "data": date
            })

            # --- CORREÇÃO: USAR update_or_create para evitar o erro UNIQUE constraint failed ---
            # Se o registro (ativo_id + data) existir, ele atualiza os defaults (price, close, status).
            # Se não existir, ele cria um novo.
            Banco.objects.update_or_create(
                ativo_id=dados["id"],
                data=date,
                defaults={
                    'price': dados["price"],
                    'close': dados["close"],
                    'status': recomendacao
                }
            )

        except (KeyError, ValueError, Exception) as e:
            # Captura qualquer erro no processamento de dados ou DB
            print(f"Aviso: Dados incompletos ou inválidos para um ativo ({dados.get('id', 'N/A')}). Erro: {e}")
            continue

    frame = pd.DataFrame(data)

    if not os.path.exists("data_extract"):
        os.makedirs("data_extract")

    excel_file = f"data_extract/{date}.xlsx"
    parquet_file = f"data_extract/{date}.parquet"

    frame.to_excel(excel_file, index=False)
    frame.to_parquet(parquet_file, index=False)

    print(f"Dados salvos com sucesso em arquivos: {excel_file} e {parquet_file}")
