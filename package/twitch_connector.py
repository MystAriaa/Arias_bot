import os
import requests
from requests.api import request
import json
from package import mysql_connector as mysql
from package import log
from package import tag_filter

#----------------------------------------------------------------------------------------------------------------------#

def get_client_id():
    return os.environ["TWITCH_CLIENT_ID"]
def get_client_secret():
    return os.environ["TWITCH_CLIENT_SECRET"]
def get_oauth_token():
    return os.environ["TWITCH_OAUTH_TOKEN"]

#convert an array of scopes to a formated string URL compatible
def scope_format(our_desired_scopes):
    formated_string = ""
    for scope in our_desired_scopes:
        tscope = scope.replace(":","%3A")
        formated_string += tscope
        if our_desired_scopes.index(scope)+1 != len(our_desired_scopes):
            formated_string += "+"
    return(formated_string)

#Generation du token d'acces
#Cas 1 : Client credentials grant flow -> Pour données publiques
#Cas 2 : Authorization code grant flow -> Pour données privées
def token_generation(client_id, client_secret, grant_type = "client_credentials", code = None, redirect_url = None):
    if (grant_type == "client_credentials"):
        auth_body = {"client_id": client_id, "client_secret": client_secret, "grant_type": grant_type}
        auth_response_json = requests.post("https://id.twitch.tv/oauth2/token", auth_body).json() #call api to get token
        log.log("Un token d'acces viens d'être générer pour l'app: {}".format(auth_response_json["access_token"]))
        return(auth_response_json["access_token"])
    elif (grant_type == "authorization_code"):
        auth_body = {"client_id": client_id, "client_secret": client_secret, "code": code, "grant_type": grant_type, "redirect_uri": redirect_url}
        auth_response = requests.post("https://id.twitch.tv/oauth2/token", auth_body) #call api to get token
        auth_response_json = auth_response.json()
        if (auth_response.status_code == 200):
            log.log("Un token d'acces viens d'être générer pour l'user: {}".format(auth_response_json["access_token"]))
            return(auth_response_json["access_token"],auth_response_json["refresh_token"])
        else:
            log.log("Echec de la création du doublet de token")
            return("","")


def token_validation(token):
    #Validation of our token
    #Enable a check on a token to know if it is outdated or not
    #Return int:user_id in case of a valid user token
    #Return 1 in case of a valid app token
    #Return 0 in case of an invalid token in need of a refresh
    #Return -1 in all other case
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url="https://id.twitch.tv/oauth2/validate", headers=headers)
    if response.status_code == 200:
        response_json = response.json()
        try:
            r = response_json["user_id"]
            log.log("Notre token user a été validée")
            return(r)   
        except:
            log.log("Notre token app a été validée")
            return(1)
    elif response.status_code == 401:
        log.log("Notre token n'a pas été validée, il a besoin d'être refresh")
        return(0)
    else:
        log.log("Notre token n'a rien de bon")
        return(-1)

#Refesh of our access_token
#Two mode, refresh our user_token or our app_token
def token_refresh(connection, client_id, client_secret, user_id = "", refresh_token = "", grant_type = "refresh_token", mode = "app"):
    if (mode == "user"):
        auth_body = {"client_id": client_id, "client_secret": client_secret, "grant_type": grant_type, "refresh_token": refresh_token}
        auth_response = requests.post("https://id.twitch.tv/oauth2/token", auth_body) #call api to get token
        #If Error 401, refresh token no longer valid, meaning user disconnected from app
        #We must remove him from the database
        #We must unban all users in his channels ban by Arias_bot
        try:
            if (auth_response.status_code == 200):
                auth_response_json = auth_response.json()
                new_access_token = auth_response_json["access_token"]
                new_refresh_token = auth_response_json["refresh_token"]
                mysql.set_new_user_info(connection, user_id, new_access_token, new_refresh_token)
                log.log("Un token d'acces et un de rafraichisement viens d'être générer par rafraichisement")
                #Generate a new file to allow
                return (new_access_token,new_refresh_token)
            elif (auth_response.status_code == 400):
                log.log("Erreur 400 Invalid token | Cet utilisateur c'est dé-enregistré")
                mysql.remove_banned_user_from_master_banlist(connection, user_id)
                mysql.remove_an_user(connection, user_id)
                return ("0","0")
            elif (auth_response.status_code == 401):
                log.log("Erreur 401 Unauthorized | Cet utilisateur c'est dé-enregistré")
                mysql.remove_banned_user_from_master_banlist(connection, user_id)
                mysql.remove_an_user(connection, user_id)
                return ("0","0")
        except:
            return ("0","0")
    if (mode == "app"):
        return (token_generation(client_id, client_secret),"0")

