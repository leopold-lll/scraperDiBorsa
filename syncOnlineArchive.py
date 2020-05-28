#The executable can be created with: $ pyinstaller --onefile syncOnlineArchive.py

from googleDriveAPI.googleDriveAPI import GDriveInterface

#################################   Core of the program   ##################################################

def main():
	#Login to GoogleDrive
	gDrive = GDriveInterface(	storeCredentials=True, printMessage=True, \
								credentialsFile="googleDriveAPI/myCredentials.json", clientSecrets="googleDriveAPI/client_secrets.json")

	#Download the archive
	archive = "andamentoTitoli.csv"
	gDrive.download("Archivio scraperDiBorsa/andamentoTitoli.csv", archive)

	#Upload data to scrape in the future
	titoli = "titoli.csv"
	gDrive.upload(titoli, "Archivio scraperDiBorsa/titoli.csv")

if __name__ == "__main__":
	main()