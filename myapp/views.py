from django.shortcuts import render
from django.http import HttpResponse
import matplotlib.pyplot as plt
import io
import urllib, base64
import pandas as pd
import datetime as dt
from rest_framework.decorators import api_view


@api_view(['GET', 'POST'])
def Home(request):
    graphic = None
    if request.method == 'POST':
        ativo = request.POST.get('ativo')

        if ativo:
            # Dia 14
            plan1 = pd.read_excel("data_extract/2025-09-14.xlsx")
            plan1 = plan1[plan1['id'] == ativo]

            # Dia 15
            plan2 = pd.read_excel("data_extract/2025-09-15.xlsx")
            plan2 = plan2[plan2['id'] == ativo]

            if not plan1.empty and not plan2.empty:
                vl1 = int(plan1['price'].iloc[0])
                vl2 = int(plan2['price'].iloc[0])

                plt.figure(figsize=(6, 4))
                plt.plot([1, 2], [vl1, vl2], marker="o")
                plt.title(f"ARTIFICIAL INTELLIGENCE - PREDICTION FOR {ativo}")
                plt.xlabel("Dias")
                plt.ylabel("Preço")

                # Salvar em buffer
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                image_png = buffer.getvalue()
                buffer.close()

                # Converter em base64
                graphic = base64.b64encode(image_png).decode('utf-8')
    
    return render(request, 'index.html', {'graphic': graphic})