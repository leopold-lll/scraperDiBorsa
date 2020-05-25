from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from googleapiclient.discovery import build
import os

#pyDrive docs: https://pythonhosted.org/PyDrive/filemanagement.html

class Pippo:
	def __init__(self, *args, **kwargs):
		return super().__init__(*args, **kwargs)

class GDriveInterface:

	def __init__(self, storeCredentials=True, printMessage=True) -> None:
		self.printMessage = printMessage
		self.googleLogin(storeCredentials)

	def googleLogin(self, storeCredentials=True) -> None:
		#This function require the "client_secrets.json" file to launch the authentication procedure
		gauth = GoogleAuth()

		# Try to load saved client credentials
		if storeCredentials:
			gauth.LoadCredentialsFile("myCredentials.json")

		if gauth.credentials is None:
			# Authenticate if they're not there
			gauth.LocalWebserverAuth()
		elif gauth.access_token_expired:
			# Refresh them if expired
			gauth.Refresh()
		else:
			# Initialize the saved creds
			storeCredentials = False
			gauth.Authorize()

		if storeCredentials:
			# Save the current credentials to a file
			gauth.SaveCredentialsFile("myCredentials.json")
		self.drive = GoogleDrive(gauth)

	############################################################################################################

	def fInfo(self, f) -> str:
		#Work for both file and folder
		#print('location: %s, parents: %s' % (f['mimeType'], f['parents']))
		return('\tfile -> title: %s, id: %s, parents ID: %s' % (f['title'], f['id'], f['parents'][0].get('id')))

	def __stringListCompare(self, str, strList) -> bool:
		for el in strList:
			if el==str:
				return True
		return False

	def __separate_pathAndFile(self, path) -> (str, str):
		#The __ notation is a convention stating that this function is private to the class
		foldersNameList = path.strip('/').split('/')
		
		parent = '/'.join(foldersNameList[:-1])
		filename = foldersNameList[-1]
		return(parent, filename)

	############################################################################################################

	def getPathIDs(self, path) -> list:
		#This function return a list of the ids of the folders up to the end of the path

		#This question state that the tree of folder in google drive is a mess...
		#https://stackoverflow.com/questions/57113254/google-pydrive-function-to-use-as-os

		#Possible queary to drive:
		#file_list = self.drive.ListFile({'q': "'%s' in parents and trashed=false" % parent}).GetList()
		#file_list = self.drive.ListFile({'q': "'1WmwwykABr2VE4WzVwRgv8YhYkEZ1AC6A' in parents and trashed=false"}).GetList()
		#file_list = self.drive.ListFile({"q": "mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
		#file_list = self.drive.ListFile({"q": "'root' in parents and trashed=false"}).GetList()

		if path=="":
			#simply optimization
			return([])
		else:
			#Get all the folders form drive
			allFolder = self.drive.ListFile({"q": "mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()

			#Extract the folders that can match the path
			foldersNameList = path.split('/')	#the list of the name of folders from root
			plausibleFolders = []
			for f in allFolder:
				if self.__stringListCompare(str=f['title'], strList=foldersNameList):
					plausibleFolders.append(f)

			#Identify the first folder on the path
			foldersOnPath = []
			for f in plausibleFolders:
				#parent=root and check my name
				if f['parents'][0].get('isRoot') and f['title']==foldersNameList[0]:
					foldersOnPath.append(f)

			#Identify the remaining folders on the path
			for name in foldersNameList[1:]:
				for f in plausibleFolders:
					#check parent id and my name
					if f['parents'][0].get('id')==foldersOnPath[-1]['id'] and f['title']==name:
							foldersOnPath.append(f)

			#return the folders ids
			folderIDsOnPath = [f['id'] for f in foldersOnPath]
			return(folderIDsOnPath)


	def getFolderID(self, path) -> str:
		IDs = self.getPathIDs(path)
		if IDs is None:
			return None
		else:
			return IDs[-1]

		
	def getFileID(self, path) -> str:
		file = self.getFile(path)
		if file is None:
			return None
		else:
			return file['id']


	def getFolder_inLocation(self, parentID, filename): # -> GoogleDriveFile
		return self.getFile_inLocation(parentID, filename)

	def getFile_inLocation(self, parentID, filename): # -> GoogleDriveFile
		#It is a very efficient version of get file (simply because the location is already known)
		if parentID is None:
			file_list = self.drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
		else:
			file_list = self.drive.ListFile({'q': "'%s' in parents and trashed=false" % str(parentID)}).GetList()
		
		for f in file_list:
			if f['title'] == filename:
				return(f)
		return(None)


	def getFolder(self, path): # -> GoogleDriveFile
		return self.getFile(path)

	def getFile(self, path): # -> GoogleDriveFile
		parent, filename = self.__separate_pathAndFile(path)
		parentID = self.getFolderID(parent)
		
		if parentID is None:
			file_list = self.drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
		else:
			file_list = self.drive.ListFile({'q': "'%s' in parents and trashed=false" % str(parentID)}).GetList()

		for f in file_list:
			if f['title'] == filename:
				if self.printMessage:	
					print('Found' + self.fInfo(f))
				return(f)
		return(None)

	############################################################################################################

	def deleteFile(self, path) -> None:
		file = self.getFile(path)
		self.__deleteCore(file)

	def deleteFile_inLocation(self, parentID, filename) -> None:
		file = self.getFile_inLocation(parentID, filename)
		self.__deleteCore(file)

	def __deleteCore(self, file, permanentlyDelete=False) -> None:
		if file is None:
			if self.printMessage:	
				print("File/folder not found and not deleted.")
		else:
			if permanentlyDelete:
				file.Delete()	# Permanently delete the file.
			else:
				file.Trash()	# Move file to trash.
			if self.printMessage:	
				print('Deleted' + self.fInfo(file))

	############################################################################################################

	def uploadFile_fromLocation(self, pathFrom, pathTo=None) -> None:
		self.updateFile_fromLocation(pathFrom, pathTo, overrideFile=False)

	def updateFile_fromLocation(self, pathFrom, pathTo=None, overrideFile=True) -> None:
		if pathTo is None:
			pathTo = pathFrom

		try:
			with open(pathFrom,"r") as fLocal:
				self.updateFile(fLocal, pathTo, overrideFile)
		except IOError:
			print('Error while reading the file given.')

	def uploadFile(self, file, pathTo) -> None:
		self.updateFile(file, pathTo, overrideFile=False)

	def updateFile(self, file, pathTo, overrideFile=True) -> None:
		if not overrideFile:
			print("Warning: The upload function do not override an existing file.")

		parent, filename = self.__separate_pathAndFile(pathTo)
		parentID = self.getFolderID(parent)

		oldFile = self.getFile_inLocation(parentID, filename)
		if oldFile is not None:
			self.__deleteCore(oldFile)
			if not overrideFile:
				print("Warning: Now more than a copy of", filename, "will exists inside", parent)

		if parentID is None:
			newFile =   self.drive.CreateFile({'title': filename, "parents":  ['root']})
		else:
			newFile =   self.drive.CreateFile({'title': filename, "parents":  [{"id": parentID}] })

		newFile.SetContentString(file.read()) 
		newFile.Upload()
		if self.printMessage:	
			if overrideFile:
				print('Updated' + self.fInfo(newFile))
			else:
				print('Uploaded' + self.fInfo(newFile))

	############################################################################################################	
	
	def downloadFile(self, pathFrom, pathTo=None) -> None:
		if pathTo is None:
			pathTo = pathFrom

		fDrive = self.getFile(pathFrom)
		try:
			with open(pathTo,"w") as fLocal:
				#todo: solve error
				fLocal.write(fDrive.GetContentFile(True))
		except IOError:
			print('Error while writing the downloaded file.')
		

	############################################################################################################

	def createFolder(self, path) -> None:
		parent, folderName = self.__separate_pathAndFile(path)
		parentID = self.getFolderID(parent)

		if self.getFile_inLocation(parentID, folderName) is None:
			if parentID is None:
				newFolder = self.drive.CreateFile({'title': folderName, "parents":  ['root'], "mimeType": "application/vnd.google-apps.folder"})
			else:
				newFolder = self.drive.CreateFile({'title': folderName, "parents":  [{"id": parentID}], "mimeType": "application/vnd.google-apps.folder"})
			newFolder.Upload()
			if self.printMessage:	
				print("Created folder", self.fInfo(newFolder))

	def createLocalFolder(self, path) -> None:
		if not os.path.isdir(path):
			os.mkdir(path)

	def deleteFolder(self, path) -> None:
		return self.deleteFile(path)

	def deleteFolder_inLocation(self, parentID, filename) -> None:
		return self.deleteFile_inLocation(parentID, filename)

	############################################################################################################

	def prova(self) -> None:
		print("test function")

def main():
	filename = "testUpload.txt"

	gDrive = GDriveInterface(storeCredentials=True, printMessage=True)
	#tmp = gDrive.getFolderID("pippo/minni/ciao")
	#tmp = gDrive.getFileID("pippo/minni/ciao/test.txt")
	#print("tmp", tmp)

	#gDrive.updateFile_fromLocation("testUpload.txt", "driveAPI/ciao.txt")
	#gDrive.createFolder("driveAPI/tobeDeleted")
	
	#todo: solve recursion in deleteFile
	#gDrive.deleteFile("driveAPI/tobeDeleted")

	#gDrive.downloadFile("driveAPI/pippo/ciao.txt", "toBeDeleted.txt")
	#gDrive.prova()

	#gDrive.getFile("testUpload.txt")
	#updateFile(drive, filename)

	


if __name__ == "__main__":
	main()