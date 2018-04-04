from flask import Flask
from flask import request
from flask import abort
from flask import jsonify
import requests
import json

app = Flask(__name__)
user_agent = "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0"
referer = "http://www.folloren.no/"
origin = "http://www.folloren.no"
municipality = "213"
app_key = "AE13DEEC-804F-4615-A74E-B4FAC11F0A30"


def get_search(string):

    main_url = "https://services.webatlas.no/GISLINE.Web.Services.Search.SOLR3.0/Service.svc/json/addressWeighted"
    weighted_municipality = "0%s" % municipality
    client_id = "Android-Renovasjon-0%s" % municipality

    url = "%s?searchString=%s" \
          "&municipality=%s" \
          "&weightedMunicipality=%s" \
          "&firstIndex=0" \
          "&maxNoOfResults=20" \
          "&language=NO" \
          "&coordsys=84" \
          "&clientID=%s" % (main_url, string, municipality, weighted_municipality, client_id)

    host = "services.webatlas.no"
    accept = "application/json, text/javascript, */*; q=0.01"
    headers = {
        "Host": host,
        "User-Agent": user_agent,
        "Origin": origin,
        "Referer": referer,
        "Accept": accept
    }

    return json.loads(requests.get(url, headers=headers).text)


def get_dates(road_name, road_code, house):

    host = "norkartrenovasjon.azurewebsites.net"
    main_url = "https://norkartrenovasjon.azurewebsites.net/proxyserver.ashx"
    server_arg = "https://komteksky.norkart.no/komtek.renovasjonwebapi/api/tommekalender/"

    url = "%s?server=%s" \
          "?kommunenr=%s" \
          "&gatenavn=%s" \
          "&gatekode=%s" \
          "&husnr=%s" % (main_url, server_arg, municipality, road_name, road_code, house)

    headers = {
        "Host": host,
        "User-Agent": user_agent,
        "Origin": origin,
        "Referer": referer,
        "RenovasjonAppKey": app_key,
        "Kommunenr": municipality
    }

    return json.loads(requests.get(url, headers=headers).text)


def enrich_data(data):

    main_url = "https://norkartrenovasjon.azurewebsites.net/proxyserver.ashx"
    server_arg = "https://komteksky.norkart.no/komtek.renovasjonwebapi/api/fraksjoner/"
    host = "norkartrenovasjon.azurewebsites.net"

    url = "%s?server=%s" % (main_url, server_arg)

    headers = {
        "Host": host,
        "User-Agent": user_agent,
        "Origin": origin,
        "Referer": referer,
        "RenovasjonAppKey": app_key,
        "Kommunenr": municipality
    }

    metadata = json.loads(requests.get(url, headers=headers).text)
    for idx, elem in enumerate(data):
        elem_id = elem["FraksjonId"]
        for meta in metadata:
            meta_id = meta["Id"]
            if elem_id == meta_id:
                trash_type = meta["Navn"]
                data[idx]["Avfallstype"] = trash_type

    return data


@app.route("/", methods=['GET'])
def hello():
    query = request.args.get('query', '')

    if not query:
        abort(400)

    search_data = get_search(query)
    road_code = search_data["AddressSearchResult"]["Roads"][0]["Id"]
    road_name = search_data["AddressSearchResult"]["Roads"][0]["RoadName"]
    house = search_data["AddressSearchResult"]["Roads"][0]["Addresses"][0]["House"]

    data = get_dates(road_name, road_code, house)
    enriched = enrich_data(data)
    return jsonify(enriched)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
