from package import discord_connector as discord
from package import log
from package import mysql_connector as mysql
import string
import random
import os
import datetime
import time
import discord as d


discord_bot = discord.get_discord_client()
discord_token = discord.get_discord_token()

connection_bd = mysql.connect_to_database()

available_discord_code = []

log_folder_path = "logs/"


def run_discord_bot():

	@discord_bot.event
	async def on_ready():
		global channel
		channel= discord.get_discord_channel(discord_bot, "test-bot")
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

		if channel == discord.get_discord_channel(discord_bot, "test-bot"):

			if "Admin" in user_roles_name:
				if user_message[0] == '!' or user_message[0] == '/':
					if message.content.startswith('!stop') or message.content.startswith('!close'):
						await message.channel.send("Bot is closing, Bye.")
						log.log("Discord bot is closing")
						await discord_bot.close()
						return

			flag = False
			last_message = ""
			log_folder_path = "logs/"
			file_name = log.get_file_name()
			if message.content.startswith('!log start'):
				await channel.send("Logging ON")
				flag = True
				while flag:
					f = open(log_folder_path + file_name, 'r')
					lignes = f.readlines()
					f.close()

					try:
						if last_message != lignes[-1]:
							await channel.send(lignes[-1])
							last_message = lignes[-1]
					except:
						pass

					def check(msg: d.Message):
						return not msg.author.bot and msg.content.lower() == "!log stop"

					try:
						if await discord_bot.wait_for("message", check=check, timeout=2):
							flag = False
							await channel.send("Logging OFF")
					except:
						pass

					
	discord_bot.run(discord_token)
	log.log("Discord bot terminated")
	os.system("cls")



if __name__ == '__main__':
	run_discord_bot()