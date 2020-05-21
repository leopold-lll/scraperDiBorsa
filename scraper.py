#Requests				per scaricare la pagina html
#Bs4 (beautiful soup)	crea il dom data la stringa dell'html					
#Bs4 tutorials:			https://www.digitalocean.com/community/tutorials/how-to-scrape-web-pages-with-beautiful-soup-and-python-3
#						https://www.youtube.com/watch?v=sAuGH1Kto2I

#Selenium				simula un browser, click, eventi, form e bla bla bla
#Pythonanywhere			permette d'eseguire script python mediante scheduling

#The executable can be created with: $ pyinstaller --onefile scraper.py

import requests as req
from bs4 import BeautifulSoup as bs
import pandas as pd

from datetime import datetime, date, time
import os


def scrape_withPandas(url):
	#Do not use (is an early version...
	#Warning: this method has the problem that pandas automatically convert the number(str) to number, but it does not consider the comma (,) as decimal delimiter
	print("\nWarning: pandas to not convert correctly float number")

	dfs = pd.read_html(url, decimal=',') #the comma separator does not work: decimal=','

	dailyStats = dfs[0]			#get the first table
	print(dailyStats)
	values = dfs[0][1].tolist()	#second column to list
	return(values[2:0:-1])

def scrape_withBS(url):
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


def loadData(filePath, companies, sep=','):
	fileName, fileExtension = os.path.splitext(filePath)
	if   os.path.exists(filePath) and fileExtension == '.csv':
		df = pd.read_csv(filePath, sep=sep)
	elif os.path.exists(filePath) and fileExtension == '.pkl':
		df = pd.read_pickle(filePath)
	else:
		header = flat([createHeaders(c) for c in companies])	#create header
		df = pd.DataFrame([], columns=header)
	
	return df.values.tolist()

def saveData(filePath, df, append, sep=','):
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
	

def createHeaders(name):
	return([ name+" min",  name+" max",  name+" delta" ])

def flat(ll):
	return([ el for l in ll for el in l ])

def isNaN(num):
    return num != num


def loadTargets(f_targets, sep=','):
	if os.path.exists(f_targets):
		targets_df = pd.read_csv(f_targets, sep=sep)

		#companies = targets_df['nome'].tolist()	#extract based on Serie name
		companies = targets_df.iloc[:, 0].tolist()	#extract based on Serie index
		urls = targets_df.iloc[:, 1].tolist()		#extract based on Serie index
		return(companies, urls)

def processCompanies(archive, companies, urls):
	#initialization
	header = []
	dailyMeasure = []
	header.append(["data", "ora"])
	dailyMeasure.append([ date.today().strftime("%d/%m/%Y") ])
	dailyMeasure.append([ datetime.now().strftime("%H:%M:%S") ])

	for company, url in zip(companies, urls):
		print("\nprocessing:", company)
		header.append( createHeaders(company) )

		values = scrape_withBS(url)				#returns open, max, min
		delta = round(values[1] - values[0], 3) #max-min
		values.append(delta)					#AKA min, max, delta

		values = ['{:.3f}'.format(v) for v in values]
		print("\tCollected data:", values)
		dailyMeasure.append(values)

	#Update archive and store it to file
	archive.append(flat(dailyMeasure))
	return pd.DataFrame(archive, columns=flat(header))


def main():
	#Load company names and urls from file
	f_targets = "titoli.csv"
	companies, urls = loadTargets(f_targets, sep=';')

	#Load the existing df or create a new one
	append = False	#flag to append, instead of overwrite. 
	#NB: the append DOES NOT write the column headers, could be a problem with new companies and/or with the first record at all...
	f_archive = "andamentoTitoli.csv"
	if append:
		archive = []
	else:
		archive = loadData(f_archive, companies, sep=';')

	#Process all the companies
	df_archive = processCompanies(archive, companies, urls)
	saveData(f_archive, df_archive, append, sep=';')
		

if __name__ == "__main__":
	main()