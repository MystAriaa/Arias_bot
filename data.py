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

mysql.insert_list_banned_into_master

connection_bd = mysql.connect_to_database()

array_of_users_info = mysql.get_all_users(connection_bd)

for user in array_of_users_info:
    banned = mysql.get_all_user_table(connection_bd, user[1])
    mysql.insert_list_banned_into_master(connection_bd, banned, user[1])