from mysql.connector import connect, Error
from package import log
from package import tag_filter
import os


#This is messy i know, i made them as i need them, so they are repetive an can completly be fused.
#I'll do it, one day, for now, it's working, not optimal, but it's working.


delay_s = 1
bdd_name = "Arias_bot_database"
bdd_ip = "localhost"
bdd_login = "Arias_bot"
bdd_password = "1212"

def connect_to_database(host=bdd_ip, user=bdd_login, password=bdd_password, database=bdd_name):
    try:
        with connect(host=host, user=user, password=password, database=database) as connection:
            return(connection)
    except Error as e:
        return(e)


def create_the_database(connection):
    command = "CREATE DATABASE Arias_bot_database"
    with connection.cursor() as cursor:
        cursor.execute(command)


def create_table_registered_user(connection):
    command = """
        CREATE TABLE registered_user(
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT(15),
            user_name VARCHAR(30),
            access_token VARCHAR(50),
            refresh_token VARCHAR(50)
            );
        ALTER TABLE registered_user ADD UNIQUE INDEX(user_id, user_name);"""
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        connection.commit()


def create_table_banned_by_user(connection, user_id):
    command = """
        CREATE TABLE {0}_banlist(
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT(15),
            user_name VARCHAR(30),
            reason VARCHAR(500),
            start_date VARCHAR(30),
            expire VARCHAR(30),
            moderator_id INT(15),
            moderator_name VARCHAR(50)
            );
        ALTER TABLE {0}_banlist ADD UNIQUE INDEX(user_id, user_name);""".format(user_id)
    
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Table banlist crée avec succès pour l'utilisateur: {}".format(user_id))
        log.log("Altération de la table réussi")

    except:
        log.log("Echec de la création de la table banlist pour l'utilisateur: {}. Peut-etre celle-ci existe dèja ?".format(user_id))


def create_table_banlist_master(connection):
    command = """
        CREATE TABLE master_banlist(
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT(15),
            user_name VARCHAR(30),
            reason VARCHAR(500),
            start_date VARCHAR(30),
            expire VARCHAR(30),
            moderator_id INT(15),
            moderator_name VARCHAR(50),
            origin_channel_id INT(15)
            );
        ALTER TABLE master_banlist ADD UNIQUE INDEX(user_id, user_name);
        """
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        connection.commit()

def create_table_user_filter(connection):
    command = """
        CREATE TABLE filter_user(
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT(15),
            permanent TINYINT(1),
            timeout TINYINT(1),
            commented TINYINT(1),
            notcommented TINYINT(1),
            sexism TINYINT(1),
            homophobia TINYINT(1),
            rascism TINYINT(1),
            backseat TINYINT(1),
            spam TINYINT(1),
            username TINYINT(1),
            other TINYINT(1)
            );
        ALTER TABLE filter_user ADD UNIQUE INDEX(user_id);
        """
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        connection.commit()

def create_table_banned_tag(connection):
    command = """
        CREATE TABLE banned_tag(
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT(15),
            permanent TINYINT(1),
            timeout TINYINT(1),
            commented TINYINT(1),
            notcommented TINYINT(1),
            sexism TINYINT(1),
            homophobia TINYINT(1),
            rascism TINYINT(1),
            backseat TINYINT(1),
            spam TINYINT(1),
            username TINYINT(1),
            other TINYINT(1)
            );
        ALTER TABLE banned_tag ADD UNIQUE INDEX(user_id);
        """
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        connection.commit()


def create_table_option_user(connection):
    command = """
        CREATE TABLE option_user(
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT(15),
            giveonly TINYINT(1)
            );
        ALTER TABLE option_user ADD UNIQUE INDEX(user_id);
        """
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        connection.commit()


#-----------------------------------------------------------------------------------------------------------------


def input_a_new_user(connection, user_id, user_name, access_token, refresh_token):
    try: #Ajout
        command = """
            INSERT INTO registered_user (user_id, user_name, access_token, refresh_token) VALUES ({}, "{}", "{}", "{}");
            """.format(user_id, user_name, access_token, refresh_token)
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Ajout avec succes d'un nouvelle utilisateur")
    except: #if already in, update token
        log.log("Echec de l'ajout d'un utilisateur due à un doublon surement")
        set_new_user_info(connection, user_id, access_token, refresh_token)
        log.log("Update avec succes d'un utilisateur")


def remove_an_user(connection, user_id):
    command = """DELETE FROM registered_user WHERE user_id = "{}";""".format(user_id)
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Nous avons supprimé un utilisateur")
    except:
        log.log("Nous n'avons pas réussi à supprimé un utilisateur")


