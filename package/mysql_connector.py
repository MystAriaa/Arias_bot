from mysql.connector import connect, Error
from package import log
from package import tag_filter
import os

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
    except: #delete le doublon et on le re-enregistre
        log.log("Echec de l'ajout d'un utilisateur due à un doublon surement")
        command = """
            DELETE FROM registered_user WHERE user_id={};
            """.format(user_id)
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()

        command = """
            INSERT INTO registered_user (user_id, user_name, access_token, refresh_token) VALUES ({}, "{}", "{}", "{}");
            """.format(user_id, user_name, access_token, refresh_token)
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
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
def remove_banned_user_from_master_banlist(connection, user_id):
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


if __name__ == '__main__':
    connection = connect_to_database()
