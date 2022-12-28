import os
from flask import Flask, render_template, request
from package import twitch_connector as twitch
from package import mysql_connector as mysql
from package import discord_connector as discord
from package import log
import threading
import time
import datetime
import string
import random


log.init_file_name()
log.start_log()


app = Flask(__name__)
discord_bot = discord.get_discord_client()

site_base_url = "http://localhost:5000/portal"
client_id = twitch.get_client_id()
client_secret = twitch.get_client_secret()
scopes = ["moderation:read","moderator:manage:banned_users"]

user_autorisation_url = "https://id.twitch.tv/oauth2/authorize?response_type={0}&client_id={1}&redirect_uri={2}&scope={3}&state=".format("code",client_id,site_base_url,twitch.scope_format(scopes))

connection_bd = mysql.connect_to_database()

app_access_token = ""
discord_token = discord.get_discord_token()
available_discord_code = []
random_state_list = []
available_home_code = []

flag_routine_update_user_banned_table = True

#---------------------------------------------------------------------------------------------------------------------#
@app.route('/')
def entree():
	log.log("Return to entry page")
	global random_state_list
	global available_discord_code
	global available_home_code
	while len(random_state_list) > 50:
		random_state_list.pop(0)
		log.log("Element popped in random_state_list")
	while len(available_discord_code) > 50:
		available_discord_code.pop(0)
		log.log("Element popped in available_discord_code")
	while len(available_home_code) > 50:
		available_home_code.pop(0)
		log.log("Element popped in available_home_code")
	return render_template('pages/entree.html')

@app.route('/home', methods=['POST'])
def home():
	try:
		home_code = request.form['return_home']
		if home_code in available_home_code:
			available_home_code.remove(home_code)
			random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
			random_state_list.append(random_state)
			log.log("An user succesfully authenticated by discord")
			return render_template('pages/home.html', acces_granted="", user_autorisation_url = user_autorisation_url + random_state)
	except:
		log.log("An user did not get authenticated by discord succesfully")
		return render_template('pages/entree.html')

@app.route('/faq')
def faq():
	log.log("Went to F.A.Q. page")
	return render_template('pages/faq.html')

@app.route('/contact')
def contact():
	log.log("Went to contact page")
	return render_template('pages/contact.html')

@app.route('/version')
def version():
	log.log("Went to version page")
	return render_template('pages/version.html')

@app.errorhandler(404)
def page_not_found(error):
	log.log("404 | Page not found")
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
				log.log("An user refused the connection with Twitch : {}.".format(error_description))
			else:                                                 #no error case
				acces_granted = True
				user_code = request.args.get('code')
				scope = request.args.get('scope')
				log.log("An user accepted the connection with Twitch")

		else:                          #cross attacks, not good
			log.log("We might be under a CSRF attack")
			random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
			random_state_list.append(random_state)
			return render_template('pages/home.html', acces_granted="Whoops, connection failed", user_autorisation_url = user_autorisation_url + random_state)
	except:
		log.log("We did not get the state value from Twitch. Return to home page")
		random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
		random_state_list.append(random_state)
		return render_template('pages/home.html', acces_granted="Whoops, connection failed", user_autorisation_url = user_autorisation_url + random_state)


	#Si nous avons reçu le code
	if (acces_granted):
		#Obtention des tokens utilisateur      
		user_access_token, user_refresh_token = twitch.token_generation(client_id, client_secret, grant_type = "authorization_code", code = user_code, redirect_url = site_base_url)
		#Obtention de l'id de notre utilisateur
		user_id = twitch.token_validation(user_access_token)
		list_of_member_banned = mysql.get_all_ban_member(connection_bd)
		if str(user_id) in list_of_member_banned:
			log.log("Member with id= {} tryied to connect is ban".format(user_id))
			random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
			random_state_list.append(random_state)
			return render_template('pages/home.html', acces_granted="You are a banned member.", user_autorisation_url = user_autorisation_url + random_state)

		#Obtention des informations de notre utilisateur
		#+check si notre app_access_token a besoin d'etre refresh      
		if (twitch.token_validation(app_access_token) != 1):
			app_access_token = twitch.token_refresh(connection_bd, client_id, client_secret, mode = "app")
		user_id, user_name, user_type = twitch.get_user_info(user_id, app_access_token, client_id)
		if (user_id == "0" and user_name == "0" and user_type == "0"):
			log.log("get_user_info returns 0, we go out. app_access_token={}, acces_granted={}".format(app_access_token,acces_granted))
			random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
			random_state_list.append(random_state)
			return render_template('pages/home.html', acces_granted="Whoops, connection failed", user_autorisation_url = user_autorisation_url + random_state)
		else:
			#Mise en base de donnée de l'utilisateur
			mysql.input_a_new_user(connection_bd, user_id, user_name, user_type, user_access_token, user_refresh_token)
			#Creation du filtrage par defaut pour cette utilisateur
			default_list_filter = ['1','0','1','1','1','1','1','0','0','0','1','0']
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
		log.log("Access have not been granted, return to main page")
		random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
		random_state_list.append(random_state)
		return render_template('pages/home.html', acces_granted="Whoops, connection failed", user_autorisation_url = user_autorisation_url + random_state)




