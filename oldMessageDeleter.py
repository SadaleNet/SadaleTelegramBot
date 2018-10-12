from telegramBot import TelegramBot
import sqlite3
import urllib
import threading
import logging
import time

class OldMessageDeleter:
	def __init__(self, bot:TelegramBot, databaseName:str, retaintionDuration:int):
		self.MESSAGE_DELETION_API_CALL_TIMEOUT = 30
		self._bot = bot
		self._databaseName = databaseName
		self._retaintionDuration = retaintionDuration
		self._connections = {} #key: threadid; value: connection
		self._connectionsRLock = threading.RLock()
		connection = sqlite3.connect(self._databaseName)
		c = connection.cursor()
		c.execute("CREATE TABLE IF NOT EXISTS messages (datetime DATETIME, messageId INTEGER, chatId INTEGER, deleted BOOLEAN)")
		connection.commit()
		connection.close()
	def _obtainDatabaseConnection(self):
		with self._connectionsRLock:
			if threading.get_ident() not in self._connections:
				self._connections[threading.get_ident()] = sqlite3.connect(self._databaseName)
			connection = self._connections[threading.get_ident()]
		return connection
	def newMessageHandler(self, jsonData):
		connection = self._obtainDatabaseConnection()
		if "message" in jsonData:
			#These conditions are guaranteed by Telegram API. But we'd like to be sure about that. No harm to have sanitization.
			if not "message_id" in jsonData["message"]:
				return
			if not "date" in jsonData["message"]:
				return
			if not "chat" in jsonData["message"] and "id" in jsonData["message"]["chat"]:
				return

			messageId = jsonData["message"]["message_id"]
			dt = jsonData["message"]["date"]
			chatId = jsonData["message"]["chat"]["id"]

			c = connection.cursor()
			c.execute("INSERT INTO messages (datetime, messageId, chatId, deleted) VALUES (?, ?, ?, ?)", (dt, messageId, chatId, False))
			logging.debug("MESSAGE_DELETER:Saved message data:"+str([dt, messageId, chatId, False]))
			connection.commit()
	def performDeleteOldMessages(self):
		connection = self._obtainDatabaseConnection()
		c = connection.cursor()
		for row in c.execute('SELECT rowid, chatId, messageId FROM messages WHERE datetime < ? AND NOT deleted', (int(time.time()-self._retaintionDuration),)):
			rowid, chatId, messageId = row
			try:
				self._bot.callApi("deleteMessage", {"chat_id": chatId, "message_id": messageId}, self.MESSAGE_DELETION_API_CALL_TIMEOUT)
				c.execute('UPDATE messages SET deleted = TRUE WHERE rowid = ?', (rowid,))
				logging.info("MESSAGE_DELETER:Deleted {} {}".format(chatId, messageId))
			except urllib.error.HTTPError as response:
				logging.error("MESSAGE_DELETER:HTTP Error:"+response.read().decode("utf-8"))
				if response.code == 400:
					c.execute('UPDATE messages SET deleted = TRUE WHERE rowid = ?', (rowid,))
					logging.info("MESSAGE_DELETER:Deleted {} {}".format(chatId, messageId))
			except urllib.error.URLError as response:
				logging.error("MESSAGE_DELETER:URL Error:"+str(response.reason))
		connection.commit()
