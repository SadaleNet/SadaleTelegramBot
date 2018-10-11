import logging, codecs, time
from telegramBot import TelegramBot
from oldMessageDeleter import OldMessageDeleter

if __name__ == "__main__":
	oldMessageDeleter = OldMessageDeleter("data/oldMessageDeleter.db", 100)
	
	telegramBot = TelegramBot(codecs.encode(open('data/token', 'r').read().replace('\n', ''), "rot-13"))
	telegramBot.setLogFile('data/chat.log', logging.DEBUG)
	telegramBot.attachHook(print)
	telegramBot.attachHook(oldMessageDeleter.newMessageHandler)
	telegramBot.startPolling(10, 0)
	logging.debug('STARTUP:Bot launched!')
	while True:
		time.sleep(1)