@app.route('/visualisation')
def visualisation():
	log.log("Loading of the visualisation page")
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
	log.log("An user wants to be disconnect from the network")
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
	random_home_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
	available_home_code.append(random_home_code)
	log.log("User {} succesfully disconnected, returning validation page".format(user_id))
	return render_template('pages/validation.html', text="Your have been successfully removed from the network.", return_home_code=random_home_code)

@app.route('/force_update_ban', methods=['POST'])
def force_update_ban():
	log.log("An user wants an update on their channel")
	user_access_token = request.form['access_token']
	user_info = mysql.get_user_info_by_access_token(connection_bd, user_access_token)
	#0: primary_key / 1:user_id / 2:user_name / 3:user_type / 4:access_token / 5:refresh_token
	user_id = user_info[1]
	user_access_token = user_info[4]
	list_of_banned_user = mysql.get_all_master_banlist(connection_bd)
	twitch.ban_from_master_banlist(connection_bd, user_id, user_access_token, list_of_banned_user, client_id)
	random_home_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
	available_home_code.append(random_home_code)
	log.log("Arias_bot has been succesfully called on {}'s channel, returning to validation page".format(user_id))
	return render_template('pages/validation.html', text="Arias_bot paid a visit on your channel !", return_home_code=random_home_code)

@app.route('/update_filter', methods=['POST'])
def update_filter():
	log.log("An user wants to update their filter")
	list_filter = [request.form['permanent'],request.form['timeout'],request.form['commented'],request.form['notcommented'],request.form['sexism'],request.form['homophobia'],request.form['rascism'],request.form['backseat'],request.form['spam'],request.form['username'],request.form['other'],request.form['trusted']]
	user_id = twitch.token_validation(request.form['access_token'])
	mysql.update_user_filter(connection_bd, user_id, list_filter)
	random_home_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
	available_home_code.append(random_home_code)
	log.log("Filter succesfully updated for user {}".format(user_id))
	return render_template('pages/validation.html', text="Your filter have been successfully updated.", return_home_code=random_home_code)

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
		
	random_home_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
	available_home_code.append(random_home_code)
	log.log("User {} activated Give_Only option for their channel".format(user_id))
	return render_template('pages/validation.html', text=text_return, return_home_code=random_home_code)

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

	random_home_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
	available_home_code.append(random_home_code)
	log.log("User {} activated Receive_Only option for their channel".format(user_id))
	return render_template('pages/validation.html', text=text_return, return_home_code=random_home_code)

#---------------------------------------------------------------------------------------------------------------------#

