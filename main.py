import logging, codecs, time
from telegramBot import TelegramBot
from oldMessageDeleter import OldMessageDeleter

MESSAGE_RETAINTION_DURATION = 7*24*60*60 #Retain a week of data
POLL_INTERVAL = 5*60

if __name__ == "__main__":
	with open('data/token', 'r') as f:
		telegramBot = TelegramBot(codecs.encode(f.read().replace('\n', ''), "rot-13"))
	oldMessageDeleter = OldMessageDeleter(telegramBot, "data/oldMessageDeleter.db", MESSAGE_RETAINTION_DURATION)
	telegramBot.setLogFile('data/chat.log', logging.DEBUG)

	telegramBot.setUpdateOffsetFilenameAndLoadOffset("data/updateOffset")
	telegramBot.attachHook(oldMessageDeleter.newMessageHandler)
	telegramBot.startPolling(POLL_INTERVAL, 0)
	logging.debug('STARTUP:Bot initialized!')
	while True:
		oldMessageDeleter.performDeleteOldMessages()
		time.sleep(1)
