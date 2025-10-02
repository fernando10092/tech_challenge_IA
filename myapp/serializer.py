from rest_framework import serializers
from .models import Banco

class BancoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banco
        # Agora estamos serializando o 'ativo_id' que contém o ticker
        fields = ('ativo_id', 'price', 'close', 'status', 'data')