@app.route('/start')
def routine_update_user_banned_table():
	log.log("Start of the daily update thread")
	global random_state
	global flag_routine_update_user_banned_table
	flag_routine_update_user_banned_table = True
	
	#S'execute tout les jours à 6 heures du matin
	#time.sleep(60*60*6 + 60*60*24 - (datetime.datetime.now().second + datetime.datetime.now().minute*60 + datetime.datetime.now().hour*60*60))
	while flag_routine_update_user_banned_table:
		log.log("| It's time for an iteration of the update thread |")
		log.log("Part 1/3")

		array_of_users_info = mysql.get_all_users(connection_bd)
		for user in array_of_users_info: #0: primary_key / 1:user_id / 2:user_name / 3:user_type / 4:access_token / 5:refresh_token
					
			user_id = user[1]
			user_name = user[2]
			user_access_token = user[4]
			user_refresh_token = user[5]
			log.log("Update of user {} informations".format(user_name))
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
					log.log("User {} have Receive_Only OFF. We fetch all banned accounts from his channel".format(user_id))
					#appeler twitch allo les bannis stp
					list_of_banned_users_by_user = twitch.get_banlist(user_id, user_access_token, client_id)
					#imput les bannies dans la datatababbaaasee
					mysql.fill_banned_user_table_by_user(connection_bd, list_of_banned_users_by_user, user_id)
				else:
					log.log("User {} have Receive_Only ON. All ban made by Arias_bot are unmade on his channel".format(user_id))
					#If ON we must remove all banned user by Arias_bot from the channel
					list_of_banned_user = twitch.get_banlist(user_id, user_access_token, client_id, filter = False)
					list_of_unbanned_user = []
					for banned_user in list_of_banned_user:
						if("User automaticaly ban by Arias_bot." in banned_user["reason"]):
							list_of_unbanned_user.append(banned_user)
					twitch.unban_all(user_id, user_access_token, list_of_unbanned_user, client_id)

			
		#--------------------------------------------------------------------

		#Ici on recupt la list a ban et on la compare a la table master pour voir qui de la table master on unban
		log.log("Part 2/3")
		array_of_users_info = mysql.get_all_users(connection_bd)
		list_of_banned_user_from_master = mysql.get_all_master_banlist(connection_bd)

		list_of_banned_user = []
		for user in array_of_users_info: #0: primary_key / 1:user_id / 2:user_name / 3:user_type / 4:access_token / 5:refresh_token
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

		log.log("Unbanning banned accounts not fetch anymore and still registered")
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
		log.log("Update of the Master banlist with new fetched banned accounts")
			
			
		#---------------------------------------------------------------------

		log.log("Part 3/3")
		for user in array_of_users_info: #0: primary_key / 1:user_id / 2:user_name / 3:user_type / 4:access_token / 5:refresh_token		
			user_id = user[1]
			user_access_token = user[4]
			#If Give-Only option is off or None we can ban on this channel
			if (mysql.get_user_option(connection_bd, user_id)["giveonly"] == "Error"):
				log.log("Give_Only option is unreadable, we skip the banning phase for user {}".format(user_id))
			else:
				if (mysql.get_user_option(connection_bd, user_id)["giveonly"] == 1):
					log.log("Give_Only option is ON for user {}, we skip the banning phase for this user")
				else:
					log.log("Give_Only option is OFF for user {}, we can proceide with the banning phase for this user".format(user_id))
					list_of_banned_user = mysql.get_all_master_banlist(connection_bd)
					twitch.ban_from_master_banlist(connection_bd, user_id, user_access_token, list_of_banned_user, client_id)

		#---------------------------------------------------------------------

		log.log("| End of this iteration for the update thread |")
		#time.sleep(60*60*24)
		flag_routine_update_user_banned_table = False

	log.log("End of the daily update thread")
	random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
	random_state_list.append(random_state)
	try:
		return render_template('pages/home.html', user_autorisation_url = user_autorisation_url + random_state)
	except:
		pass


