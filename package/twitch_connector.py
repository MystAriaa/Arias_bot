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
	log.log("Called token_generation")
	if (grant_type == "client_credentials"):
		auth_body = {"client_id": client_id, "client_secret": client_secret, "grant_type": grant_type}
		auth_response_json = requests.post("https://id.twitch.tv/oauth2/token", auth_body).json() #call api to get token
		log.log("A new app access token has been generated: {}".format(auth_response_json["access_token"]))
		return(auth_response_json["access_token"])
	elif (grant_type == "authorization_code"):
		auth_body = {"client_id": client_id, "client_secret": client_secret, "code": code, "grant_type": grant_type, "redirect_uri": redirect_url}
		auth_response = requests.post("https://id.twitch.tv/oauth2/token", auth_body) #call api to get token
		auth_response_json = auth_response.json()
		if (auth_response.status_code == 200):
			log.log("A new user access token and refresh has been generated: {} / {}".format(auth_response_json["access_token"],auth_response_json["refresh_token"]))
			return(auth_response_json["access_token"],auth_response_json["refresh_token"])
		else:
			log.log("Failed to generate an user access token. Returning ( , )")
			return("","")


def token_validation(token):
	#Validation of our token
	#Enable a check on a token to know if it is outdated or not
	#Return int:user_id in case of a valid user token
	#Return 1 in case of a valid app token
	#Return 0 in case of an invalid token in need of a refresh
	#Return -1 in all other case
	log.log("Called token_validation")
	headers = {"Authorization": f"Bearer {token}"}
	response = requests.get(url="https://id.twitch.tv/oauth2/validate", headers=headers)
	if response.status_code == 200:
		response_json = response.json()
		try:
			r = response_json["user_id"]
			log.log("Successfully validated user access token")
			return(r)   
		except Exception as e:
			log.log("Successfully validated app access token")
			log.log(str(e))
			return(1)
	elif response.status_code == 401:
		log.log("Failed to validate our token. It needs to be refreshed")
		return(0)
	else:
		log.log("Failed to validate our token. It is not a valid token")
		return(-1)

#Refesh of our access_token
#Two mode, refresh our user_token or our app_token
def token_refresh(connection, client_id, client_secret, user_id = "", refresh_token = "", grant_type = "refresh_token", mode = "app"):
	log.log("Called token_refresh")
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
				log.log("Successfully refresh user access token and refresh token")
				#Generate a new file to allow
				return (new_access_token,new_refresh_token)
			elif (auth_response.status_code == 400):
				log.log("Erreur 400 Invalid token | User {} is disconnect from the network. Returning (0,0)".format(user_id))
				mysql.remove_ban_from_user_in_master(connection, user_id)
				mysql.remove_an_user(connection, user_id)
				return ("0","0")
			elif (auth_response.status_code == 401):
				log.log("Erreur 401 Unauthorized | User {} is disconnect from the network. Returning (0,0)".format(user_id))
				mysql.remove_ban_from_user_in_master(connection, user_id)
				mysql.remove_an_user(connection, user_id)
				return ("0","0")
		except Exception as e:
			log.log("Failed to refresh our token. Returning (0,0)")
			log.log(str(e))
			return ("0","0")
	if (mode == "app"):
		return (token_generation(client_id, client_secret),"0")

def revoke_token(token, client_id):
	log.log("Called revoke_token")
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
		log.log("Successfully revoked token")
	else:
		log.log("Failed to revoke token")
		log.log(response.json())


#Get user info via app_access_token
def get_user_info(user_id, app_access_token, client_id):
	log.log("Called get_user_info")
	url = "https://api.twitch.tv/helix/users?id={}".format(user_id)
	auth_header = {"Authorization": 'Bearer {}'.format(app_access_token), "Client-ID": client_id}
	request_data = {
			"method": "GET",
			"url": url,
			"headers": auth_header}
	response = requests.request(**request_data)
	response_json = response.json()
	if (response.status_code == 200):
		log.log("Successfully fetch user {} info from twitch".format(user_id))
		return (response_json["data"][0]["id"],response_json["data"][0]["display_name"],response_json["data"][0]["broadcaster_type"])
	else:
		log.log("Failed to fetch user {} info from twitch. Returning (0,0,0)".format(user_id))
		return ("0","0","0")
	

#Get banlist from user from twitch
#Filter out ban made by Arias_bot &&& Temporary bans
#So gather only bans made by user&mods
def filter_banlist(array):
	log.log("Called filter_banlist")
	filtered_array = []
	for ele in array:
		if (not ("User automaticaly ban by Arias_bot." in ele["reason"])): # and not 'expire_in' in ele
			filtered_array.append(ele)
	return filtered_array
def get_banlist(user_id, access_token, client_id, filter=True):
	log.log("Called get_banlist")
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
			log.log("Successfully fetched user {} banlist from twitch".format(user_id))
			return(filter_banlist(response_json["data"]))
		else:
			log.log("Failed to fetch user {} banlist from twitch".format(user_id))
			return(response_json["data"])
	else:
		return([])


def ban_from_master_banlist(connection, user_id, user_access_token, list_of_banned_user, client_id):
	log.log("Called ban_from_master_banlist")
	log.log("Starting to ban for user {}".format(user_id))
	user_filter_pref = mysql.get_user_filter(connection, user_id)
	list_of_eligible_id_for_ban = mysql.get_bannable_id_by_filter(connection, user_filter_pref)
	for banned_user in list_of_banned_user:
		if (banned_user[-1] == user_id): #skip if banned_user comming from this channel
			log.log("This user cannot be ban because it is originated from this channel")
		else:
			if (banned_user[1] in list_of_eligible_id_for_ban):
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
					log.log("Successfully banned user {} for the channel user {}".format(banned_user[1],user_id))
				else:
					log.log("Failed to ban user {} for the channel user {}".format(banned_user[1],user_id))
		








def unban_all(user_id, user_access_token, list_of_unbanned_user, client_id):
	log.log("Called unban_all")
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
			log.log("Successfully unban user {} from channel user {}".format(unbanned_user_id,user_id))
		else:
			log.log("Failed to unban user {} from channel user {}".format(unbanned_user_id,user_id))




if __name__ == '__main__':
	log.log("This file is not meant to be executed directly from console")