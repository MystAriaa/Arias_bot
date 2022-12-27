import os
from flask import Flask, render_template, request
from package import twitch_connector as twitch
from package import mysql_connector as mysql
from package import log
import threading
import time
import datetime
import string
import random

log.init_file_name()
log.start_log()


app = Flask(__name__)

site_base_url = "http://localhost:5000/portal"
client_id = twitch.get_client_id()
client_secret = twitch.get_client_secret()
scopes = ["moderation:read","moderator:manage:banned_users"]

user_autorisation_url = "https://id.twitch.tv/oauth2/authorize?response_type={0}&client_id={1}&redirect_uri={2}&scope={3}&state=".format("code",client_id,site_base_url,twitch.scope_format(scopes))

connection_bd = mysql.connect_to_database()

app_access_token = ""
random_state_list = []

flag_routine_update_user_banned_table = True

#---------------------------------------------------------------------------------------------------------------------#
@app.route('/')
def home():
	global random_state_list
	random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
	random_state_list.append(random_state)
	while len(random_state_list) > 50:
		random_state_list.pop(0)
	return render_template('pages/home.html', user_autorisation_url = user_autorisation_url + random_state)

@app.route('/faq')
def faq():
	return render_template('pages/faq.html')

@app.route('/contact')
def contact():
	return render_template('pages/contact.html')

@app.route('/version')
def version():
	return render_template('pages/version.html')

@app.errorhandler(404)
def page_not_found(error):
	return render_template('pages/page_not_found.html'), 404

@app.route('/portal')
def query():
	global random_state_list
	global app_access_token
	acces_granted = False
	try:
		if (request.args.get('state') in random_state_list):  #no cross attacks, we good
			random_state_list.remove(request.args.get('state'))
			error_state = request.args.get('error')               #error case
			if (error_state == "access_denied"):
				acces_granted = False
				error_description = request.args.get('error_description')
				log.log("Nous avons un refus de l'utilisateur : {}.".format(error_description))
			else:                                                 #no error case
				acces_granted = True
				user_code = request.args.get('code')
				scope = request.args.get('scope')
				log.log("Nous avons reçu l'autorisation de l'utilisateur.")

		else:                          #cross attacks, not good
			log.log("We might be under a CSRF attack")
			random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
			random_state_list.append(random_state)
			return render_template('pages/home.html', acces_granted="Whoops, connection failed", user_autorisation_url = user_autorisation_url + random_state)
	except:
		random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
		random_state_list.append(random_state)
		return render_template('pages/home.html', acces_granted="Whoops, connection failed", user_autorisation_url = user_autorisation_url + random_state)


	#Si nous avons reçu le code
	if (acces_granted):
		#Obtention des tokens utilisateur      
		user_access_token, user_refresh_token = twitch.token_generation(client_id, client_secret, grant_type = "authorization_code", code = user_code, redirect_url = site_base_url)
		#Obtention de l'id de notre utilisateur
		user_id = twitch.token_validation(user_access_token)
		#Obtention des informations de notre utilisateur
		#+check si notre app_access_token a besoin d'etre refresh      
		if (twitch.token_validation(app_access_token) != 1):
			app_access_token = twitch.token_refresh(connection_bd, client_id, client_secret, mode = "app")
		user_id, user_name = twitch.get_user_info(user_id, app_access_token, client_id)
		if (user_id == "0" and user_name == "0"):
			log.log("get_user_info returns 0, we go out. app_access_token={}, acces_granted={}".format(app_access_token,acces_granted))
			random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
			random_state_list.append(random_state)
			return render_template('pages/home.html', acces_granted="Whoops, connection failed", user_autorisation_url = user_autorisation_url + random_state)
		else:
			#Mise en base de donnée de l'utilisateur
			mysql.input_a_new_user(connection_bd, user_id, user_name, user_access_token, user_refresh_token)
			#Creation du filtrage par defaut pour cette utilisateur
			default_list_filter = ['1','0','1','1','1','1','1','0','0','0','1']
			mysql.set_user_filter(connection_bd, user_id, default_list_filter)
			#Creation de ces options
			mysql.set_user_option(connection_bd, user_id, [0,0])
			#Creation de sa table de bannis
			mysql.create_table_banned_by_user(connection_bd, user_id)
			#Fill la nouvelle table avec les bannis de l'utilisateur
			list_of_banned_users_by_user = twitch.get_banlist(user_id, user_access_token, client_id)
			mysql.fill_banned_user_table_by_user(connection_bd, list_of_banned_users_by_user, user_id)

	#Petite mise en page en fonction de l'acces reçu
	if (acces_granted):
		user_option = mysql.get_user_option(connection_bd, user_id)
		if user_option["giveonly"] == 1:
			giveonly_text = "The Give-Only option is currently ON for your channel."
		elif user_option["giveonly"] == 0:
			giveonly_text = "The Give-Only option is currently OFF for your channel."
		if user_option["receiveonly"] == 1:
			receiveonly_text = "The Receive-Only option is currently ON for your channel."
		elif user_option["receiveonly"] == 0:
			receiveonly_text = "The Receive-Only option is currently OFF for your channel."
		#Boxes auto checked with registered user filter pref
		user_filter_pref = mysql.get_user_filter(connection_bd, user_id)
		
		checked_box_list = []
		for e in user_filter_pref:
			if e == 1:
				checked_box_list.append("checked")
			else:
				checked_box_list.append("")

		return render_template('pages/portal.html',acces_granted="Successful connection", channel_name=user_name, token=user_access_token, check=checked_box_list, giveonlytext = giveonly_text, receiveonlytext = receiveonly_text)
	else:
		random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
		random_state_list.append(random_state)
		return render_template('pages/home.html', acces_granted="Whoops, connection failed", user_autorisation_url = user_autorisation_url + random_state)




