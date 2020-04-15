import requests
import base64
import re

def getPlaylistFromId(id, access_token):
    URL = "https://api.spotify.com/v1/playlists/" + id + "/tracks"
    headers = {"Authorization": "Bearer " + access_token}
    params = {"offset": 0}
    playlist = []
    
    while True:
        r = requests.get(URL, headers = headers, verify = True, params = params)

        if r.status_code != 200:
            print(r.status_code)
            print("Spotify GET error:")
            print(r.reason)
            print(r.text)
            print(r)
            return 

        songs = []
        tracks = r.json()['items']
        for track in tracks:
            track = track['track']
            song = '{} - {}'.format(track['artists'][0]['name'], track['name'])
            song = re.sub('[/]', ' ', song) # '/' in string causes http errors
            songs.append(song)
        
        if (songs == []):
            break

        playlist += songs
        params["offset"] = params["offset"] + 100

    return playlist

