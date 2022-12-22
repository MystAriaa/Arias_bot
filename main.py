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

site_base_url = "http://localhost:5000/autorisation_code"
client_id = twitch.get_client_id()
client_secret = twitch.get_client_secret()
scopes = ["moderation:read","moderator:manage:banned_users"]

user_autorisation_url = "https://id.twitch.tv/oauth2/authorize?response_type={0}&client_id={1}&redirect_uri={2}&scope={3}&state=".format("code",client_id,site_base_url,twitch.scope_format(scopes))

connection_bd = mysql.connect_to_database()

app_access_token = ""

flag_routine_update_user_banned_table = True

#---------------------------------------------------------------------------------------------------------------------#
@app.route('/')
def home():
	global random_state
	random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
	return render_template('pages/home.html', user_autorisation_url = user_autorisation_url + random_state, state = random_state)

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

@app.route('/autorisation_code')
def query():
	global random_state
	global app_access_token
	acces_granted = False
	try:
		if (request.args.get('state') == random_state):  #no cross attacks, we good

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
			print("We might be under a CSRF attack")
			try:
				os.remove("templates/pages/temp_pages/unban_all_{}.html".format(user_access_token))
			except:
				pass
			random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
			return render_template('pages/home.html', acces_granted="Whoops, connection failed", user_autorisation_url = user_autorisation_url + random_state, state = random_state)
	except:
		try:
			os.remove("templates/pages/temp_pages/unban_all_{}.html".format(user_access_token))
		except:
			pass
		random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
		return render_template('pages/home.html', acces_granted="Whoops, connection failed", user_autorisation_url = user_autorisation_url + random_state, state = random_state)


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
		user_id, user_login, user_name = twitch.get_user_info(user_id, app_access_token, client_id)
		#Mise en base de donnée de l'utilisateur
		mysql.input_a_new_user(connection_bd, user_id, user_login, user_name, user_access_token, user_refresh_token)
		#Creation de sa table de bannis
		mysql.create_table_banned_by_user(connection_bd, user_id)
		#Fill la nouvelle table avec les bannis de l'utilisateur
		list_of_banned_users_by_user = twitch.get_banlist(user_id, user_access_token, client_id)
		mysql.fill_banned_user_table_by_user(connection_bd, list_of_banned_users_by_user, user_id)

	#Petite mise en page en fonction de l'acces reçu
	if (acces_granted):
		f = open('templates/pages/temp_pages/unban_all_{}.html'.format(user_access_token), 'w')
		html_template = """<html><head><title>Redirect</title></head><body></body></html>"""
		f.write(html_template)
		f.close()
		f = open('templates/pages/temp_pages/force_update_ban_{}.html'.format(user_access_token), 'w')
		html_template = """<html><head><title>Redirect</title></head><body></body></html>"""
		f.write(html_template)
		f.close()
		thread_timeout_file_unban_all = threading.Thread(target = timeout_file_unban_all, args = (user_access_token,))
		thread_timeout_file_unban_all.start()
		thread_timeout_file_force_update_ban = threading.Thread(target = timeout_file_force_update_ban, args = (user_access_token,))
		thread_timeout_file_force_update_ban.start()
		return render_template('pages/autorisation_code.html',acces_granted="Successful connection", channel_name=user_name, unban_all_url = "http://localhost:5000/unban_all_{}.html".format(user_access_token), force_update_ban_url = "http://localhost:5000/force_update_ban_{}.html".format(user_access_token))
	else:
		try:
			os.remove("templates/pages/temp_pages/unban_all_{}.html".format(user_access_token))
		except:
			pass
		random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
		return render_template('pages/home.html', acces_granted="Whoops, connection failed", user_autorisation_url = user_autorisation_url + random_state, state = random_state)


@app.route('/unban_all_<string:user_access_token>.html') #return_to_original_state
def unban_all(user_access_token):
	global random_state
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
	mysql.remove_an_user(connection_bd, user_id)
	try:
		os.remove("templates/pages/temp_pages/unban_all_{}.html".format(user_access_token))
	except:
		pass
	random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
	return render_template('pages/home.html', user_autorisation_url = user_autorisation_url + random_state, state = random_state)

