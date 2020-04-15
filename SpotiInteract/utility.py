import requests
import base64
import re

def getPlaylistFromId(id, access_token):
    URL = "https://api.spotify.com/v1/playlists/" + id + "/tracks"
    headers = {"Authorization": "Bearer " + access_token}
    r = requests.get(URL, headers = headers, verify = True)
    playlist = []
    
    if r.status_code != 200:
        print("Spotify GET error:")
        print(r.reason)
        print(r.text)
        print(r)
        return False

    tracks = r.json()['items']
    for track in tracks:
        track = track['track']
        song = '{} - {}'.format(track['artists'][0]['name'], track['name'])
        song = re.sub('[/]', ' ', song) # '/' in string causes http errors
        playlist.append(song)

    return playlist

