import unittest
import os, logging, codecs, time, threading, sqlite3
from telegramBot import TelegramBot
from oldMessageDeleter import OldMessageDeleter

TOKEN_FILE = "data/test/token"
LOG_FILE = "data/test/chat.log"
OLD_MESSAGES_DB_FILE = "data/test/oldMessageDeleter.db"
UPDATE_OFFSET_FILE = "data/test/updateOffset"
MESSAGE_POLLING_INTERVAL = 10
API_RESPONSE_MAX_DELAY = 20
MESSAGE_RESPOSE_DELAY = MESSAGE_POLLING_INTERVAL+API_RESPONSE_MAX_DELAY
TEST_GROUPS_ID = [
				("Usual Group", -235608864), #Usual group
				("Super Group", -1001357958274) #Super group
				]


class TelegramBotTestCase(unittest.TestCase):
	def setUp(self):
		if os.path.exists(UPDATE_OFFSET_FILE):
			os.remove(UPDATE_OFFSET_FILE)
		if os.path.exists(LOG_FILE):
			os.remove(LOG_FILE)
		self.receptionDetectedLock = threading.RLock()

		with open(TOKEN_FILE, 'r') as f:
			self.telegramBot = TelegramBot(codecs.encode(f.read().replace('\n', ''), "rot-13"))
		self.telegramBot.setLogFile(LOG_FILE, logging.DEBUG)
		self.telegramBot.setUpdateOffsetFilenameAndLoadOffset(UPDATE_OFFSET_FILE)

	def startPollingDecorator(func):
		def wrapper(*args, **kwargs):
			self = args[0]
			self.telegramBot.startPolling(MESSAGE_POLLING_INTERVAL, 0)

			# Wait for the first message update to get completed, which we're going to disregard
			print("Waiting for all previous messages to get received...")
			time.sleep(MESSAGE_RESPOSE_DELAY)
			func(*args, **kwargs)

			self.telegramBot.stopPolling()
			self.telegramBot.waitStopPolling()
		return wrapper

	def receptionDetectionHook(self, message):
		with self.receptionDetectedLock:
			self.receptionDetected = True

	@startPollingDecorator
	def test_message_reception(self):
		testStartTime = time.time()
		updateOffsetWritten = False

		self.telegramBot.attachHook(self.receptionDetectionHook)
		for testGroup in TEST_GROUPS_ID:
			testGroupName, testGroupId = testGroup
			with self.receptionDetectedLock:
				self.receptionDetected = False
			# Send a message
			# Apparently Telegram doesn't allow bots to receive other bots messages
			# So we have to manually send the message
			'''
			self.telegramBot.callApi("sendMessage",
									 {"chat_id": testGroupId, "text": binascii.b2a_hex(os.urandom(16)).decode("ascii")},
									 API_RESPONSE_MAX_DELAY)
			'''
			input('*** Please manually send a message to {} and press <enter> ***'.format(testGroupName))
			print('waiting for message reception...')
			# Wait and check if it's detected
			time.sleep(MESSAGE_RESPOSE_DELAY)
			with self.receptionDetectedLock:
				self.assertTrue(self.receptionDetected, "Sent message didn't get received by the bot")
		self.telegramBot.detachHook(self.receptionDetectionHook)

	def test_log_file_exists(self):
		time.sleep(5)
		self.assertTrue(os.path.exists(LOG_FILE))

	@startPollingDecorator
	def test_message_deletion(self):
		testStartTime = time.time()
		updateOffsetWritten = False
		retainDuration = 50
		if os.path.exists(OLD_MESSAGES_DB_FILE):
			os.remove(OLD_MESSAGES_DB_FILE)
		oldMessageDeleter = OldMessageDeleter(self.telegramBot, OLD_MESSAGES_DB_FILE, retainDuration)

		connection = sqlite3.connect(OLD_MESSAGES_DB_FILE)
		c = connection.cursor()
		c.execute('SELECT COUNT(*) FROM messages')
		messageCount, = c.fetchone()
		self.assertEqual(messageCount, 0, "The database isn't empty at the beginning")

		self.telegramBot.attachHook(oldMessageDeleter.newMessageHandler)
		for testGroup in TEST_GROUPS_ID:
			testGroupName, testGroupId = testGroup
			with self.receptionDetectedLock:
				self.receptionDetected = False
			input('*** Please manually send a message to {} and press <enter> ***'.format(testGroupName))
			print('waiting for message reception...')
			# Wait until the message got received
			time.sleep(MESSAGE_RESPOSE_DELAY)
			# Check if the entity got recorded to our database
			print("Ensure that the entity got recorded into the database...")
			c.execute('SELECT chatId FROM messages')
			result = c.fetchall()
			self.assertEqual(len(result), 1,
				"No messages were recorded into the database, or more than one messages were received.")
			self.assertEqual(result[0][0], testGroupId, "Wrong group ID.")



			oldMessageDeleter.performDeleteOldMessages()
			print("Ensure that the entity is not deleted too early...")
			c.execute('SELECT COUNT(*) FROM messages')
			messageCount, = c.fetchone()
			self.assertEqual(messageCount, 1, "The message were deleted too early")

			print("Wait for the message to get deleted...")
			time.sleep(retainDuration)
			oldMessageDeleter.performDeleteOldMessages()
			print("Ensure that the message is deleted...")
			c.execute('SELECT COUNT(*) FROM messages')
			messageCount, = c.fetchone()
			self.assertEqual(messageCount, 0, "The message was not deleted")

		self.telegramBot.detachHook(oldMessageDeleter.newMessageHandler)


if __name__ == "__main__":
	unittest.main()