#---------MASTER BAN LIST AREA--------------------------------------------------------------------------#

def get_all_master_banlist(connection):
    #command = """SELECT user_id,reason,origin_channel_id FROM master_banlist;"""
    command = """SELECT * FROM master_banlist;"""
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        list_of_banned_user = cursor.fetchall()
    return (list_of_banned_user)
def delete_all_master_banlist(connection):
    try:
        command = """DELETE FROM master_banlist;"""
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Succes du netoyage de la master banlist")
    except:
        log.log("Echec du netoyage de la master banlist")
def insert_list_banned_into_master(connection, list_of_banned_user, user_id):
    for banned_user in list_of_banned_user:
        command = """INSERT INTO master_banlist 
        (user_id, user_name, reason, start_date, expire, moderator_id, moderator_name, origin_channel_id) 
        VALUES ({}, "{}", "{}", "{}", "{}", "{}", "{}", {});
        """.format(banned_user[1],banned_user[2],banned_user[3],banned_user[4],banned_user[5],banned_user[6],banned_user[7],user_id)
        try:
            connection.reconnect()
            with connection.cursor() as cursor:
                cursor.execute(command)
                connection.commit()
            log.log("Ajout d'un nouvel utilisateur bannis dans la master banlist.")
        except:
            log.log("Un utilisateur bannis n'a pas été rajouté à la master banlist car déja présent.")
def remove_ban_from_user_in_master(connection, user_id):
    command = """SELECT * FROM {}_banlist;""".format(user_id)
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        list_of_banned_user = cursor.fetchall()

    for banned_user in list_of_banned_user:
        try:
            command = """DELETE FROM master_banlist WHERE user_id = {};""".format(banned_user[1])
            connection.reconnect()
            with connection.cursor() as cursor:
                cursor.execute(command)
                connection.commit()
            log.log("Retrait de l'utilisateur {} de la banlist".format(banned_user[3]))
        except:
            log.log("Echec du retrait de l'utilisateur {} de la banlist".format(banned_user[3]))

def remove_list_user_in_master(connection, list):
    for banned_user in list:
        try:
            command = """DELETE FROM master_banlist WHERE user_id = {};""".format(banned_user[1])
            connection.reconnect()
            with connection.cursor() as cursor:
                cursor.execute(command)
                connection.commit()
            log.log("Retrait de l'utilisateur {} de la banlist".format(banned_user[3]))
        except:
            log.log("Echec du retrait de l'utilisateur {} de la banlist".format(banned_user[3]))


#---------USER AREA--------------------------------------------------------------------------#


def get_all_users(connection):
    command = """SELECT * FROM registered_user;"""
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        result = cursor.fetchall()
        return (result)
def get_user_id_by_name(connection, user_name):
    command = """SELECT user_id FROM registered_user WHERE user_name = "{}";""".format(user_name)
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        result = cursor.fetchall()
        return (result[0][0])
def get_user_name_by_id(connection, user_id):
    command = """SELECT user_name FROM registered_user WHERE user_id = "{}";""".format(user_id)
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        result = cursor.fetchall()
        return (result[0][0])
def get_user_info_by_id(connection, user_id):
    command = """SELECT * FROM registered_user WHERE user_id = {};""".format(user_id)
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        result = cursor.fetchall()
        return (result[0])
def get_user_info_by_access_token(connection, access_token):
    command = """SELECT * FROM registered_user WHERE access_token = "{}";""".format(access_token)
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        result = cursor.fetchall()
        return (result[0])
def set_new_user_info(connection, user_id, new_access_token, new_refresh_token):
    command = """
        UPDATE registered_user 
        SET access_token = '{1}', refresh_token = '{2}'
        WHERE user_id={0};""".format(user_id, new_access_token, new_refresh_token)
    connection.reconnect()
    with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()

def get_all_user_table(connection, user_id):
    command = """SELECT * FROM {}_banlist""".format(user_id)
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        list_of_banned_user = cursor.fetchall()
    return(list_of_banned_user)

