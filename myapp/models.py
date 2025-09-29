from django.db import models

class Banco(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    price = models.FloatField()
    close = models.FloatField()
    status = models.CharField(max_length=10)
    data = models.DateField()

    def __str__(self):
        return self.id