@app.route('/visualisation')
def visualisation():

	command = """
	SELECT user_id, user_name, reason, moderator_name, origin_channel_id
	FROM master_banlist"""
	connection_bd.reconnect()
	with connection_bd.cursor() as cursor:
		cursor.execute(command)
		list_of_banned_user_info = cursor.fetchall()
	
	list_data = []
	#0 user_id, 1 usr_name, 2 reason, 3 moderator_name, 4 origin_id
	for e in list_of_banned_user_info:
		#Get user_name by id
		user_name = mysql.get_user_name_by_id(connection_bd, e[-1])
		#Mise en format
		origin_text = "Banned from {}'s channel by {}".format(user_name, e[3])
		#Get Tags
		list_tag = mysql.get_tag_by_id(connection_bd, e[0])
		#Mise en list
		list_data.append((e[1], list_tag, e[2], origin_text))
	return render_template('pages/visualisation.html', data = list_data)


@app.route('/disconnect', methods=['POST']) #return_to_original_state
def disconnect():
	user_access_token = request.form['access_token']
	user_info = mysql.get_user_info_by_access_token(connection_bd, user_access_token)
	user_refresh_token = user_info[-1]
	id = twitch.token_validation(user_access_token)
	if ( id == 0 or id == 1):
		user_access_token, user_refresh_token = twitch.token_refresh(connection_bd, client_id, client_secret, user_id=user_id, refresh_token=user_refresh_token, mode = "user")
	user_id = user_info[1]
	list_of_banned_user = twitch.get_banlist(user_id, user_access_token, client_id, filter = False)
	#filter ban list to keep on user ban by arias
	list_of_unbanned_user = []
	for banned_user in list_of_banned_user:
		if("User automaticaly ban by Arias_bot." in banned_user["reason"]):
			list_of_unbanned_user.append(banned_user)
	twitch.unban_all(user_id, user_access_token, list_of_unbanned_user, client_id)
	twitch.revoke_token(user_access_token, client_id)
	twitch.revoke_token(user_refresh_token, client_id)
	mysql.delete_user_option(connection_bd, user_id)
	mysql.remove_an_user(connection_bd, user_id)
	return render_template('pages/validation.html',text="Your have been successfully removed from the network.")

