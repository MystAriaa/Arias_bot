from package import twitch_connector as twitch
from package import mysql_connector as mysql

connection_bd = mysql.connect_to_database()
    
#mysql.remove_banned_user_from_master_banlist(connection_bd, 161641887)

