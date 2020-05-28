#Requests				per scaricare la pagina html
#Bs4 (beautiful soup)	crea il dom data la stringa dell'html					
#Bs4 tutorials:			https://www.digitalocean.com/community/tutorials/how-to-scrape-web-pages-with-beautiful-soup-and-python-3
#						https://www.youtube.com/watch?v=sAuGH1Kto2I

#Selenium				simula un browser, click, eventi, form e bla bla bla
#Pythonanywhere			permette d'eseguire script python mediante scheduling

#The executable can be created with: $ pyinstaller --onefile scraper.py
#The requirements for the project were created with: $ pip3 freeze > requirements.txt

import requests as req
from bs4 import BeautifulSoup as bs
import pandas as pd

from datetime import datetime, date, time, timedelta
import os

from googleDriveAPI.googleDriveAPI import GDriveInterface


from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files	import GoogleDriveFile
from googleapiclient.discovery import build
import os
import shutil

#################################   Scraping functions   ###################################################

def scrape_withPandas(url):
	""" Deprecated: scrape the url given. """
	#Warning: this method has the problem that pandas automatically convert the number(str) to number, but it does not consider the comma (,) as decimal delimiter
	print("\nWarning: pandas to not convert correctly float number")

	dfs = pd.read_html(url, decimal=',') #the comma separator does not work: decimal=','

	dailyStats = dfs[0]			#get the first table
	print(dailyStats)
	values = dfs[0][1].tolist()	#second column to list
	return(values[2:0:-1])

def scrape_withBS(url: str) -> list:
	""" Scrape the url given. """
	values = [0,0,0]
	if isNaN(url):
		print("\tMissing link")
	else:
		#Download the page with requests
		page = req.get(url)

		#Create a BeautifulSoup object (the DOM)
		soup = bs(page.text, 'html.parser')	

		#Extract the table from the DOM
		#table = soup.table					#wrapper for find('table')
		table = soup.find('table')			#find only the first table that occour -> equal to find_all('table')[0]
		#table = soup.find_all('table')[0]	#find all the tables and list them

		#Process the DOM
		rows_leftColumns = table.find_all(class_='t-text -right')	#extraction based on a class
		#_ = table.find_all('span')									#extraction based on tag

		values = []
		for el in rows_leftColumns[2:0:-1]:	#iteration 0°=max - 1°=min
			v = el.text.replace(',','.')	#extract the text content of each element
			if v!='':
				values.append(float(v))		#convert the numbers (save as string) into number
			else:
				values.append(0)			#coorner case for empty values online
		
	return(values)


#################################   Interaction with OS   ##################################################

def loadData(filePath: str, companies: list, sep: str=',') -> "list of list":
	""" Load the dataframe stored in the file given (.csv or .pkl), otherwise it create a new one. """
	fileName, fileExtension = os.path.splitext(filePath)

	if os.path.exists(filePath) and fileExtension == '.csv':
		df = pd.read_csv(filePath, sep=sep, dtype=object)
		#dtype=object force pandas to consider the number (int or float) as string while loading the csv
		#this guarantee that a number as 0.202 or 45.400 is not converted, solving 2 problems:
		#1) the deletion of the precision (3 decimal digits) by removing zeros: 45.400 != 45.4
		#2) the approsimation of a float do not influence a string: 0.202 != 0.201999999999999

	elif os.path.exists(filePath) and fileExtension == '.pkl':
		df = pd.read_pickle(filePath)
	else:
		#create new dataframe
		header = flat([createHeaders(c) for c in companies])	#create header
		df = pd.DataFrame([], columns=header)
	
	return df.values.tolist()

def saveData(filePath: str, df: pd.DataFrame, append: bool, sep: str=',') -> None:
	""" Save the dataframe given to the specified path as a csv file. """
	fileName, fileExtension = os.path.splitext(filePath)
	if append:
		print("\nAppend procedure")
		mode = 'a'
		h = not os.path.exists(filePath) #set the header if first call of the process
	else:
		
		print("\nOverride procedure")
		mode = 'w'
		h = True

	df.to_csv(filePath, mode=mode, header=h, index=False, sep=sep)
	print("Data are saved.")
	

