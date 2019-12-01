import requests
import base64
import os
import time
from dotenv import load_dotenv

load_dotenv()

URL = "https://api.spotify.com"
TOKEN_URL = "https://accounts.spotify.com/api/token"

CLIENT_ID = os.getenv("SPOTIFY_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_SECRET")

class AccessToken(object):
    def __init__(self, client_id = None, client_secret = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tokenData = None

    def getAccessToken(self):
        if self.tokenData and not self.tokenExpired(self.tokenData):
            return self.tokenData['access_token']
        
        tokenData = self._requestAccessToken()
        tokenData = self._appendExpireTime(tokenData)
        self.tokenData = tokenData
        return self.tokenData['access_token']

    def _requestAccessToken(self):
        payload = {'grant_type' : 'client_credentials'}
        auth_header = base64.b64encode(str(self.client_id + ':' + self.client_secret).encode())
        headers = {'Authorization' : 'Basic %s' % auth_header.decode()}
        r = requests.post(TOKEN_URL, data = payload, headers = headers,
                      verify = True)

        if r.status_code != 200:
            print("Spotify authorization error:")
            print(response.reason)

        tokenData = r.json()
        return tokenData
       
    def _tokenExpired(self, tokenData):
        now = int(time.time())
        return tokenData['expire_time'] - now < 60

    def _appendExpireTime(self, tokenData):
        print(tokenData)
        tokenData['expire_time'] = int(time.time()) + tokenData['expires_in']
        return tokenData

accessTokenManager = AccessToken(CLIENT_ID, CLIENT_SECRET)
accessToken = accessTokenManager.getAccessToken()
print(accessToken)
