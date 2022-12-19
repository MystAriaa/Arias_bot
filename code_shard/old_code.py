import hashlib
import hmac
import os
import requests
from requests.api import request
from urllib.parse import urlencode

oauth_token = "oauth:mw11ii0jn8yrd1ixgx32npj1tu7oij"
client_id = "gogmi2ufzgqcww4rh65sgez3kz1tek"
client_secret = "c345z62b5ra43icw2g2tnwgkondymk"
access_token = "hvy7oj9mvgjbb9zi6qc8nekgmoe934"

# Get the App Access Token. If one not generated, generate it
def get_access_token():
    if access_token != "":
        return access_token
    return generate_access_token()


# Generate App Access Token and set OS variable
def generate_access_token():
    # Generate an access token for authenticating requests
    auth_body = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    auth_response = requests.post("https://id.twitch.tv/oauth2/token", auth_body)

    # Setup Headers for future requests
    auth_response_json = auth_response.json()

    # Set Environment variable
    access_token = auth_response_json["access_token"]
    os.environ["TWITCH_ACCESS_TOKEN"] = access_token
    print(access_token)
    return access_token

# Validate Access Token
def validate_auth(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url="https://id.twitch.tv/oauth2/validate", headers=headers)
    response_json = response.json()
    if response.status_code == requests.status_codes.ok & response_json.get('client_id') == client_id:
        return response_json
    return False

# Central way to get headers for requests to Twitch
def get_auth_headers():
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {get_access_token()}"
    }
    return headers

def get_user_id(nom_chaine):
    response = requests.get(url='https://api.twitch.tv/helix/users?login={}'.format(nom_chaine) , headers=get_auth_headers())
    try:
        return response.json()['data'][0]['id']
    except:
        print("Chaine non trouvé et/ou mauvaise requete")
        return None

print(get_user_id("mystaria_"))

"""response = requests.get(url='https://api.twitch.tv/helix/moderation/moderators?broadcaster_id={}'.format("oauth:mw11ii0jn8yrd1ixgx32npj1tu7oij") , headers=get_auth_headers())
print(response.json())"""

#https://id.twitch.tv/oauth2/authorize?client_id=<your client id>&redirect_url=<your registered redirect URL>&response_type=<type>&scope=<space-separated list of scopes>

def get_auth_url():
    your_client_id = client_id
    redirect_url = "http://localhost:5000/auth"
    types = "token"
    space_separated_list_of_scopes = "user:read:follows moderator:manage:banned_users"
    url = "https://id.twitch.tv/oauth2/authorize?client_id={}&redirect_url={}&response_type={}&scope={}".format(your_client_id,redirect_url,types,space_separated_list_of_scopes)
    return urlencode(url)

print(get_auth_url())