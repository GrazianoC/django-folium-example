from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .models import EVChargingLocation
import random
from PIL import Image
from pillow_heif import register_heif_opener
from lat_lon_parser import parse
from geopy import geocoders


def get_exif(filename):
    image = Image.open(filename)
    image.verify()
    return image.getexif().get_ifd(0x8825)


def get_geotagging(exif):
    geo_tagging_info = {}
    if not exif:
        raise ValueError("No EXIF metadata found")
    else:
        gps_keys = ['GPSVersionID', 'GPSLatitudeRef', 'GPSLatitude', 'GPSLongitudeRef', 'GPSLongitude',
                    'GPSAltitudeRef', 'GPSAltitude', 'GPSTimeStamp', 'GPSSatellites', 'GPSStatus', 'GPSMeasureMode',
                    'GPSDOP', 'GPSSpeedRef', 'GPSSpeed', 'GPSTrackRef', 'GPSTrack', 'GPSImgDirectionRef',
                    'GPSImgDirection', 'GPSMapDatum', 'GPSDestLatitudeRef', 'GPSDestLatitude', 'GPSDestLongitudeRef',
                    'GPSDestLongitude', 'GPSDestBearingRef', 'GPSDestBearing', 'GPSDestDistanceRef', 'GPSDestDistance',
                    'GPSProcessingMethod', 'GPSAreaInformation', 'GPSDateStamp', 'GPSDifferential']

        for k, v in exif.items():
            try:
                geo_tagging_info[gps_keys[k]] = str(v)
            except IndexError:
                pass
        return geo_tagging_info

# Create your views here.
def index(request):
    punti = list (EVChargingLocation.objects.values())
    context = {'punti':punti}
    return render(request, 'index.html', context)

def upload(request):
    
    if request.method == 'POST' and request.FILES['photo']: 
        myfile = request.FILES['photo'] 
        print(request.POST.get('lat'))
        print(request.POST.get('lon'))
        fs = FileSystemStorage(location="media/images") 
        # print("--->")
        print(str(myfile))
        #carico solo le 3 tipologia di file jpg, heic e jpeg
        if (str(myfile)[-3:]).upper() =="JPG" or (str(myfile)[-4:]).upper() =="HEIC" or (str(myfile)[-4:]).upper() =="JPEG": 
            register_heif_opener() #carica il lettore di immagine heic
            
            filename = fs.save(myfile.name, myfile) ##salva il file nella cartella
            uploaded_file_url = fs.url(filename) 
            file_upload=uploaded_file_url.split("/")
            uploadfile=file_upload[1]+"/images/"+file_upload[2]
            
            image_info = get_exif(uploadfile) #estraggo le info della geolocalizzazione
            if request.POST.get('lat')=="": #se non leggo le coordinate da browser
            
             if not image_info: #se non leggo le info exif
               context = {'errore':'No EXIF metadata found or no gps found from browser' }
               print ("-------->No EXIF metadata found",myfile.name)
               return render(request, 'upload.html', context)
             else: #Se leggo le exif queste hanno priorità rispetto alle coordinae del browser
              results = get_geotagging(image_info)
              print (results)

              #conversione coordinate da formato gradi a decimale
              lat= ((results["GPSLatitude"][1:-1]).split(", "))
              latd= ((lat[0]+"° "+lat[1]+"' "+lat[2]+"\" "+results["GPSLatitudeRef"] ))
              lata= (parse(latd))
              lon= ((results["GPSLongitude"][1:-1]).split(", "))
              lond= ((lon[0]+"° "+lon[1]+"' "+lon[2]+"\" "+results["GPSLongitudeRef"] ))
              lona= (parse(lond))
            else: #altrimenti prendo per buone quelle del browser
              lata=request.POST.get('lat')
              lona=request.POST.get('lon')

                #cerco indirizzo da coordinate
            geolocator = geocoders.Nominatim(user_agent="foodwaste")     #cos'era user agent?
            location = geolocator.reverse(str(lata) +", "+ str(lona))
            print(location.address)	
               #Salvo i dati 
            f = EVChargingLocation.objects.create(
              station_name="Prova"+str(random.random()), 
              latitude=lata, 
              longitude=lona,  
              address = location.address, 
              image=uploadfile)
            f.save()
           
            
            return redirect('index')
        else: #se non è un jpeg, heic, jpg allora ritorno alla pagina di caricamento
            print (request.FILES['photo'])
            return redirect('index')
    else: #se non mi trovo nel metodo post allora visualizzo la pagina di caricameto
        
        context = {}
        return render(request, 'upload.html', context)