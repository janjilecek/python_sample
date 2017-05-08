# nazev: Fortuna Downloader
# autor: Bc. Jan Jilecek, janjilecek at gmail.com
# datum: 03.05.2017

import requests
from bs4 import BeautifulSoup
from collections import defaultdict, OrderedDict
import json, sys
from operator import itemgetter

def downloadCheck(func):
	def functionWrapper(name):
		try:
			func(name)
		except requests.exceptions.Timeout:
			try:
				name.retry()
			except ValueError:
				print(e)
				sys.exit(1)
		except (requests.exceptions.HTTPError, requests.exceptions.RequestException) as e:
			print(e)
			sys.exit(1)
		try:
			name.parsedData = BeautifulSoup(name.rawData, 'html.parser')
		except (ValueError, AttributeError, IOError) as e:
			print(e)
			sys.exit(1)
	return functionWrapper

class Downloader:
	def __init__(self):
		self.mUrl = "https://www.ifortuna.cz/cz/sazeni/"
		self.rawData = None
		self.parsedData = None
		self.session = requests.Session() # new requests session
		self.retries = 3
		self.tableHeader = []
		self.savedData = defaultdict(list)
		self.resultDictData = dict()
		self.resultOrdered = OrderedDict()	

	@downloadCheck
	def downloadData(self): # download the data with downloadCheck
		self.rawData = self.session.get(self.mUrl).text

	def retry(self):
		if self.retries > 0:
			self.retries -= 1
			self.retry()
		else:
			raise ValueError("Number of retries exceeded.")

	def getTableByClass(self, tableName):
		table = self.parsedData.findAll("table", id=tableName)
		for t in table:
			try:
				classes = t["class"]
				if "bet_table" in classes and "last_table" in classes:
					return (t, tableName)
			except:
				continue
		return (None, tableName)

	def getTableData(self, table):
		dct = defaultdict(list)
		thead = table[0].find("thead")
		tbody = table[0].find("tbody")

		tmpHead = []
		headRow = thead.find("tr")
		for th in headRow.findAll("th"):
			tmp = "--" if not th.span else th.span.text.strip() # use -- if no text found
			tmpHead.append(tmp if not th.a else th.a.text.strip())
		self.tableHeader = tmpHead

		i = 1 # we start indexing after header row
		bodyRow = tbody.findAll("tr")
		for r in bodyRow:
			for td in r.findAll("td"):
				try:
					s = td.div.span.text.replace("\n", " _ ")[:s.find("_")].strip()
					dct[i].append(s)
				except:
					try:
						dct[i].append(td.a.text.strip())
					except:
						try:
							dct[i].append(td.span.text.strip())
						except:
							dct[i].append("--")
							pass
			i+=1

		self.resultDictData[table[1]] = dct
		return dct

	def printData(self):
		#print(json.dumps(self.resultOrdered))
		for key, d in self.resultOrdered.items():
			for a in d:
				s = ""
				for b in a:
					s += str(b) + "\t"
				print(s)

	def checkFloat(self, s):
		try:
			return float(s)
		except ValueError:
			return s

	def exporter(self, fileName):
		with open(fileName, 'w') as f:
			json.dump(self.resultOrdered, f)

	def orderAllByCol(self): # order the dict by it's list values (columns) and save in ordered dict
		tmp = {k:sorted(v.values(), key=itemgetter(1)) for k,v in self.resultDictData.items()}
		orderedData = OrderedDict((k,v) for k,v in sorted(tmp.items(), key=lambda i: i[1]))
		orderedData["header"] = self.tableHeader	
		self.resultOrdered = orderedData

if __name__ == "__main__":
	dl = Downloader()

	dl.downloadData() # we download the website and parse it with BS4
	
	dl.getTableData(dl.getTableByClass("betTable-93-1")) # NHL table
	dl.getTableData(dl.getTableByClass("betTable-17-1")) # Premier League table

	dl.orderAllByCol() # order data by 'vyhra domaci'
	dl.printData() # we can print the data
	dl.exporter("output.json") # export to file