#---------------------------------------------------------------------------------------------------------------------#


def run_discord_bot():

	@discord_bot.event
	async def on_ready():
		global channel
		channel= discord.get_discord_channel(discord_bot, "bot-commands")
		log.log("Discord bot succesfully online and ready")
		await channel.send("I am reborn.")

	@discord_bot.event
	async def on_message(message):
		if message.author == discord_bot.user:
			return

		username = str(message.author)
		user_message = str(message.content)
		channel = message.channel
		user_roles = message.author.roles
		user_roles_name = [role.name for role in user_roles]

		#print(f"{username} said: '{user_message}' ({str(channel)})")

		if channel == discord.get_discord_channel(discord_bot, "bot-commands"):

			if "Admin" in user_roles_name:
				if user_message[0] == '!' or user_message[0] == '/':
					if "stop" in user_message or "close" in user_message:
						await message.channel.send("Bot is closing, Bye.")
						log.log("Discord bot is closing")
						await discord_bot.close()
						return

					if "update" in user_message:
						await message.channel.send("Force update de Arias_bot.")
						log.log("Forced iteration of the update thread by discord bot")
						routine_update_user_banned_table()
						return

					if user_message[:4] == "!ban":
						try:
							id = user_message[5:]
							await message.channel.send("User {} banned from the network.".format(id))
							log.log("Member {} have been banned from the network for discord bot".format(id))
							mysql.add_ban_member(connection_bd, id)
						except:
							await message.channel.send("Wrong format: !ban <id>")
						return
						

					if user_message[:6] == "!unban":
						try:
							id = user_message[7:]
							await message.channel.send("User {} unbanned from the network.".format(id))
							log.log("Member {} have been unbanned from the network for discord bot".format(id))
							mysql.remove_ban_member(connection_bd, id)
						except:
							await message.channel.send("Wrong format: !unban <id>")
						return
						

					if user_message[:6] == "!getid":
						try:
							name = user_message[7:]
							id = mysql.get_user_id_by_name(connection_bd, name)
							await message.channel.send("User {} got this id: {}".format(name,id))
							log.log("Member with id {} have the name {} from discord bot".format(id,name))
						except:
							await message.channel.send("Wrong format: !getid <name>")
						return

			if user_message[0] == '!' or user_message[0] == '/':
					if "code" in user_message:
						random_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
						available_discord_code.append(random_code)
						await message.author.send("A new code has been generated: {}".format(random_code))
						log.log("A new code has been generated : {} for user {}".format(random_code,username))
						await message.channel.send("@{} A new code has been generated, check your private message".format(username))
						return
			
					
	discord_bot.run(discord_token)
	log.log("Discord bot terminated")



@app.route('/discord_code_validation', methods=['POST'])
def discord_code_validation():
	log.log("Attempting to submit a discord generated code")
	received_code = request.form["discord_code"]
	if received_code in available_discord_code:
		available_discord_code.remove(received_code)
		random_state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
		random_state_list.append(random_state)
		log.log("Codes matching, authentifaction succesfull, returning to home page")
		return render_template('pages/home.html', acces_granted="", user_autorisation_url = user_autorisation_url + random_state)
	else:
		log.log("Codes mismatching, authentification failed, returning to entree page")
		return render_template('pages/entree.html')



#---------------------------------------------------------------------------------------------------------------------#

if __name__ == '__main__':
	log.log("Start of the main script")
	app_access_token = twitch.token_generation(client_id,client_secret)
	#thread_update_user_banned_table = threading.Thread(target = routine_update_user_banned_table)
	THREAD_discord_bot = threading.Thread(target = run_discord_bot)
	THREAD_discord_bot.start()
	log.log("Start of the discord bot")
	log.log("Start of flask web app")
	app.run(debug=False, port=5000)
	log.end_log()







#C:\Users\adrie\Documents\Twitch_project>virtual_env\scripts\activate.bat
#                                      .\virtual_env\Scripts\activate.ps1