def fill_banned_user_table_by_user(connection, list_of_banned_users, user_id):
    command = """DELETE FROM {}_banlist;""".format(user_id)
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Mise à neuf de la table {}_banlist".format(user_id))
    except:
        log.log("Delete all from failled")

    for banned_user in list_of_banned_users:
        try:
            expire = banned_user["expires_at"]
        except:
            expire = ""
        command = """
        INSERT INTO {0}_banlist
        (user_id, user_name, reason, start_date, expire, moderator_id, moderator_name) 
        VALUES ({1}, "{2}", "{3}", "{4}", "{5}", "{6}", "{7}");
        """.format(user_id,banned_user["user_id"],banned_user["user_name"],
        banned_user["reason"],banned_user["created_at"],expire,banned_user["moderator_id"],banned_user["moderator_name"])
        try:
            connection.reconnect()
            with connection.cursor() as cursor:
                cursor.execute(command)
                connection.commit()
            log.log("Un utilisateur bannis à été ajouté à la table {}_banlist".format(user_id))
        except:
            log.log("Un utilisateur bannis à été filtré car déja présent dans la table {}_banlist".format(user_id))


    for banned_user in list_of_banned_users:
        try:
            expire = banned_user["expires_at"]
        except:
            expire = ""
        t = tag_filter.extract_tag(banned_user["reason"],expire)

        command = """
        INSERT INTO banned_tag
        (user_id, permanent, timeout, commented, notcommented, sexism, homophobia, rascism, backseat, spam, username, other)
        VALUE ({},{},{},{},{},{},{},{},{},{},{},{});
        """.format(banned_user["user_id"],t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8],t[9],t[10])
        try:
            connection.reconnect()
            with connection.cursor() as cursor:
                cursor.execute(command)
                connection.commit()
            log.log("Un utilisateur bannis à été affublé de tags")
        except:
            log.log("Un utilisateur bannis n'à pas été affublé de tags car deja present surement")


def get_tag_by_id(connection, user_id):
    command = """
    SELECT permanent, timeout, commented, notcommented, sexism, homophobia, rascism, backseat, spam, username, other FROM banned_tag WHERE user_id = {}
    """.format(user_id)
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        list_of_tag = cursor.fetchall()
        tuple_of_tag = list_of_tag[0]
    dict = {"permanent": tuple_of_tag[0], "timeout": tuple_of_tag[1], "commented": tuple_of_tag[2], "notcommented": tuple_of_tag[3], "sexism": tuple_of_tag[4], "homophobia": tuple_of_tag[5], "rascism": tuple_of_tag[6], "backseat": tuple_of_tag[7],"spam": tuple_of_tag[8],"username": tuple_of_tag[9],"other": tuple_of_tag[10]}
    return(dict)


#---------FILTER AREA--------------------------------------------------------------------------#


def remove_list_user_from_tag_table(connection, list_user):
    for user in list_user:
        command = """DELETE FROM banned_tag WHERE user_id = {};""".format(user[1])
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Les datas(tags) d'un utilisateur unban on été éffacé")
    except:
        log.log("Les datas(tags) d'un utilisateur unban n'on pas pu etre éffacé")

def get_user_filter(connection, user_id):
    command = """SELECT * FROM filter_user WHERE user_id = {}""".format(user_id)
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            result = cursor.fetchall()
            tuple = result[0]
            #final = [tuple[2],tuple[3],tuple[4],tuple[5],tuple[6],tuple[7],tuple[8],tuple[9],tuple[10],tuple[11],tuple[12]]
            final = []
            for e in tuple:
                final.append(e)
            final.pop(0)
            final.pop(0)
            return (final)
    except:
        return [1,0,1,1,1,1,1,0,0,0,1] #default filter

def set_user_filter(connection, user_id, f):
    t = []
    for e in f:
        t.append(int(e))
    command = """
    INSERT INTO filter_user
    (user_id, permanent, timeout, commented, notcommented, sexism, homophobia, rascism, backseat, spam, username, other)
    VALUE ({0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11});""".format(user_id,t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8],t[9],t[10])
    log.log("Ajout de nouvelles données de filtre pour l'user {}".format(user_id))
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Nouvelles préference de filtre pour l'user {}".format(user_id))
    except:
        log.log("Echec de l'ajout de data surment deja existante")

def update_user_filter(connection, user_id, f):
    t = []
    for e in f:
        t.append(int(e))
    command = """
    INSERT INTO filter_user
    (user_id, permanent, timeout, commented, notcommented, sexism, homophobia, rascism, backseat, spam, username, other)
    VALUE ({0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11});""".format(user_id,t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8],t[9],t[10])
    log.log("Ajout de nouvelles données de filtre pour l'user {}".format(user_id))
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Nouvelles préference de filtre pour l'user {}".format(user_id))
    except:
        log.log("Echec de l'ajout de data surment deja existante")

    command = """ 
    UPDATE filter_user 
    SET permanent='{}',timeout='{}', commented='{}', notcommented='{}', sexism='{}', homophobia='{}', rascism='{}', backseat='{}', spam='{}', username='{}', other='{}'
    WHERE user_id = {};
    """.format(t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8],t[9],t[10],user_id)
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Mise à jour des filtres pour l'user {}".format(user_id))
    except:
        log.log("Echec de la mise à jour des filtres pour l'user {}".format(user_id))



