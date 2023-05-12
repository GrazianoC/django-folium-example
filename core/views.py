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
    context = {}
    return render(request, 'index.html', context)

def upload(request):
    
    if request.method == 'POST' and request.FILES['photo']:
        myfile = request.FILES['photo']
        
        fs = FileSystemStorage(location="media/images")
        # print("--->")
        print(str(myfile))
        if (str(myfile)[-3:]).upper() =="JPG" or (str(myfile)[-4:]).upper() =="HEIC": 
            register_heif_opener()
            print ("-------->",myfile.name)
            filename = fs.save(myfile.name, myfile)
            uploaded_file_url = fs.url(filename)
            file_upload=uploaded_file_url.split("/")
            uploadfile=file_upload[1]+"/images/"+file_upload[2]
            
            image_info = get_exif(uploadfile) #estraggo le info della geolocalizzazione
            if not image_info:
               context = {'errore':'No EXIF metadata found' }
               return render(request, 'upload.html', context)
            else:
             results = get_geotagging(image_info)
             print (results)

             #conversione coordinate da formato gradi a decimale
             lat= ((results["GPSLatitude"][1:-1]).split(", "))
             latd= ((lat[0]+"° "+lat[1]+"' "+lat[2]+"\" "+results["GPSLatitudeRef"] ))
             lata= (parse(latd))
             lon= ((results["GPSLongitude"][1:-1]).split(", "))
             lond= ((lon[0]+"° "+lon[1]+"' "+lon[2]+"\" "+results["GPSLongitudeRef"] ))
             lona= (parse(lond))
             

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
        else:
            print (request.FILES['photo'])
            return redirect('index')
    else:
        
        context = {}
        return render(request, 'upload.html', context)