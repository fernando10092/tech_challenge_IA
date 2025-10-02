from django.db import models

class Banco(models.Model):
    # ID interno automático
    id = models.AutoField(primary_key=True)
    # Ticker da Ação (usado para pesquisa e importação)
    ativo_id = models.CharField(max_length=10)
    price = models.FloatField()
    close = models.FloatField()
    status = models.CharField(max_length=10)
    data = models.DateField()

    class Meta:
        # Evita a duplicação do mesmo ativo no mesmo dia
        unique_together = ("ativo_id", "data")

    def __str__(self):
        return f"{self.ativo_id} - {self.data}"
