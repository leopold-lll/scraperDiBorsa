from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files	import GoogleDriveFile
from googleapiclient.discovery import build
import os
import shutil

#pyDrive docs: https://pythonhosted.org/PyDrive/filemanagement.html

class GDriveInterface:

	def __functionName(self, pippo: str="example", pluto: 'list of string'=None) -> int:
		""" 
		Example function to show well designed code. 
  
		This function shows how to use docstring, and few other things...
  
		Parameters: 
		pippo (str): A useless parameter
  
		Returns: 
		int: Always the same value (42)
  
		"""
		#To remember:
		#The __ notation is a convention stating that this function is private to the class

		#Each parameter type can be specified with ": type" or if comple can be described as: ": 'complex type'"
		#Then the default value as "=default"

		#If one parameter depend on another one it can be managed as:
		if pluto is None:
			pluto = [pippo]
		
		#Finally the type of the return value as "-> type"
		#In the end, the docstring above can be shown with: print(__functionName.__doc__)

		return 42


	#################################   Initialization Function   ##############################################

	def __init__(self, storeCredentials: bool=True, printMessage: bool=True) -> None:
		""" Initialization function. """
		self.printMessage = printMessage
		self.drive = self.login(storeCredentials)
		##todo: solve this
		#print("Warning: this Class do not manage path with ../ to access previous folder nor / to access root. \n\tIt always go down in the tree folders structure.")

	def login(self, storeCredentials: bool=True) -> GoogleDrive:
		"""
			Login to a google account and by default store the used credentials.

			This function require the "client_secrets.json" file to launch the authentication procedure
		"""
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
		return GoogleDrive(gauth)


	#################################   Support Functions   ####################################################

	def info(self, f: GoogleDriveFile) -> str:
		""" Print info of the given file. """
		if f is None:
			return ""
		else:
			#print('location: %s, parents: %s' % (f['mimeType'], f['parents']))
			return('\tfile -> title: %s, id: %s, parents ID: %s' % (f['title'], f['id'], f['parents'][0].get('id')))

	def __pathAndFile(self, path: str) -> (str, str):
		""" Given a path separate it into last object (file or folder) and previous part. """
		foldersNameList = path.strip('/').split('/')
		
		parent = '/'.join(foldersNameList[:-1])
		filename = foldersNameList[-1]
		return(parent, filename)

	def __pathRemoveFile(self, path: str) -> str:
		""" Remove the last element of the path if it is a file, nothing otherwise. """
		parent, filename = self.__pathAndFile(path)
		if self.isPathFile(filename):
			return(parent)
		else:
			return(path)

	def getPathIDs(self, path: str) -> list:
		""" This function return a list of the ID of the folders up to the end of the path, and eventually the file placed at the end. """

		elements = self.getPathElements(path)
		#[print(self.info(f)) for f in elements]
		return [None if f is None else f['id'] for f in elements]

	def getPathElements(self, path: str) -> list:
		""" This function return a list containing the folders up to the end of the path, and eventually the file placed at the end. """

		#This question state that the tree of folder in google drive is a mess...
		#https://stackoverflow.com/questions/57113254/google-pydrive-function-to-use-as-os

		#Possible query to google drive:
		#file_list = self.drive.ListFile({'q': "'%s' in parents and trashed=false" % parent}).GetList()
		#file_list = self.drive.ListFile({'q': "'1WmwwykABr2VE4WzVwRgv8YhYkEZ1AC6A' in parents and trashed=false"}).GetList()
		#file_list = self.drive.ListFile({"q": "mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
		#file_list = self.drive.ListFile({"q": "'root' in parents and trashed=false"}).GetList()

		if path=="":
			#simply optimization
			return([])
		else:
			#Extract the folders that can match the path
			parent, filename = self.__pathAndFile(path)
			#the list of names of folders from root
			if self.isPathFile(filename):
				foldersNameList = parent.split('/')	
			else:
				foldersNameList = path.split('/')

			#Get all the folders form drive
			allFolder = self.drive.ListFile({"q": "mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
			plausibleFolders = []
			for f in allFolder:
				if f['title'] in foldersNameList:
					plausibleFolders.append(f)

			#Identify the first folder on the path
			elementsOnPath = []
			for f in plausibleFolders:
				#parent=root and check my name
				if f['parents'][0].get('isRoot') and f['title']==foldersNameList[0]:
					elementsOnPath.append(f)

			#Identify the remaining folders on the path
			for name in foldersNameList[1:]:
				for f in plausibleFolders:
					#check parent id and my name
					if f['parents'][0].get('id')==elementsOnPath[-1]['id'] and f['title']==name:
							elementsOnPath.append(f)

			#extract even the filename ID if exist
			if self.isPathFile(filename):
				if len(elementsOnPath)==0:
					elementsOnPath.append( self.downloadFile(path, None) )
				else:
					elementsOnPath.append( self.downloadFile(path, elementsOnPath[-1]['id']) )

			return(elementsOnPath)
		
	def getLastFolderID(self, path: str) -> str:
		""" Get the ID of last folder identified in the path, None if it does not exist. AKA getParentID"""
		print("get parent id")
		elements = self.getPathElements(path)
		if len(elements)>0:
			if   self.isFolder(elements[-1]):
				return elements[-1]['id']
			elif self.isFolder(elements[-1]) and len(elements)>1:
				return elements[-2]['id']
		return None
		
	def getID(self, path: str, parentID: str=None) -> str:
		""" Get the ID of the element identified from the path, None if it does not exist. """
		file = self.downloadFile(path, parentID)
		if file is None:
			return None
		else:
			return file['id']


	#################################   Checking functions   ###################################################

	def isPathFile(self, path: str) -> bool:
		""" Check if the last element of the path is a File (contain a dot). """
		return not self.isPathFolder(path)

	def isPathFolder(self, path: str) -> bool:
		""" Check if the last element of the path is a Folder (do not contain a dot). """
		parent, filename = self.__pathAndFile(path)
		return( filename.find(".")==-1 )

	def isIdFolder(self, id: str) -> bool:
		""" Check if the given ID correspond to a folder. """
		file_list = self.drive.ListFile({'q': "id='%s' and trashed=false"}).GetList()
		print(file_list)

	def isFile(self, file: GoogleDriveFile) -> bool:
		""" Check if the given GoogleDriveFile is a file. """
		return not self.isFolder(file)

	def isFolder(self, file: GoogleDriveFile) -> bool:
		""" Check if the given GoogleDriveFile is a folder. """
		return( file['mimeType']=="application/vnd.google-apps.folder" )

	def exists(self, path: str, parentID: str=None) -> bool:
		return self.getID(path, parentID) is not None
	
	def existsLocal(self, path: str) -> bool:
		""" Check if the element at the given path exists or not. """
		if path=="":
			return True
		return os.path.exists(path)


	#################################   Function on Local OS   #################################################

	def createLocalFolder(self, path: str) -> None:
		""" Create a folder on the local OS at the given location. A folder name cannot contians dot. """
		if self.isPathFolder(path):
			if not os.path.isdir(path):
				try:
					os.mkdir(path)
				except IOError:
					print("Error while creating the folder at:", path)
		else:
			print("NB: This interface assume that a folder name does not contians dot !")

	def removeLocal(self, path: str) -> None:
		""" Remove the specified path. It can be a file or even a folder. """
		#Try to remove file
		try:
			os.remove(path)
		except IsADirectoryError:

			#Try to remove folder and its content
			try:
				shutil.rmtree(path) 
			except OSError:
				print ("Not able to remove:", path)

	def saveLocalFile(self, file: GoogleDriveFile, path: str) -> bool:
		""" Save the file at the given location. """
		#parent, filename = self.__pathAndFile(path)
		#if self.existsLocal(parent) and self.isPathFile(filename):
		try:
			file.GetContentFile(path.strip("/"))	
		except (NotADirectoryError, FileNotFoundError) as err:
			print(err)
			return False
		return True



	###################################### other ###############################################################

	#def getFolder_inLocation(self, parentID, filename): # -> GoogleDriveFile
	#	return self.downloadFile(parentID, filename)
		
	def downloadFile(self, path: str, parentID: str=None) -> GoogleDriveFile:
		""" Download the file in the given location. None if it does not exist. """
		if parentID is None or parentID=="":
			elements = self.getPathElements(path)
			if elements is not None:
				return elements[-1]
		else:
			file_list = self.drive.ListFile({'q': "'%s' in parents and trashed=false" % str(parentID)}).GetList()
		
			parent, filename = self.__pathAndFile(path)
			for f in file_list:
				if f['title'] == filename:
					return(f)
		return(None)


	#def getFolder(self, path): # -> GoogleDriveFile
	#	return self.getFile(path)

	#def getFile(self, path): # -> GoogleDriveFile
	#	parent, filename = self.__pathAndFile(path)
	#	parentID = self.getFolderID(parent)
		
	#	if parentID is None:
	#		file_list = self.drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
	#	else:
	#		file_list = self.drive.ListFile({'q': "'%s' in parents and trashed=false" % str(parentID)}).GetList()

	#	for f in file_list:
	#		if f['title'] == filename:
	#			if self.printMessage:	
	#				print('Found' + self.info(f))
	#			return(f)
	#	return(None)

	############################################################################################################

	#def deleteFile(self, path) -> None:
	#	file = self.getFile(path)
	#	self.__deleteCore(file)

	#def deleteFile_inLocation(self, parentID, filename) -> None:
	#	file = self.downloadFile(parentID, filename)
	#	self.__deleteCore(file)

	#def __deleteCore(self, file, permanentlyDelete=False) -> None:
	#	if file is None:
	#		if self.printMessage:	
	#			print("File/folder not found and not deleted.")
	#	else:
	#		if permanentlyDelete:
	#			file.Delete()	# Permanently delete the file.
	#		else:
	#			file.Trash()	# Move file to trash.
	#		if self.printMessage:	
	#			print('Deleted' + self.info(file))

	############################################################################################################

	#def uploadFile_fromLocation(self, pathFrom, pathTo=None) -> None:
	#	self.updateFile_fromLocation(pathFrom, pathTo, overrideFile=False)

	#def updateFile_fromLocation(self, pathFrom, pathTo=None, overrideFile=True) -> None:
	#	if pathTo is None:
	#		pathTo = pathFrom

	#	try:
	#		with open(pathFrom,"r") as fLocal:
	#			self.updateFile(fLocal, pathTo, overrideFile)
	#	except IOError:
	#		print('Error while reading the file given.')

	#def uploadFile(self, file, pathTo) -> None:
	#	self.updateFile(file, pathTo, overrideFile=False)

	#def updateFile(self, file, pathTo, overrideFile=True) -> None:
	#	if not overrideFile:
	#		print("Warning: The upload function do not override an existing file.")

	#	parent, filename = self.__pathAndFile(pathTo)
	#	parentID = self.getFolderID(parent)

	#	oldFile = self.downloadFile(parentID, filename)
	#	if oldFile is not None:
	#		self.__deleteCore(oldFile)
	#		if not overrideFile:
	#			print("Warning: Now more than a copy of", filename, "will exists inside", parent)

	#	if parentID is None:
	#		newFile =   self.drive.CreateFile({'title': filename, "parents":  ['root']})
	#	else:
	#		newFile =   self.drive.CreateFile({'title': filename, "parents":  [{"id": parentID}] })

	#	newFile.SetContentString(file.read()) 
	#	newFile.Upload()
	#	if self.printMessage:	
	#		if overrideFile:
	#			print('Updated' + self.info(newFile))
	#		else:
	#			print('Uploaded' + self.info(newFile))

	############################################################################################################	
	
	#def downloadFile(self, pathFrom, pathTo=None) -> None:
	#	if pathTo is None:
	#		pathTo = pathFrom

	#	fDrive = self.getFile(pathFrom)
	#	try:
	#		with open(pathTo,"w") as fLocal:
	#			#todo: solve error
	#			fLocal.write(fDrive.GetContentFile(True))
	#	except IOError:
	#		print('Error while writing the downloaded file.')
		

	############################################################################################################

	#def createFolder(self, path) -> None:
	#	parent, folderName = self.__pathAndFile(path)
	#	parentID = self.getFolderID(parent)

	#	if self.downloadFile(parentID, folderName) is None:
	#		if parentID is None:
	#			newFolder = self.drive.CreateFile({'title': folderName, "parents":  ['root'], "mimeType": "application/vnd.google-apps.folder"})
	#		else:
	#			newFolder = self.drive.CreateFile({'title': folderName, "parents":  [{"id": parentID}], "mimeType": "application/vnd.google-apps.folder"})
	#		newFolder.Upload()
	#		if self.printMessage:	
	#			print("Created folder", self.info(newFolder))

	#def deleteFolder(self, path) -> None:
	#	return self.deleteFile(path)

	#def deleteFolder_inLocation(self, parentID, filename) -> None:
	#	return self.deleteFile_inLocation(parentID, filename)

	############################################################################################################

	def prova(self) -> None:
		print("test function")
		fl = self.drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
		print(type(fl[0]))

def main():
	filename = "testUpload.txt"

	gDrive = GDriveInterface(storeCredentials=True, printMessage=True)
	fDrive = gDrive.downloadFile("drive API/pippo/ciao.txt")
	#todo: manage this case:
	gDrive.saveLocalFile(fDrive, "prova/downloaded.txt/ciao.txt")
	
	#tmp = gDrive.getFolderID("pippo/minni/ciao")
	#tmp = gDrive.getFileID("pippo/minni/ciao/test.txt")
	#print("tmp", tmp)

	#gDrive.updateFile_fromLocation("testUpload.txt", "driveAPI/ciao.txt")
	#gDrive.createFolder("driveAPI/tobeDeleted")
	
	
	
	


if __name__ == "__main__":
	main()