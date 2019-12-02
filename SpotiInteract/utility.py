import requests
import base64

def getPlaylistFromId(id, access_token):
    URL = "https://api.spotify.com/v1/playlists/"
    #params = {"playlist_id": id}
    #print(access_token)
    headers = {"Authorization": "Bearer " + access_token}
    r = requests.get(URL + id, headers = headers, verify = True)
    
    if r.status_code != 200:
        print("Spotify GET error:")
        print(r.reason)
        print(r.text)
        print(r)
        return False

    return r.json()

