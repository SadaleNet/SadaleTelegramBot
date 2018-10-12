import logging, codecs, time
from telegramBot import TelegramBot
from oldMessageDeleter import OldMessageDeleter

if __name__ == "__main__":
	telegramBot = TelegramBot(codecs.encode(open('data/token', 'r').read().replace('\n', ''), "rot-13"))
	oldMessageDeleter = OldMessageDeleter(telegramBot, "data/oldMessageDeleter.db", 20)

	telegramBot.setLogFile('data/chat.log', logging.DEBUG)
	telegramBot.setUpdateOffsetFilenameAndLoadOffset("data/updateOffset")
	telegramBot.attachHook(print)
	telegramBot.attachHook(oldMessageDeleter.newMessageHandler)
	telegramBot.startPolling(10, 0)
	logging.debug('STARTUP:Bot initialized!')
	while True:
		oldMessageDeleter.performDeleteOldMessages()
		time.sleep(1)
