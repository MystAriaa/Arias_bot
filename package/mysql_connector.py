from mysql.connector import connect, Error
from package import log
from package import tag_filter
import os


#This is messy i know, i made them as i need them, so they are repetive an can completly be fused.
#I'll do it, one day, for now, it's working, not optimal, but it's working.


delay_s = 1
bdd_name = "arias_bot_database"
bdd_ip = os.environ["AWS_IP"]
bdd_login = os.environ["Arias_bot_login"]
bdd_password = os.environ["Arias_bot_password"]

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
            user_type VARCHAR(10),
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
        log.log("Successfully created banned accounts table for user {}".format(user_id))
    except Exception as e:
        log.log("Failed to create banned accounts table for user {}".format(user_id))
        log.log(str(e))


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
            other TINYINT(1),
            trusted TINYINT(1)
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
            other TINYINT(1),
            trusted TINYINT(1)
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
            giveonly TINYINT(1),
            receiveonly TINYINT(1)
            );
        ALTER TABLE option_user ADD UNIQUE INDEX(user_id);
        """
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        connection.commit()


def create_table_banned_member(connection):
    command = """
        CREATE TABLE banned_member(
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT(15),
            user_name VARCHAR(30)
            );
        ALTER TABLE banned_member ADD UNIQUE INDEX(user_id);
        """
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        connection.commit()


#-----------------------------------------------------------------------------------------------------------------


def input_a_new_user(connection, user_id, user_name, user_type, access_token, refresh_token):
    log.log("Adding a new user {}, {} to the database".format(user_id,user_name))
    try: #Ajout
        command = """
            INSERT INTO registered_user (user_id, user_name, user_type, access_token, refresh_token) VALUES ({}, "{}", "{}", "{}", "{}");
            """.format(user_id, user_name, user_type, access_token, refresh_token)
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("User {}, {} successfully registered in the database".format(user_id,user_name))
    except Exception as e: #if already in, update token
        log.log("User {}, {} failed to be registered in the database".format(user_id,user_name))
        log.log(str(e))
        log.log("Trying to update user {}, {} informations in the database".format(user_id,user_name))
        set_new_user_info(connection, user_id, access_token, refresh_token)
        log.log("Update of user {}, {} successfull in the database".format(user_id,user_name))


def remove_an_user(connection, user_id):
    log.log("Deleting user {} from the database".format(user_id))
    command = """DELETE FROM registered_user WHERE user_id = "{}";""".format(user_id)
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("User {} successfully deleted from the database".format(user_id))
    except Exception as e:
        log.log("Deletion of user {} failed from the database".format(user_id))
        log.log(str(e))


#---------MASTER BAN LIST AREA--------------------------------------------------------------------------#

def get_all_master_banlist(connection):
    log.log("Called get_all_master_banlist")
    command = """SELECT * FROM master_banlist;"""
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            list_of_banned_user = cursor.fetchall()
        log.log("Returned: {}".format(list_of_banned_user))
        return (list_of_banned_user)
    except Exception as e:
        log.log("Returned: []")
        log.log(str(e))
        return([])
def delete_all_master_banlist(connection):
    log.log("Called delete_all_master_banlist")
    command = """DELETE FROM master_banlist;"""
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Total whipeout of Master banlist successfull")
    except Exception as e:
        log.log("Failed to wipeout Master banlist")
        log.log(str(e))
def insert_list_banned_into_master(connection, list_of_banned_user, user_id):
    log.log("Called insert_list_banned_into_master")
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
            log.log("Added successfully user {}, {} into Master banlist".format(banned_user[1],banned_user[2]))
        except Exception as e:
            log.log("Failed to add user {}, {} into Master banlist".format(banned_user[1],banned_user[2]))
            log.log(str(e))
def remove_ban_from_user_in_master(connection, user_id):
    log.log("Called remove_ban_from_user_in_master")
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
            log.log("User {}, {} remove from Master banlist".format(banned_user[1],banned_user[2]))
        except Exception as e:
            log.log("Failed to remove user {}, {} from Master banlist".format(banned_user[1],banned_user[2]))
            log.log(str(e))

def remove_list_user_in_master(connection, list):
    log.log("Called remove_list_user_in_master")
    for banned_user in list:
        try:
            command = """DELETE FROM master_banlist WHERE user_id = {};""".format(banned_user[1])
            connection.reconnect()
            with connection.cursor() as cursor:
                cursor.execute(command)
                connection.commit()
            log.log("User {}, {} remove from Master banlist".format(banned_user[1],banned_user[2]))
        except Exception as e:
            log.log("Failed to remove user {}, {} from Master banlist".format(banned_user[1],banned_user[2]))
            log.log(str(e))


#---------USER AREA--------------------------------------------------------------------------#


def get_all_users(connection):
    log.log("Called get_all_users")
    command = """SELECT * FROM registered_user;"""
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        result = cursor.fetchall()
        return (result)
def get_user_id_by_name(connection, user_name):
    log.log("Called get_user_id_by_name")
    command = """SELECT user_id FROM registered_user WHERE user_name = "{}";""".format(user_name)
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        result = cursor.fetchall()
        return (result[0][0])
def get_user_name_by_id(connection, user_id):
    log.log("Called get_user_name_by_id")
    command = """SELECT user_name FROM registered_user WHERE user_id = "{}";""".format(user_id)
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        result = cursor.fetchall()
        return (result[0][0])
def get_user_info_by_id(connection, user_id):
    log.log("Called get_user_info_by_id")
    command = """SELECT * FROM registered_user WHERE user_id = {};""".format(user_id)
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        result = cursor.fetchall()
        return (result[0])
def get_user_info_by_access_token(connection, access_token):
    log.log("Called get_user_info_by_access_token")
    command = """SELECT * FROM registered_user WHERE access_token = "{}";""".format(access_token)
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        result = cursor.fetchall()
        return (result[0])
def set_new_user_info(connection, user_id, new_access_token, new_refresh_token):
    log.log("Called set_new_user_info")
    command = """
        UPDATE registered_user 
        SET access_token = '{1}', refresh_token = '{2}'
        WHERE user_id={0};""".format(user_id, new_access_token, new_refresh_token)
    connection.reconnect()
    with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()

def get_all_user_table(connection, user_id):
    log.log("Called get_all_user_table")
    command = """SELECT * FROM {}_banlist""".format(user_id)
    connection.reconnect()
    with connection.cursor() as cursor:
        cursor.execute(command)
        list_of_banned_user = cursor.fetchall()
    return(list_of_banned_user)

def fill_banned_user_table_by_user(connection, list_of_banned_users, user_id):
    log.log("Called fill_banned_user_table_by_user")
    user_type = get_user_info_by_id(connection, user_id)[3]
    if user_type == "":
        user_type = 0
    else:
        user_type = 1

    command = """DELETE FROM {}_banlist;""".format(user_id)
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Successfully wipeout table {}_banlist".format(user_id))
    except Exception as e:
        log.log("Failed to wipeout table {}_banlist".format(user_id))
        log.log(str(e))

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
            log.log("A new user {} has been added in table {}_banlist".format(banned_user["user_id"],user_id))
        except Exception as e:
            log.log("Failed to add a new user {} in table {}_banlist".format(banned_user["user_id"],user_id))
            log.log(str(e))


    for banned_user in list_of_banned_users:
        try:
            expire = banned_user["expires_at"]
        except:
            expire = ""
        t = tag_filter.extract_tag(banned_user["reason"],expire)

        command = """
        INSERT INTO banned_tag
        (user_id, permanent, timeout, commented, notcommented, sexism, homophobia, rascism, backseat, spam, username, other, trusted)
        VALUE ({},{},{},{},{},{},{},{},{},{},{},{},{});
        """.format(banned_user["user_id"],t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8],t[9],t[10],user_type)
        try:
            connection.reconnect()
            with connection.cursor() as cursor:
                cursor.execute(command)
                connection.commit()
            log.log("Successfully added tags to user {} in banned_tag table".format(banned_user["user_id"]))
        except Exception as e:
            log.log("Failed to add tags to user {} in banned_tag table".format(banned_user["user_id"]))
            log.log(str(e))

        command = """
        UPDATE banned_tag
        SET permanent={}, timeout={}, commented={}, notcommented={}, sexism={}, homophobia={}, rascism={}, backseat={}, spam={}, username={}, other={}, trusted={}
        WHERE user_id = {};
        """.format(t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8],t[9],t[10],user_type,banned_user["user_id"])
        try:
            connection.reconnect()
            with connection.cursor() as cursor:
                cursor.execute(command)
                connection.commit()
            log.log("Successfully updated tags for user {} in banned_tag table".format(banned_user["user_id"]))
        except Exception as e:
            log.log("Failed to update tags for user {} in banned_tag table".format(banned_user["user_id"]))
            log.log(str(e))




def get_tag_by_id(connection, user_id):
    log.log("Called get_tag_by_id")
    command = """
    SELECT permanent, timeout, commented, notcommented, sexism, homophobia, rascism, backseat, spam, username, other, trusted FROM banned_tag WHERE user_id = {}
    """.format(user_id)
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            list_of_tag = cursor.fetchall()
            tuple_of_tag = list_of_tag[0]
        dict = {"permanent": tuple_of_tag[0], "timeout": tuple_of_tag[1], "commented": tuple_of_tag[2], "notcommented": tuple_of_tag[3], "sexism": tuple_of_tag[4], "homophobia": tuple_of_tag[5], "rascism": tuple_of_tag[6], "backseat": tuple_of_tag[7],"spam": tuple_of_tag[8],"username": tuple_of_tag[9],"other": tuple_of_tag[10],"trusted": tuple_of_tag[11]}
        log.log("Successfully returning filter tags for user {}: {}".format(user_id,dict))
        return(dict)
    except Exception as e:
        log.log("Failed to return filter tags for user {}".format(user_id))
        log.log(str(e))
        return({"permanent": 0, "timeout": 0, "commented": 0, "notcommented": 0, "sexism": 0, "homophobia": 0, "rascism": 0, "backseat": 0,"spam": 0,"username": 0,"other": 0,"trusted": 0})


#---------FILTER AREA--------------------------------------------------------------------------#


def remove_list_user_from_tag_table(connection, list_user):
    log.log("Called remove_list_user_from_tag_table")
    for user in list_user:
        command = """DELETE FROM banned_tag WHERE user_id = {};""".format(user[1])
        try:
            connection.reconnect()
            with connection.cursor() as cursor:
                cursor.execute(command)
                connection.commit()
            log.log("Successfully removed user {} from banned_tag table".format(user[1]))
        except Exception as e:
            log.log("Failed to remove user {} from banned_tag table".format(user[1]))
            log.log(str(e))

def get_user_filter(connection, user_id):
    log.log("Called get_user_filter")
    command = """SELECT * FROM filter_user WHERE user_id = {}""".format(user_id)
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            result = cursor.fetchall()
            tuple = result[0]
            final = []
            for e in tuple:
                final.append(e)
            final.pop(0)
            final.pop(0)
            log.log("Successfully returning filter options for user {}: {}".format(user_id,final))
            return (final)
    except Exception as e:
        log.log("Failed to get filter options for user {}. Returning [1,0,1,1,1,1,1,0,0,0,1,0]".format(user_id))
        log.log(str(e))
        return [1,0,1,1,1,1,1,0,0,0,1,0] #default filter

def set_user_filter(connection, user_id, f):
    log.log("Called set_user_filter")
    t = []
    for e in f:
        t.append(int(e))
    command = """
    INSERT INTO filter_user
    (user_id, permanent, timeout, commented, notcommented, sexism, homophobia, rascism, backseat, spam, username, other, trusted)
    VALUE ({0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12});""".format(user_id,t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8],t[9],t[10],t[11])
    log.log("Trying to add new filter options for user {}".format(user_id))
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Successfully added new filter options for user {}".format(user_id))
    except Exception as e:
        log.log("Failed to add new filter option for user {}".format(user_id))
        log.log(str(e))

def update_user_filter(connection, user_id, f):
    log.log("Called update_user_filter")
    t = []
    for e in f:
        t.append(int(e))
    command = """
    INSERT INTO filter_user
    (user_id, permanent, timeout, commented, notcommented, sexism, homophobia, rascism, backseat, spam, username, other, trusted)
    VALUE ({0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12});""".format(user_id,t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8],t[9],t[10],t[11])
    log.log("Ajout de nouvelles données de filtre pour l'user {}".format(user_id))
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Successfully added new filter options for user {}".format(user_id))
    except Exception as e:
        log.log("Failed to add new filter option for user {}".format(user_id))
        log.log(str(e))

    command = """ 
    UPDATE filter_user 
    SET permanent='{}',timeout='{}', commented='{}', notcommented='{}', sexism='{}', homophobia='{}', rascism='{}', backseat='{}', spam='{}', username='{}', other='{}', trusted='{}'
    WHERE user_id = {};
    """.format(t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8],t[9],t[10],t[11],user_id)
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Successfully updated filter options for user {}".format(user_id))
    except Exception as e:
        log.log("Failed to update filter options for user {}".format(user_id))
        log.log(str(e))



def get_bannable_id_by_filter(connection, user_filter_pref):
    log.log("Called get_bannable_id_by_filter")
    #Fonction that get a list of banned_user_id select in fonction of the user preferene via filter
    #A litte bit complicated but we do Unions and Intersections like so
    # ((perma)U(timeout)) I ((commented)U(notcommented)) I ((sexism)U(homophobia)U(rascism)U(backseat)U(spam)U(username)U(other) I (trusted)U(nottrusted))
    #user_filter_pref = [1,0,1,0,1,0,0,0,0,0,1]
    
    dict_1 = {"permanent": user_filter_pref[0], "timeout": user_filter_pref[1]}
    dict_2 = {"commented": user_filter_pref[2], "notcommented": user_filter_pref[3]}
    dict_3 = {"sexism": user_filter_pref[4], "homophobia": user_filter_pref[5], "rascism": user_filter_pref[6], "backseat": user_filter_pref[7],"spam": user_filter_pref[8],"username": user_filter_pref[9],"other": user_filter_pref[10]}
    trusted_value_filter = user_filter_pref[11]

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

    temp_list1 = [value for value in list_of_id_1 if value in list_of_id_2] #intersection

    if (dict_2["notcommented"] == 1):
        temp_list2 = temp_list1
    else:
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
        
        temp_list2 = [value for value in temp_list1 if value in list_of_id_3]

    list_of_id_4 = []
    if trusted_value_filter == 1:
        command = """SELECT user_id FROM banned_tag WHERE trusted = 1;"""
        try:
            connection.reconnect()
            with connection.cursor() as cursor:
                cursor.execute(command)
                r = cursor.fetchall()
                for e in r:
                    list_of_id_4.append(e[0])
        except:
            pass
        final = [value for value in temp_list2 if value in list_of_id_4]
    else:
        final = temp_list2
    return (final)


#----------------USER OPTION-----------------------------------------------------------------------------------------

def set_user_option(connection, user_id, option_list):
    log.log("Called set_user_option")
    command = """
    INSERT INTO option_user
    (user_id, giveonly, receiveonly)
    VALUE ({},{},{})
    """.format(user_id,option_list[0],option_list[1])
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Successfully added filter options for user {}".format(user_id))
    except Exception as e:
        log.log("Failed to add filter options for user {}".format(user_id))
        log.log(str(e))

def update_user_option(connection, user_id, option_list):
    log.log("Called update_user_option")
    command = """
    UPDATE option_user 
    SET giveonly='{1}', receiveonly='{2}'
    WHERE user_id = {0};
    """.format(user_id, option_list[0], option_list[1])
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Successfully updated user {} filter options".format(user_id))
    except Exception as e:
        log.log("Failed to update filtet options for user {}".format(user_id))
        log.log(str(e))

def get_user_option(connection, user_id):
    log.log("Called get_user_option")
    command = """
    SELECT giveonly, receiveonly FROM option_user
    WHERE user_id = '{}';""".format(user_id)
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            r = cursor.fetchall()[0]
            dict = {"giveonly": r[0], "receiveonly": r[1]}
            log.log("Successfully returned user {} filter options: {}".format(user_id,dict))
            return(dict) #Only sent out giveonly as tuple look like [(0,)]
    except Exception as e:
        log.log("Failed to return user {} filter options. Returned Error".format(user_id))
        log.log(str(e))
        return("Error")

def delete_user_option(connection, user_id):
    log.log("Called delete_user_option")
    command = """
    DELETE FROM option_user WHERE user_id = {}
    """.format(user_id)
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("Successfully removed filter options for user {}".format(user_id))
    except Exception as e:
        log.log("Failed to remove filter options for user {}".format(user_id))
        log.log(str(e))



#---------------BAN MEMBER---------------------------------------------------------------------------------------------------

def add_ban_member(connection, id):
    log("Called add_ban_member")
    command = """
    INSERT INTO banned_member
    (user_id, user_name)
    VALUE ({},{})
    """.format(id,"0")
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("User {} successfully added to banned_member table".format(id))
    except Exception as e:
        log.log("Failed to add user {} to banned_member table".format(id))
        log.log(str(e))

def remove_ban_member(connection, id):
    log.log("Called remove_ban_member")
    command = """
    DELETE FROM banned_member WHERE user_id = {}
    """.format(id)
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            connection.commit()
        log.log("User {} successfully removed from banned_member table".format(id))
    except Exception as e:
        log.log("Failed to remove user {} from banned_member table".format(id))
        log.log(str(e))

def get_all_ban_member(connection):
    log.log("Called get_all_ban_member")
    command = """SELECT user_id FROM banned_member;"""
    try:
        connection.reconnect()
        with connection.cursor() as cursor:
            cursor.execute(command)
            r = cursor.fetchall()
            l = [str(e) for e in r[0]]
            log.log("Successfully return all banned members from the network: {}".format(l))
            return(l) #Only sent out giveonly as tuple look like [(0,)]
    except Exception as e:
        log.log("Failed to return all banned members from the network. Returned Error")
        log.log(str(e))
        return("Error")












if __name__ == '__main__':
    connection = connect_to_database()
