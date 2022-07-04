import base64
import json
import os
from datetime import datetime, timedelta
from functools import cache
from io import BytesIO
from typing import OrderedDict

import tekore as tk
from flask import Flask, render_template, request, send_from_directory
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'

app.wsgi_app = ProxyFix(app.wsgi_app)

cid = os.environ.get('SPOTIFY_CLIENT_ID')
secret = os.environ.get('SPOTIFY_SECRET')

#cred = tk.Credentials(client_id=cid,client_secret=secret,redirect_uri=redirect_uri,sender=None, asynchronous=None)
token = tk.request_client_token(cid, secret)
sp = tk.Spotify()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/privacy.html')
def privacy():
    return render_template('privacy.html')

@app.route('/about.html')
def about():
    return render_template('about.html')

@cache
def get_spotify_popularity(artist: str) -> int:
    search_results = sp.search(artist, types=('artist',), limit=1)[0]
    if not search_results.total:
        #Not even found on Spotify! HIPSTER VICTORY!!!!
        return -1
    if search_results.items[0].name != artist:
        #Unfortunately Spotify's API does not really let you do exact matches, you can put stuff in double quotes but it'll still return some other weird results sometimes
        #So if this is not returning the artist we asked for, it is not on Spotify, therefore HIPSTER VICTORY!!!!!
        return -1
    return search_results.items[0].popularity

def get_artist_playcount(term: timedelta=None) -> dict[str, int]:
    #Spotify /me/top/artists API: long_term = "several years of data", medium_term = last 6 months, short_term = last 4 weeks
    playcounts: dict[str, int] = {}
    playlog_file = request.files['playlog']
    playlog_file.seek(0)
    play_log = json.load(playlog_file)
    for track_path, track_info in play_log.items():
        artist = track_info.get('artist')
        if not artist:
            artist = track_path.rsplit('/', 3)[-3]
        if ', ' in artist or artist == 'Various Artists':
            continue
        for play in track_info['plays']:
            play_time = datetime.fromisoformat(play)
            if (not term) or ((datetime.now() - term) < play_time):
                if artist not in playcounts:
                    playcounts[artist] = 1
                else:
                    playcounts[artist] += 1

    return playcounts