@app.route('/force_update_ban', methods=['POST'])
def force_update_ban():
	user_access_token = request.form['access_token']
	user_info = mysql.get_user_info_by_access_token(connection_bd, user_access_token)
	#0: primary_key / 1:user_id / 2:user_name / 3:access_token / 4:refresh_token
	user_id = user_info[1]
	user_access_token = user_info[3]
	list_of_banned_user = mysql.get_all_master_banlist(connection_bd)
	twitch.ban_from_master_banlist(connection_bd, user_id, user_access_token, list_of_banned_user, client_id)
	return render_template('pages/validation.html',text="Arias_bot paid a visit on your channel !")

@app.route('/update_filter', methods=['POST'])
def update_filter():
	list_filter = [request.form['permanent'],request.form['timeout'],request.form['commented'],request.form['notcommented'],request.form['sexism'],request.form['homophobia'],request.form['rascism'],request.form['backseat'],request.form['spam'],request.form['username'],request.form['other']]
	user_id = twitch.token_validation(request.form['access_token'])
	mysql.update_user_filter(connection_bd, user_id, list_filter)
	return render_template('pages/validation.html', text="Your filter have been successfully updated.")

@app.route('/give_only', methods=['POST'])
def give_only():
	user_id = twitch.token_validation(request.form["access_token"])
	
	dict_option = mysql.get_user_option(connection_bd, user_id)
	if dict_option["giveonly"] == 0:
		mysql.update_user_option(connection_bd, user_id, [1,dict_option["receiveonly"]])
		text_return = "Give-Only is active for your channel."
	else:
		mysql.update_user_option(connection_bd, user_id, [0,dict_option["receiveonly"]])
		text_return = "Give-Only is not active for your channel."
		
	return render_template('pages/validation.html', text=text_return)

@app.route('/receive_only', methods=['POST'])
def receive_only():
	user_id = twitch.token_validation(request.form["access_token"])
	
	dict_option = mysql.get_user_option(connection_bd, user_id)
	if dict_option["receiveonly"] == 0:
		mysql.update_user_option(connection_bd, user_id, [dict_option["giveonly"], 1])
		text_return = "Receive-Only is active for your channel."
	else:
		mysql.update_user_option(connection_bd, user_id, [dict_option["giveonly"], 0])
		text_return = "Receive-Only is not active for your channel."
		
	return render_template('pages/validation.html', text=text_return)

#---------------------------------------------------------------------------------------------------------------------#

