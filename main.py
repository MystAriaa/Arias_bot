import os
from flask import Flask, render_template, request
from package import twitch_connector as twitch
from package import mysql_connector as mysql
import threading
import time
import datetime



app = Flask(__name__)

site_base_url = "http://localhost:5000/autorisation_code"
client_id = twitch.get_client_id()
client_secret = twitch.get_client_secret()
scopes = ["moderation:read","moderator:manage:banned_users"] #"user:edit",
state = "example_state" #anti-CSRF attacks

user_autorisation_url = "https://id.twitch.tv/oauth2/authorize?response_type={0}&client_id={1}&redirect_uri={2}&scope={3}&state={4}".format("code",client_id,site_base_url,twitch.scope_format(scopes),state)

connection_bd = mysql.connect_to_database()

app_access_token = ""

user_code = ""
user_id = ""
user_login = ""
user_name = ""
user_access_token = ""
user_refresh_token = ""

flag_routine_update_user_banned_table = True

#---------------------------------------------------------------------------------------------------------------------#

@app.route('/')
def home():
    return render_template('pages/home.html', user_autorisation_url=user_autorisation_url)

@app.route('/contact')
def contact():
    return render_template('pages/contact.html')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('pages/page_not_found.html'), 404

@app.route('/autorisation_code')
def query():
    global app_access_token
    global user_code
    global user_id
    global user_login
    global user_name
    global user_access_token
    global user_refresh_token
    Acces_granted = False
    received_state = request.args.get('state')
    if (received_state == state):  #no cross attacks, we good

        error_state = request.args.get('error')               #error case
        if (error_state == "access_denied"):
            Acces_granted = False
            error_description = request.args.get('error_description')
            error_state = request.args.get('state')
            print("Nous avons un refus de l'utilisateur : {}.".format(error_description))
        else:                                                 #no error case
            Acces_granted = True
            code = request.args.get('code')
            user_code = code
            scope = request.args.get('scope')
            print("Nous avons reçu l'autorisation de l'utilisateur.")
            #print("Code: {}, Scope: {}, State: {}".format(code,scope,state))

    else:                          #cross attacks, not good
        raise Warning("We might be under a CSRF attack")


    #Si nous avons reçu le code
    if (Acces_granted):
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
    if (Acces_granted):
        return render_template('pages/autorisation_code.html',Acces_granted="Acces autorisé")
    else:
        return render_template('pages/autorisation_code.html',Acces_granted="Acces refusé")

@app.route('/stop')
def stop():
    global flag_routine_update_user_banned_table
    flag_routine_update_user_banned_table = False
    return render_template('pages/home.html', user_autorisation_url=user_autorisation_url)

@app.route('/start')
def start():
    global flag_routine_update_user_banned_table
    flag_routine_update_user_banned_table = True
    thread_update_user_banned_table.start()
    return render_template('pages/home.html', user_autorisation_url=user_autorisation_url)
    

#---------------------------------------------------------------------------------------------------------------------#

def routine_update_user_banned_table():
    print("Rentre dans le thread")
    #S'execute tout les jours à 6 heures du matin
    #time.sleep(60*60*6 + 60*60*24 - (datetime.datetime.now().second + datetime.datetime.now().minute*60 + datetime.datetime.now().hour*60*60))
    while flag_routine_update_user_banned_table:
        os.system('cls')
        print("| Voici une itération du thread |")
        print("1/3")

        array_of_users_info = mysql.get_all_users(connection_bd)
        time.sleep(1)
        for user in array_of_users_info: #0: primary_key / 1:user_id / 2:user_login / 3:user_name / 4:access_token / 5:refresh_token
                    
            user_id = user[1]
            user_name = user[3]
            user_access_token = user[4]
            user_refresh_token = user[5]
            print("Mise à jour des bannis pour {}".format(user_name))
            #check les access_token
            id = twitch.token_validation(user_access_token)
            if ( id == 0 or id == 1):
                user_access_token, user_refresh_token = twitch.token_refresh(connection_bd, client_id, client_secret, user_id=user_id, refresh_token=user_refresh_token, mode = "user")
            #appeler twitch allo les bannis stp
            list_of_banned_users_by_user = twitch.get_banlist(user_id, user_access_token, client_id)
            #imput les bannies dans la datatababbaaasee
            mysql.fill_banned_user_table_by_user(connection_bd, list_of_banned_users_by_user, user_id)
            time.sleep(1)
        #--------------------------------------------------------------------

        print("2/3")
        array_of_users_info = mysql.get_all_users(connection_bd)
        time.sleep(1)
        for user in array_of_users_info: #0: primary_key / 1:user_id / 2:user_login / 3:user_name / 4:access_token / 5:refresh_token
                    
            user_id = user[1]
            user_name = user[3]
            user_access_token = user[4]
            user_refresh_token = user[5]

            command = """SELECT * FROM {}_banlist""".format(user_id)
            connection_bd.reconnect()
            with connection_bd.cursor() as cursor:
                cursor.execute(command)
                list_of_banned_user = cursor.fetchall()
            
            print("Mise à jour de la master_banlist depuis l'utilisateur: {}({})".format(user_name,user_id))
            for banned_user in list_of_banned_user:
                command = """INSERT INTO master_banlist 
                (user_id, user_login, user_name, reason, moderator_id, moderator_login, moderator_name, origin_channel_id) 
                VALUES ({}, "{}", "{}", "{}", "{}", "{}", "{}", {});
                """.format(banned_user[1],banned_user[2],banned_user[3],banned_user[4],banned_user[5],banned_user[6],banned_user[7],user_id)
                try:
                    connection_bd.reconnect()
                    with connection_bd.cursor() as cursor:
                        cursor.execute(command)
                        connection_bd.commit()
                    print("Ajout d'un nouvel utilisateur bannis dans la master banlist.")
                except:
                    print("Un utilisateur bannis n'a pas été rajouté à la master banlist car déja présent.")
            
        #---------------------------------------------------------------------

        print("3/3")
        array_of_users_info = mysql.get_all_users(connection_bd)
        time.sleep(1)
        for user in array_of_users_info: #0: primary_key / 1:user_id / 2:user_login / 3:user_name / 4:access_token / 5:refresh_token
                    
            user_id = user[1]
            user_name = user[3]
            user_access_token = user[4]
            user_refresh_token = user[5]

            command = """SELECT user_id,reason,origin_channel_id FROM master_banlist;"""
            connection_bd.reconnect()
            with connection_bd.cursor() as cursor:
                cursor.execute(command)
                list_of_banned_user = cursor.fetchall()
            twitch.ban_from_master_banlist(connection_bd, user_id, user_access_token, list_of_banned_user, client_id)


        print("| Voici la fin de l'itération du thread |")
        #time.sleep(60*60*24)
        flag_routine_update_user_banned_table = False
        time.sleep(60)

    print("Sort du thread")

#---------------------------------------------------------------------------------------------------------------------#


if __name__ == '__main__':
    os.system('cls')

    app_access_token = twitch.token_generation(client_id,client_secret)

    thread_update_user_banned_table = threading.Thread(target = routine_update_user_banned_table)

    app.run(debug=True, port=5000)







#C:\Users\adrie\Documents\Twitch_project>virtual_env\scripts\activate.bat