def revoke_token(token, client_id):
        url = "https://id.twitch.tv/oauth2/revoke"
        auth_header = {"Content-Type": "application/x-www-form-urlencoded"}
        data_body = "client_id={}&token={}".format(client_id,token)
        request_data = {
                "method": "POST",
                "url": url,
                "headers": auth_header,
                "data": data_body}
        response = requests.request(**request_data)
        if (response.status_code == 200):
            log.log("Token successfully revoken")
        else:
            log.log("Token not revoken")
            log.log(response.json())
    

#Get user info via app_access_token
def get_user_info(user_id, app_access_token, client_id):
    url = "https://api.twitch.tv/helix/channels?broadcaster_id={}".format(user_id)
    auth_header = {"Authorization": 'Bearer {}'.format(app_access_token), "Client-ID": client_id}
    request_data = {
            "method": "GET",
            "url": url,
            "headers": auth_header}
    response = requests.request(**request_data)
    response_json = response.json()
    if (response.status_code == 200):
        return (response_json["data"][0]["broadcaster_id"],response_json["data"][0]["broadcaster_name"])
    else:
        return ("0","0")
    

#Get banlist from user from twitch
#Filter out ban made by Arias_bot &&& Temporary bans
#So gather only bans made by user&mods
def filter_banlist(array):
    filtered_array = []
    for ele in array:
        if (not ("User automaticaly ban by Arias_bot." in ele["reason"])): # and not 'expire_in' in ele
            filtered_array.append(ele)
    return filtered_array
def get_banlist(user_id, access_token, client_id, filter=True):
    url = "https://api.twitch.tv/helix/moderation/banned?broadcaster_id={}".format(user_id)
    auth_header = {"Authorization": 'Bearer {}'.format(access_token), "Client-ID": client_id}
    request_data = {
            "method": "GET",
            "url": url,
            "headers": auth_header}
    response = requests.request(**request_data)
    response_json = response.json()
    if (response.status_code == 200):
        if(filter):
            
            return(filter_banlist(response_json["data"]))
        else:
            return(response_json["data"])
    else:
        return([])


def ban_from_master_banlist(connection, user_id, user_access_token, list_of_banned_user, client_id):
    
    log.log("Bannisement pour l'utilisateur: {}".format(user_id))
    for banned_user in list_of_banned_user:
        if (banned_user[-1] == user_id): #skip if banned_user comming from this channel
            log.log("Skip du ban car originaire de cette utilisateur")
        else:
            url = "https://api.twitch.tv/helix/moderation/bans?broadcaster_id={}&moderator_id={}".format(user_id,user_id)
            auth_header = {"Authorization": 'Bearer {}'.format(user_access_token), "Client-ID": client_id, "Content-Type": "application/json"}
            description = "User automaticaly ban by Arias_bot. \rUser originaly ban from the channel: {}. \rOriginal reason: {}".format(mysql.get_user_name_by_id(connection, banned_user[-1]),banned_user[3])
            if (banned_user[5] == ""):
                banned_user_data = {"data":{"user_id":banned_user[1], "reason":description}}
            else:
                dur = min(tag_filter.convert_expire_time(banned_user[4],banned_user[5]),1209600)
                banned_user_data = {"data":{"user_id":banned_user[1], "duration":dur, "reason":description}}
            request_data = {
                    "method": "POST",
                    "url": url,
                    "headers": auth_header,
                    "json": banned_user_data}
            response = requests.request(**request_data)
            if (response.status_code == 200):
                log.log("Ban de {}".format(banned_user[0]))
            """else:
                log.log()"""

def unban_all(user_id, user_access_token, list_of_unbanned_user, client_id):
    for unbanned_user in list_of_unbanned_user:
        try:
            unbanned_user_id = unbanned_user["user_id"]
        except:
            unbanned_user_id = unbanned_user[1]
        url = "https://api.twitch.tv/helix/moderation/bans?broadcaster_id={}&moderator_id={}&user_id={}".format(user_id,user_id,unbanned_user_id)
        auth_header = {"Authorization": 'Bearer {}'.format(user_access_token), "Client-ID": client_id}
        request_data = {
                "method": "DELETE",
                "url": url,
                "headers": auth_header}
        response = requests.request(**request_data)
        if (response.status_code == 204):
            log.log("User ({}) unban from channel ({})".format(unbanned_user_id,user_id))




if __name__ == '__main__':
    log.log("Ce fichier n'est pas fait pour etre executer directement mais comme un package à importer")