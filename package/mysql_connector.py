from mysql.connector import connect, Error

def connect_to_database(host="localhost", user="Arias_bot", password="1212", database="Arias_bot_database"):
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
            user_login VARCHAR(30),
            user_name VARCHAR(30),
            access_token VARCHAR(50),
            refresh_token VARCHAR(50));
        )"""
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        connection.commit()


def create_table_banned_by_user(connection, user_id):
    command = """
        CREATE TABLE {}_banlist(
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT(15),
            user_login VARCHAR(30),
            user_name VARCHAR(30),
            reason VARCHAR(500),
            moderator_id INT(15),
            moderator_login VARCHAR(50),
            moderator_name VARCHAR(50)
            );""".format(user_id)
    
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        print("Table banlist crée avec succès pour l'utilisateur: {}".format(user_id))
        
        try:
            command = """ALTER TABLE {}_banlist ADD UNIQUE INDEX(user_id, user_login, user_name);""".format(user_id)
            connection.reconnect()
            with connection.cursor() as cursor:
                cursor.execute(command)
                connection.commit()
            print("Altération de la table réussi")
        except:
            print("Echec de l'altération de la table")

    except:
        print("Echec de la création de la table banlist pour l'utilisateur: {}. Peut-etre celle-ci existe dèja ?".format(user_id))


def create_table_banlist_commune(connection):
    command = """
        CREATE TABLE master_banlist(
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT(15),
            user_login VARCHAR(30),
            user_name VARCHAR(30),
            reason VARCHAR(500),
            moderator_id INT(15),
            moderator_login VARCHAR(50),
            moderator_name VARCHAR(50),
            origin_channel_id INT(15)
            );
        ALTER TABLE master_banlist ADD UNIQUE INDEX(user_id, user_login, user_name);
        """
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        connection.commit()


def input_a_new_user(connection, user_id, user_login, user_name, access_token, refresh_token):
    try: #Ajout
        command = """
            INSERT INTO registered_user (user_id, user_login, user_name, access_token, refresh_token) VALUES ({}, "{}", "{}", "{}", "{}");
            """.format(user_id, user_login, user_name, access_token, refresh_token)
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        print("Ajout avec succes d'un nouvelle utilisateur")
    except: #delete le doublon et on le re-enregistre
        print("Echec de l'ajout d'un utilisateur due à un doublon surement")
        command = """
            DELETE FROM registered_user WHERE user_id={};
            """.format(user_id)
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()

        command = """
            INSERT INTO registered_user (user_id, user_login, user_name, access_token, refresh_token) VALUES ({}, "{}", "{}", "{}", "{}");
            """.format(user_id, user_login, user_name, access_token, refresh_token)
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        print("Update avec succes d'un utilisateur")

def remove_an_user(connection, user_id):
    command = """DELETE FROM registered_user WHERE user_id = "{}";""".format(user_id)
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        print("Nous avons supprimé un utilisateur")
    except:
        print("Nous n'avons pas réussi à supprimé un utilisateur")

def delete_all_master_banlist(connection):
    try:
        command = """DELETE FROM master_banlist;"""
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        print("Succes du netoyage de la master banlist")
    except:
        print("Echec du netoyage de la master banlist")
def remove_banned_user_from_master_banlist(connection, user_id):
    command = """SELECT * FROM {}_banlist;""".format(user_id) #Pas obligé de tout select
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
            print("Retrait de l'utilisateur {} de la banlist".format(banned_user[3]))
        except:
            print("Echec du retrait de l'utilisateur {} de la banlist".format(banned_user[3]))


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
def set_new_user_info(connection, user_id, new_access_token, new_refresh_token):
    command = """
        UPDATE registered_user 
        SET access_token = '{1}', refresh_token = '{2}'
        WHERE user_id={0};""".format(user_id, new_access_token, new_refresh_token)
    connection.reconnect()
    with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()


def fill_banned_user_table_by_user(connection, list_of_banned_users, user_id):
    command = """DELETE FROM {}_banlist;""".format(user_id)
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
    except:
        print("Delete all from failled")

    for banned_user in list_of_banned_users:
        command = """
        INSERT INTO {0}_banlist
        (user_id, user_login, user_name, reason, moderator_id, moderator_login, moderator_name) 
        VALUES ({1}, "{2}", "{3}", "{4}", "{5}", "{6}", "{7}");
        """.format(user_id,banned_user["user_id"],banned_user["user_login"],banned_user["user_name"],
        banned_user["reason"],banned_user["moderator_id"],banned_user["moderator_login"],banned_user["moderator_name"])
        try:
            connection.reconnect()
            with connection.cursor() as cursor:
                cursor.execute(command)
                connection.commit()
            print("Un utilisateur bannis à été ajouté à la table {}_banlist".format(user_id))
        except:
            print("Un utilisateur bannis à été filtré car déja présent dans la table {}_banlist".format(user_id))

    """#Remove banned user in database #DELETE all from table INSTEAD SIMPLER MAYBE NOT FASTER
    command = """"""
    try:
        connection.reconnect()
        cursor.execute(command)
        list_of_banned_id = cursor.fetchall()
        for banner_user_id in list_of_banned_id:
            if (banner_user_id in list_of_banned_users):

    except:"""


if __name__ == '__main__':
    connection = connect_to_database()