import requests
import pandas as pd
import datetime as dt
import os
from myapp.models import Banco

def Scraper():
    """
    Função principal do Scraper que busca dados, salva no banco de dados e em arquivos.
    """
    date = str(dt.datetime.now().date())
    print(f"Executando Scraper para data: {date}")

    try:
        response = requests.get("https://ledev.com.br/api/cotacoes")
        stocks_data = response.json()
    except requests.RequestException as e:
        print(f"Erro ao buscar dados da API: {e}")
        return # Use return em vez de exit() dentro de uma função chamada por uma view

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

            # Salva no banco de dados (A versão que você queria usar)
            banco = Banco(
                id=dados["id"],
                price=dados["price"],
                close=dados["close"],
                status=recomendacao,
                data=date
            )
            banco.save()
            # O print está aqui para debug, mas pode ser removido em produção
            # print(f"Dados salvos no banco de dados: {banco}") 
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