@app.route('/berg.html', methods=['POST'])
def berg():
    with sp.token_as(token):
        ###CREATE ICEBERG

        name = request.form['name']
        
        artists = {}
        for term in [None, timedelta(days=30*6), timedelta(days=4 * 7)]:
            temp_artists = OrderedDict(sorted(get_artist_playcount(term).items(), key=lambda item: item[1])[:50])
            for artist in temp_artists.keys():
                artists[artist] = get_spotify_popularity(artist)

        # for term in ["long_term", "medium_term", "short_term"]:
        #     temp_artists = sp.current_user_top_artists(limit=50, offset=0, time_range=term)

        #     for artist in temp_artists.items:
        #         artists[artist.name] = artist.popularity

        sections: list[tuple[int, str]] = [(-1, 'hipster victory'), (16,'first'),(28,'second'),(40,'third'),(52,'fourth'),(64,'fifth'),(76,'sixth'),(88,'seventh'),(100,'eighth')]
        iceberg: dict[str, list[str]] = {'first':[], 'second':[], 'third':[], 'fourth':[], 'fifth':[], 'sixth':[], 'seventh':[], 'eighth':[], 'hipster victory': []}
        min_pop = 0
        for max_pop in sections:
            for artist, pop in artists.items():
                if pop == -1 and len(iceberg['hipster victory']) < 5:
                    iceberg['hipster victory'].append(artist)
                    continue
                if (pop <= max_pop[0]) and (pop > min_pop) and len(iceberg[max_pop[1]]) < 5:
                    iceberg[max_pop[1]].append(artist)
            min_pop = max_pop[0]

        ###DRAW ICEBERG
        for section, artists_in_section in iceberg.items():
            artists_sorted = (sorted(artists_in_section, key=len))
            artists_sorted.reverse()
            iceberg[section] = artists_sorted

        ###FONT WORK
        intro = ImageFont.truetype("Intro Regular Regular.ttf", 55)
        noto = ImageFont.truetype("NotoSans-Regular.ttf", 55)
        #korean = ImageFont.truetype("NotoSansKR-Regular.otf", 55)
        korean = ImageFont.truetype('NotoSansCJK-Regular.ttc', index=1)
        #japanese = ImageFont.truetype("rounded-mgenplus-1cp-regular.ttf", 55)
        japanese = ImageFont.truetype('NotoSansCJK-Regular.ttc', index=0)

        intro_ttf = TTFont('Intro Regular Regular.ttf')
        #noto_ttf = TTFont('NotoSans-Regular.ttf')
        noto_ttf = TTFont(noto.path)
        #korean_ttf = TTFont('NotoSansKR-Regular.otf')
        korean_ttf = TTFont(korean.path, fontNumber=1)
        #japanese_ttf = TTFont('rounded-mgenplus-1cp-regular.ttf')
        japanese_ttf = TTFont(japanese.path, fontNumber=0)

        def has_glyph(font, glyph):
            for table in font['cmap'].tables:
                if ord(glyph) in table.cmap.keys():
                    return True
            return False

        def print_artist(artist):
            count = 0
            for char in artist:
                if has_glyph(intro_ttf, char):
                    count += 1
            if count == len(artist):
                return(intro)
            
            count = 0
            for char in artist:
                if has_glyph(noto_ttf, char):
                    count += 1
            if count == len(artist):
                return(noto)

            count = 0
            for char in artist:
                if has_glyph(korean_ttf, char):
                    count += 1
            if count == len(artist):
                return(korean)

            count = 0
            for char in artist:
                if has_glyph(japanese_ttf, char):
                    count += 1
            if count == len(artist):
                return(japanese)
            
            return(intro)
        
        ###
        iceberg_img2 = Image.open("iceberg_blank2.jpg")
        image2 = ImageDraw.Draw(iceberg_img2)

        coordinates = {}
        coordinates['eighth'] = [[350, 335], [30,270], [640, 425], [150,415], [800,260]]
        if iceberg['hipster victory']:
            iceberg_img2_new = Image.new(iceberg_img2.mode, (iceberg_img2.width, iceberg_img2.height + 256))
            iceberg_img2_new.paste(iceberg_img2)
            iceberg_img2 = iceberg_img2_new
            image2 = ImageDraw.Draw(iceberg_img2)
        else:
            iceberg.pop('hipster victory')
            sections.pop(0)
        #for i in range(6,-1,-1):
        for i in range(7, -1, -1):
            if sections[i][1] != 'sixth':
                coordinates[sections[i][1]] = []
                for j in range(5):
                    coordinates[sections[i][1]].append([coordinates[sections[i+1][1]][j][0], coordinates[sections[i+1][1]][j][1] + 256])
            elif sections[i][1] == 'sixth':
                coordinates[sections[i][1]] = []
                for j in range(5):
                    coordinates[sections[i][1]].append([coordinates[sections[i+1][1]][j][0], coordinates[sections[i+1][1]][j][1] + 271])

        for section in sections:
            count = 0
            for artist in iceberg[section[1]]:
                image2.text(tuple(coordinates[section[1]][count]), artist, (230, 54, 41), print_artist(artist))
                count += 1

        ###TITLE
        intro_font_big = ImageFont.truetype("Intro Regular Regular.ttf", 100)
        image2.text((25, 20), name + "'s Not Spotify", (19, 81, 143), intro_font_big)
        image2.text((195, 120), "Iceberg", (19, 81, 143), intro_font_big)

        ###SAVING
        bytesio = BytesIO()
        iceberg_img2.save(bytesio, format='png')
        encoded = base64.b64encode(bytesio.getvalue()).decode('ascii')

    return render_template('berg.html', value=encoded, height=iceberg_img2.height // 2)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