def get_bannable_id_by_filter(connection, user_filter_pref):
    #Fonction that get a list of banned_user_id select in fonction of the user preferene via filter
    #A litte bit complicated but we do Unions and Intersections like so
    # ((perma)U(timeout)) I ((commented)U(notcommented)) I ((sexism)U(homophobia)U(rascism)U(backseat)U(spam)U(username)U(other))
    #user_filter_pref = [1,0,1,0,1,0,0,0,0,0,1]
    
    dict_1 = {"permanent": user_filter_pref[0], "timeout": user_filter_pref[1]}
    dict_2 = {"commented": user_filter_pref[2], "notcommented": user_filter_pref[3]}
    dict_3 = {"sexism": user_filter_pref[4], "homophobia": user_filter_pref[5], "rascism": user_filter_pref[6], "backseat": user_filter_pref[7],"spam": user_filter_pref[8],"username": user_filter_pref[9],"other": user_filter_pref[10]}
    list_of_id_1 = []
    for key,value in dict_1.items():
        if (value == 1):
            command = """SELECT user_id FROM banned_tag WHERE {}={};""".format(key,value)
            try:
                connection.reconnect()
                with connection.cursor() as cursor:
                    cursor.execute(command)
                    r = cursor.fetchall() #output like this [(1241590,), (155230646,), (264625375,), (442565528,), (454713337,)]
                    for e in r:
                        list_of_id_1.append(e[0])
            except:
                    pass
    list_of_id_1 = [list_of_id_1[i] for i in range(len(list_of_id_1)) if i == list_of_id_1.index(list_of_id_1[i])] #Remove duplicates

    #select comment or not and intersection 
    list_of_id_2 = []
    for key,value in dict_2.items():
        if (value == 1):
            command = """SELECT user_id FROM banned_tag WHERE {}={};""".format(key,value)
            try:
                connection.reconnect()
                with connection.cursor() as cursor:
                    cursor.execute(command)
                    r = cursor.fetchall()
                    for e in r:
                        list_of_id_2.append(e[0])
            except:
                    pass
    list_of_id_2 = [list_of_id_2[i] for i in range(len(list_of_id_2)) if i == list_of_id_2.index(list_of_id_2[i])] #Remove duplicates

    temp_list = [value for value in list_of_id_1 if value in list_of_id_2] #intersection

    #need to exclude not wanted tag
    list_of_id_3 = []
    for key,value in dict_3.items():
        if (value == 1):
            command = """SELECT user_id FROM banned_tag WHERE {}={};""".format(key,value)
            try:
                connection.reconnect()
                with connection.cursor() as cursor:
                    cursor.execute(command)
                    r = cursor.fetchall()
                    for e in r:
                        list_of_id_3.append(e[0])
            except:
                    pass
    list_of_id_3 = [list_of_id_3[i] for i in range(len(list_of_id_3)) if i == list_of_id_3.index(list_of_id_3[i])] #Remove duplicates
    
    final = [value for value in temp_list if value in list_of_id_3]
    return (final)


#----------------USER OPTION-----------------------------------------------------------------------------------------

def set_user_option(connection, user_id, option_list):
    command = """
    INSERT INTO option_user
    (user_id, giveonly)
    VALUE ({},{})
    """.format(user_id,option_list[0])
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Ajout de nouvelle options pour l'user {}".format(user_id))
    except:
        log.log("Echec de l'ajout de nouvelle options pour l'user {}".format(user_id))

def update_user_option(connection, user_id, option_list):
    command = """
    UPDATE option_user 
    SET giveonly='{1}'
    WHERE user_id = {0};
    """.format(user_id, option_list[0])
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Update d'options pour l'user {}".format(user_id))
    except:
        log.log("Echec de l'update d'options pour l'user {}".format(user_id))

def get_user_option(connection, user_id):
    command = """
    SELECT giveonly FROM option_user
    WHERE user_id = '{}';""".format(user_id)
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            r = cursor.fetchall()[0]
            dict = {"giveonly": r[0]}
            return(dict) #Only sent out giveonly as tuple look like [(0,)]
    except:
        pass

def delete_user_option(connection, user_id):
    command = """
    DELETE FROM option_user WHERE user_id = {}
    """.format(user_id)
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Effacement d'options pour l'user {}".format(user_id))
    except:
        log.log("Echec de l'effacement d'options pour l'user {}".format(user_id))






















if __name__ == '__main__':
    connection = connect_to_database()