@app.route('/force_update_ban_<string:user_access_token>.html')
def force_update_ban(user_access_token):
	global random_state
	
	user_info = mysql.get_user_info_by_access_token(connection_bd, user_access_token)
	#0: primary_key / 1:user_id / 2:user_login / 3:user_name / 4:access_token / 5:refresh_token
	user_id = user_info[1]
	user_access_token = user_info[4]
	list_of_banned_user = mysql.get_all_master_banlist(connection_bd)
	twitch.ban_from_master_banlist(connection_bd, user_id, user_access_token, list_of_banned_user, client_id)

	try:
		os.remove("templates/pages/temp_pages/force_update_ban_{}.html".format(user_access_token))
	except:
		pass
	random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
	return render_template('pages/home.html', user_autorisation_url = user_autorisation_url + random_state, state = random_state)
	

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
		for user in array_of_users_info: #0: primary_key / 1:user_id / 2:user_login / 3:user_name / 4:access_token / 5:refresh_token
					
			user_id = user[1]
			user_name = user[3]
			user_access_token = user[4]
			user_refresh_token = user[5]
			log.log("Mise à jour des bannis pour {}".format(user_name))
			#check les access_token
			id = twitch.token_validation(user_access_token)
			if ( id == 0 or id == 1):
				user_access_token, user_refresh_token = twitch.token_refresh(connection_bd, client_id, client_secret, user_id=user_id, refresh_token=user_refresh_token, mode = "user")
			#appeler twitch allo les bannis stp
			list_of_banned_users_by_user = twitch.get_banlist(user_id, user_access_token, client_id)
			#imput les bannies dans la datatababbaaasee
			mysql.fill_banned_user_table_by_user(connection_bd, list_of_banned_users_by_user, user_id)

		#--------------------------------------------------------------------

		log.log("2/3")
		array_of_users_info = mysql.get_all_users(connection_bd)
		mysql.delete_all_master_banlist(connection_bd)
		for user in array_of_users_info: #0: primary_key / 1:user_id / 2:user_login / 3:user_name / 4:access_token / 5:refresh_token
					
			user_id = user[1]
			user_name = user[3]
			user_access_token = user[4]
			user_refresh_token = user[5]

			list_of_banned_user = mysql.get_all_user_table(connection_bd, user_id)
			
			log.log("Mise à jour de la master_banlist depuis l'utilisateur: {}({})".format(user_name,user_id))
			mysql.insert_list_banned_into_master(connection_bd, list_of_banned_user, user_id)
			
		#---------------------------------------------------------------------

		log.log("3/3")
		array_of_users_info = mysql.get_all_users(connection_bd)
		for user in array_of_users_info: #0: primary_key / 1:user_id / 2:user_login / 3:user_name / 4:access_token / 5:refresh_token
					
			user_id = user[1]
			user_name = user[3]
			user_access_token = user[4]
			user_refresh_token = user[5]

			list_of_banned_user = mysql.get_all_master_banlist(connection_bd)
			twitch.ban_from_master_banlist(connection_bd, user_id, user_access_token, list_of_banned_user, client_id)

		#---------------------------------------------------------------------
		
		for f in os.listdir("templates/pages/temp_pages"):
			if not f.endswith(".html"):
				continue
			os.remove(os.path.join("templates/pages/temp_pages", f))

		log.log("| Voici la fin de l'itération du thread |")
		#time.sleep(60*60*24)
		flag_routine_update_user_banned_table = False

	log.log("Sort du thread")
	random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
	return render_template('pages/home.html', user_autorisation_url = user_autorisation_url + random_state, state = random_state)


def timeout_file_unban_all(user_access_token):
	time.sleep(60)
	try:
		os.remove("templates/pages/temp_pages/unban_all_{}.html".format(user_access_token))
	except:
		log.log("Failed remove of file unban_all_{}.html".format(user_access_token))
		pass

def timeout_file_force_update_ban(user_access_token):
	time.sleep(60)
	try:
		os.remove("templates/pages/temp_pages/force_update_ban_{}.html".format(user_access_token))
	except:
		log.log("Failed remove of file unban_all_{}.html".format(user_access_token))
		pass


#---------------------------------------------------------------------------------------------------------------------#


if __name__ == '__main__':
	app_access_token = twitch.token_generation(client_id,client_secret)
	thread_update_user_banned_table = threading.Thread(target = routine_update_user_banned_table)
	app.run(debug=True, port=5000)
	log.end_log()







#C:\Users\adrie\Documents\Twitch_project>virtual_env\scripts\activate.bat
#                                      .\virtual_env\Scripts\activate.ps1