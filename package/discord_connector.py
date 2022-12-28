import discord
import random
import os


def get_discord_token():
	return os.environ["DISCORD_TOKEN"]

def init_unique_client():
	intents = discord.Intents.default()
	intents.message_content = True
	client = discord.Client(intents = intents)
	return client

unique_client = init_unique_client()

def get_discord_client():
	return unique_client

def get_discord_guild(client):
	return client.get_guild(1057337928868696195)

def get_discord_channel(client, name):
	if name == "bot-logs":
		return client.get_channel(1057339640257990656)
	elif name == "test-bot":
		return client.get_channel(1057356935541821460)
	elif name == "bot-commands":
		return client.get_channel(1057648114179260436)




"""def get_channel():
	return channel

def run_discord_bot():
	global server
	global channel
	print("Enter discord bot thread")

	server = 0
	channel = 0

	@unique_client.event
	async def on_ready():
		global channel
		global server
		print(f'{unique_client.user} is now running!')
		server = get_discord_guild(unique_client)
		channel = get_discord_channel(unique_client, "test-bot")
		await channel.send("I am reborn.")

	@unique_client.event
	async def on_message(message):
		if message.author == unique_client.user:
			return
		username = str(message.author)
		user_message = str(message.content)
		channel = str(message.channel)
		print(f"{username} said: '{user_message}' ({channel})")
		#await discord.send_message(message.channel, user_message)
		if user_message[0] == '!':
			if "stop" in str(user_message):
				print("closing")
				await message.channel.send("Bot is closing, Bye.")
				await unique_client.close()
				return

	unique_client.run(get_discord_token())


	print("Exit discord bot thread")"""