#################################   Support functions   ####################################################

def isWorkingDay() -> bool:
	""" Check if today is a worrking day or not. """
	day = date.today().weekday()
	#This respect, more or less, the period when the borsa's website has consistent data.
	return( day<5 or (day==5 and datetime.now().hour<5) )

def createHeaders(name: str) -> list:
	""" Format an header list. """
	return([ name+" min",  name+" max",  name+" delta" ])

def flat(ll: "list of list") -> list:
	""" Transform a 2D list (aka Mat) into a 1D list. """
	return([ el for l in ll for el in l ])

def isNaN(num: "url") -> bool:
	""" Check if the given url is not defined. """
	return num != num


#################################   Support functions   ####################################################

def loadTargets(f_targets: str, sep: str=',') -> (list, list):
	""" Load from the given file the companies list and the urls associated. """
	if os.path.exists(f_targets):
		targets_df = pd.read_csv(f_targets, sep=sep)

		#companies = targets_df['nome'].tolist()	#extract based on Serie name
		companies = targets_df.iloc[:, 0].tolist()	#extract based on Serie index
		urls = targets_df.iloc[:, 1].tolist()		#extract based on Serie index
		return(companies, urls)

def processCompanies(archive: "list of list", companies: list, urls: list) -> pd.DataFrame:
	""" Process each one of companies given, and store to a dataframe the values downloaded from the urls. """

	#Initialization
	header = []
	dailyMeasure = []

	#Corner case: data still online but referred to the previous day (the night is a better moment for scraping)
	header.append(["data", "ora"])
	now = datetime.now()
	today = date.today()
	if now.hour<5:			#borsa have not open and the online table (hopefully) is not reset yet
		yesterday = today - timedelta(days=1)
		dailyMeasure.append([ yesterday.strftime("%d/%m/%Y") ])
		dailyMeasure.append(["23:59:59"])
	else:					#today's borsa is running or is over
		dailyMeasure.append([ today.strftime("%d/%m/%Y") ])
		dailyMeasure.append([ now.strftime("%H:%M:%S") ])

	#For each company
	for company, url in zip(companies, urls):
		print("\nprocessing:", company)
		header.append( createHeaders(company) )

		#scrape data from the website
		values = scrape_withBS(url)				#returns min, max
		delta = round(values[1] - values[0], 3) #max-min
		values.append(delta)					#AKA min, max, delta

		#format the values to  be returned
		values = ['{:.3f}'.format(v) for v in values]
		print("\tCollected data:", values)
		dailyMeasure.append(values)

	#Update archive and store it to file
	archive.append(flat(dailyMeasure))
	return pd.DataFrame(archive, columns=flat(header))


#################################   Core of the program   ##################################################

def main():
	if isWorkingDay():
		#Set input & output file
		f_targets = "titoli.csv"
		f_archive = "andamentoTitoli.csv"

		#Login to GoogleDrive and download titoli.csv
		gDrive = GDriveInterface(	storeCredentials=True, printMessage=True, \
									credentialsFile="googleDriveAPI/myCredentials.json", clientSecrets="googleDriveAPI/client_secrets.json")
		gDrive.download("Archivio scraperDiBorsa/titoli.csv", f_targets)

		#Load company names and urls from file
		if not os.path.exists(f_targets):
			print("Error: the", f_targets, "file is missing nothing can be done...")
		else:
			companies, urls = loadTargets(f_targets, sep=';')

			#Load the existing df or create a new one
			append = False	#flag to append, instead of overwrite. 
			#NB: the append DOES NOT write the column headers, could be a problem with new companies and/or with the first record at all...
			if append:
				archive = []
			else:
				archive = loadData(f_archive, companies, sep=';')

			#Process all the companies
			df_archive = processCompanies(archive, companies, urls)
			saveData(f_archive, df_archive, append, sep=';')

			#Upload the generatted result on GoogleDrive
			gDrive.upload(f_archive, "Archivio scraperDiBorsa/andamentoTitoli.csv")
	else:
		#corner case -> no data to scrape
		print("Today the Borsa is closed, and the website has no data...")

if __name__ == "__main__":
	main()