from django.db import models

# Create your models here.
class EVChargingLocation(models.Model):
    station_name = models.CharField(max_length=250)
    latitude = models.FloatField(null=True, blank=True, default=None)
    longitude = models.FloatField(null=True, blank=True, default=None)
    address = models.TextField(null=True, blank=True, default=None)
    image = models.ImageField(upload_to="images/", null=True, blank = True)

    def __str__(self):
        return self.station_name