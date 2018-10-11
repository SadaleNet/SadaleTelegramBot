import codecs
import threading
import json
import time
import logging
import sqlite3
import urllib.request
import urllib.parse

class TelegramBot:
	def __init__(self, apiKey):
		self._apiKey = apiKey
		self._pollDuration = -1
		self._pollUpdateOffset = 0
		self._pollVariablesLock = threading.RLock()
		self._updateHooks = []
		self._pollThread = None
	def setLogFile(self, filename:str, level=logging.INFO):
		logging.basicConfig(filename=filename, format='%(asctime)s:%(levelname)s:%(message)s', level=level)
	def attachHook(self, hook):
		self._updateHooks.append(hook)
	def detachHook(self, hook):
		self._updateHooks.remove(hook)
	def updateHandler(self, message):
		for hook in self._updateHooks:
			hook(message)
	def startPolling(self, pollDuration, updateOffset):
		self._pollVariablesLock.acquire()
		if self._pollDuration == -1:
			self._pollDuration = pollDuration
			self._pollVariablesLock.release()
			self.waitStopPolling()
			#Starts polling thread
			self._pollThread = threading.Thread(target=self._poll)
			self._pollThread.start()
		else:
			self._pollDuration = pollDuration
			self._pollVariablesLock.release()
	def stopPolling(self):
		self._pollVariablesLock.acquire()
		self._pollDuration = -1
		self._pollVariablesLock.release()
	def waitStopPolling(self):
		if self._pollThread != None:
			self._pollThread.join()
			self._pollThread = None
	def callApi(self, apiMethod:str, data:dict, timeout:float):
		return urllib.request.urlopen(
				urllib.request.Request(
						"https://api.telegram.org/bot{}/{}".format(self._apiKey, apiMethod),
						data=urllib.parse.urlencode(data).encode(),
						method="POST"),
					timeout=timeout
				)
	def _poll(self):
		self._pollVariablesLock.acquire()
		if self._pollDuration != -1:
			self._pollVariablesLock.release()
			try:
				logging.debug('POLLING:Sending getUpdates Request')
				with self.callApi("getUpdates", {"offset": self._pollUpdateOffset}, self._pollDuration+10) as response:
					responseData = response.read()
					try:
						jsonResponseData = json.loads(responseData)
						logging.info("POLLING:Response Received:"+responseData.decode("utf-8"))
						if jsonResponseData["ok"]:
							for data in jsonResponseData["result"]:
								if data["update_id"]+1 > self._pollUpdateOffset:
									self._pollUpdateOffset = data["update_id"]+1
								self.updateHandler(data)
						else:
							logging.warn("POLLING:Telegram API Error:"+responseData.decode("utf-8"))
					except json.JSONDecodeError as jsonError:
						logging.error("POLLING:Telegram API nvalid JSON payload:"+jsonError.msg+":"+responseData.decode("utf-8"))
			except urllib.error.HTTPError as response:
				logging.error("POLLING:HTTP Error:"+response.read().decode("utf-8"))
			time.sleep(5)
			self._poll()

