import requests
import pandas as pd
import datetime as dt
import os

# Obtém a data atual para nomear os arquivos de forma única.
date = str(dt.datetime.now().date())

try:
    # Faz a requisição GET para a API de cotações.
    response = requests.get("https://ledev.com.br/api/cotacoes")
    # Converte a resposta JSON em uma lista de dicionários.
    stocks_data = response.json()
except requests.RequestException as e:
    print(f"Erro ao buscar dados da API: {e}")
    # Encerra o script se não puder obter os dados.
    exit()

data = []

# Itera sobre os dados de cada ativo.
for dados in stocks_data:
    try:
        # Calcula a variação entre o preço de fechamento anterior e o preço atual.
        # Sua correção está aqui, a lógica está correta.
        variacao = float(dados["close"]) - float(dados["price"])
        
        # Atribui "loss" se o preço atual estiver abaixo ou igual ao anterior.
        # Atribui "gain" se o preço atual estiver acima do anterior.
        recomendacao = "gain" if variacao < 0 else "loss"
        
        # Adiciona os dados processados à lista.
        data.append({
            "id": dados["id"],
            "price": dados["price"],
            "close": dados["close"],
            "status": recomendacao,
            "data": date
        })
    except (KeyError, ValueError) as e:
        # Ignora linhas com dados ausentes ou inválidos.
        print(f"Aviso: Dados incompletos ou inválidos para um ativo. Pulando... Erro: {e}")
        continue

# Cria o DataFrame a partir da lista de dados processados.
frame = pd.DataFrame(data)

# Garante que o diretório 'data_extract' exista.
if not os.path.exists("data_extract"):
    os.makedirs("data_extract")

# Salva o DataFrame em arquivos Excel e Parquet.
excel_file = f"data_extract/{date}.xlsx"
parquet_file = f"data_extract/{date}.parquet"

frame.to_excel(excel_file, index=False)
frame.to_parquet(parquet_file, index=False)

print(f"Dados salvos com sucesso em: {excel_file} e {parquet_file}")