import requests
import pandas as pd
import datetime as dt

date = str(dt.datetime.now().date())

response = requests.get("https://ledev.com.br/api/cotacoes")

response = list(response.json())

data = []

for i, dados in enumerate(response):
    variacao = float(response[i]["close"]) - float(response[i]["price"])
    recomendacao = 0
    if variacao >= 0:
        recomendacao = "gain"
    else:
        recomendacao = "loss"
    data.append({"id":response[i]["id"],"price":response[i]["price"], "close":response[i]["close"], "status": recomendacao,"data": date})


frame = pd.DataFrame(data)

arquivo = frame.to_excel(f"data_extract/{date}.xlsx", index=False)
arquivo = frame.to_parquet(f"data_extract/{date}.parquet", index=False)

print(arquivo)