@app.route('/start')
def routine_update_user_banned_table():
	global random_state
	global flag_routine_update_user_banned_table
	flag_routine_update_user_banned_table = True
	log.log("Rentre dans le thread")
	#S'execute tout les jours à 6 heures du matin
	#time.sleep(60*60*6 + 60*60*24 - (datetime.datetime.now().second + datetime.datetime.now().minute*60 + datetime.datetime.now().hour*60*60))
	while flag_routine_update_user_banned_table:
		log.log("| Voici une itération du thread |")
		log.log("1/3")

		array_of_users_info = mysql.get_all_users(connection_bd)
		for user in array_of_users_info: #0: primary_key / 1:user_id / 2:user_name / 3:access_token / 4:refresh_token
					
			user_id = user[1]
			user_name = user[2]
			user_access_token = user[3]
			user_refresh_token = user[4]
			log.log("Mise à jour des bannis pour {}".format(user_name))
			#check les access_token
			id = twitch.token_validation(user_access_token)
			if ( id == 0 or id == 1):
				user_access_token, user_refresh_token = twitch.token_refresh(connection_bd, client_id, client_secret, user_id=user_id, refresh_token=user_refresh_token, mode = "user")
			
			#Do not get banned_user from user with Receive-Only
			user_option = mysql.get_user_option(connection_bd, user_id)
			if user_option == "Error":
				pass
			else:
				if (user_option["receiveonly"] == 0): # 0==OFF
					#appeler twitch allo les bannis stp
					list_of_banned_users_by_user = twitch.get_banlist(user_id, user_access_token, client_id)
					#imput les bannies dans la datatababbaaasee
					mysql.fill_banned_user_table_by_user(connection_bd, list_of_banned_users_by_user, user_id)
				else:
					#If ON we must remove all banned user by Arias_bot from the channel
					list_of_banned_user = twitch.get_banlist(user_id, user_access_token, client_id, filter = False)
					list_of_unbanned_user = []
					for banned_user in list_of_banned_user:
						if("User automaticaly ban by Arias_bot." in banned_user["reason"]):
							list_of_unbanned_user.append(banned_user)
					twitch.unban_all(user_id, user_access_token, list_of_unbanned_user, client_id)

			
		#--------------------------------------------------------------------

		#Ici on recupt la list a ban et on la compare a la table master pour voir qui de la table master on unban
		log.log("2/3")
		array_of_users_info = mysql.get_all_users(connection_bd)
		list_of_banned_user_from_master = mysql.get_all_master_banlist(connection_bd)

		list_of_banned_user = []
		for user in array_of_users_info: #0: primary_key / 1:user_id / 2:user_name / 3:access_token / 4:refresh_token
			list_of_banned_user.extend(mysql.get_all_user_table(connection_bd, user[1]))

		#Il faut mettre à 0 les PRIMARY_KEY de tout les elements des deux listes pour pouvoir les comparer+ retirer les origin channels + time 
		temp_1 = []
		temp_2 = []
		for e in list_of_banned_user_from_master:
			temp_1.append(("0",e[1],e[2],e[3],e[4],"",e[6],e[7]))
		for e in list_of_banned_user:
			temp_2.append(("0",e[1],e[2],e[3],e[4],"",e[6],e[7]))
		list_of_banned_user_from_master = temp_1
		list_of_banned_user_m = temp_2

		user_to_unban = list(set(list_of_banned_user_from_master) - set(list_of_banned_user_m))

		for user in array_of_users_info:
			user_id = user[1]
			user_access_token = user[3]
			twitch.unban_all(user_id,user_access_token,user_to_unban,client_id)
		
		#need to remove unbanned_user from flag table
		mysql.remove_list_user_from_tag_table(connection_bd, user_to_unban)
		#need to remove unbanned_user from master_table
		mysql.remove_list_user_in_master(connection_bd, user_to_unban)
		#need to update master_table with new banned
		for user in array_of_users_info:
			user_id = user[1]
			mysql.insert_list_banned_into_master(connection_bd, mysql.get_all_user_table(connection_bd, user_id), user_id)
		log.log("Mise à jour de la master_banlist")
			
			
		#---------------------------------------------------------------------

		log.log("3/3")
		#array_of_users_info = mysql.get_all_users(connection_bd)
		for user in array_of_users_info: #0: primary_key / 1:user_id / 2:user_name / 3:access_token / 4:refresh_token			
			user_id = user[1]
			user_access_token = user[3]
			#If Give-Only option is off or None we can ban on this channel
			if (mysql.get_user_option(connection_bd, user_id)["giveonly"] == "Error"):
				pass
			else:
				if (mysql.get_user_option(connection_bd, user_id)["giveonly"] == 1):
					pass
				else:
					list_of_banned_user = mysql.get_all_master_banlist(connection_bd)
					twitch.ban_from_master_banlist(connection_bd, user_id, user_access_token, list_of_banned_user, client_id)

		#---------------------------------------------------------------------

		log.log("| Voici la fin de l'itération du thread |")
		#time.sleep(60*60*24)
		flag_routine_update_user_banned_table = False

	log.log("Sort du thread")
	random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
	random_state_list.append(random_state)
	return render_template('pages/home.html', user_autorisation_url = user_autorisation_url + random_state)


#---------------------------------------------------------------------------------------------------------------------#


if __name__ == '__main__':
	app_access_token = twitch.token_generation(client_id,client_secret)
	thread_update_user_banned_table = threading.Thread(target = routine_update_user_banned_table)
	app.run(debug=True, port=5000)
	log.end_log()







#C:\Users\adrie\Documents\Twitch_project>virtual_env\scripts\activate.bat
#                                      .\virtual_env\Scripts\activate.ps1