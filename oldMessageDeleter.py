import sqlite3

class OldMessageDeleter:
	def __init__(self, databaseName, retaintionDuration):
		self.databaseName = databaseName
		self.retaintionDuration = retaintionDuration
		connection = sqlite3.connect(self.databaseName)
		c = connection.cursor()
		c.execute("CREATE TABLE IF NOT EXISTS messages (datetime DATETIME, messageId INTEGER, chatId INTEGER, deleted BOOLEAN)")
		connection.commit()
		connection.close()
	def newMessageHandler(self, jsonData):
		print(jsonData)
		if "message" in jsonData:
			#These conditions are guaranteed by Telegram API. But we'd like to be sure about that. No harm to have sanitization.
			if not "message_id" in jsonData["message"]:
				return
			if not "date" in jsonData["message"]:
				return
			if not "chat" in jsonData["message"] and "id" in jsonData["message"]["chat"]:
				return

			connection = sqlite3.connect(self.databaseName)
			messageId = jsonData["message"]["message_id"]
			dt = jsonData["message"]["date"]
			chatId = jsonData["message"]["chat"]["id"]

			c = connection.cursor()
			c.execute("INSERT INTO messages (datetime, messageId, chatId, deleted) VALUES (?, ?, ?, ?)", (dt, messageId, chatId, False))
			connection.commit()
			connection.close()
	def deleteOldMessages(self):
		pass #TODO: SELECT (messageId, chatId) FROM WHERE datetime >= ? , then delete all of them!
