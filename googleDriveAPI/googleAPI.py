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
		#todo: solve this
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

	def parentID(self, f: GoogleDriveFile) -> str:
		""" Get the parent ID of the given file. None if it does not exist. """
		if f is None:
			return None
		else:
			return f['parents'][0].get('id')

	def info(self, f: GoogleDriveFile) -> str:
		""" Print info of the given file. """
		if f is None:
			return "\tNot existing file."
		else:
			#print('location: %s, parents: %s' % (f['mimeType'], f['parents']))
			return('\tfile -> %s, id: %s, parentID: %s' % (f['title'], f['id'], f['parents'][0].get('id')))

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
		path = path.strip("/")
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
				found = False
				for f in plausibleFolders:
					#check parent id and my name
					if f['parents'][0].get('id')==elementsOnPath[-1]['id'] and f['title']==name:
						elementsOnPath.append(f)
						found = True
				if not found:
					elementsOnPath.append(None)
					return(elementsOnPath)

			#extract even the filename ID if exist
			if self.isPathFile(filename):
				if len(elementsOnPath)==0:
					id = self.downloadGdFile(path, "root")
				else:
					id = self.downloadGdFile(path, elementsOnPath[-1]['id'])

				elementsOnPath.append(id)

			return(elementsOnPath)
		
	def getLastFolderID(self, path: str) -> str:
		""" Get the ID of last folder identified in the path, None if it does not exist. """
		if path=="":
			return("root")

		elements = self.getPathElements(path)
		#remove last element if none
		if len(elements)>0 and elements[-1] is None:
			elements = elements[:-1]

		if len(elements) == self.pathLength(path):
			if len(elements)>0:
				if   self.isFolder(elements[-1]):
					return elements[-1]['id']
				elif self.isFile(elements[-1]) and len(elements)>1:
					return elements[-2]['id']
			return("root")
		else:
			return(None)
		
	def getID(self, path: str, parentID: str=None) -> str:
		""" Get the ID of the element identified from the path, None if it does not exist. """
		file = self.downloadGdFile(path, parentID)
		if file is None:
			return None
		else:
			return file['id']

	def pathLength(self, path: str) -> int:
		elements = path.strip('/').split('/')
		return(len(elements))


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

	def createLocalFolder(self, path: str) -> bool:
		""" Create a folder on the local OS at the given location. A folder name cannot contians dot. """
		res = False
		if self.isPathFolder(path):
			if not os.path.isdir(path):
				try:
					os.mkdir(path)
					res = True
					if self.printMessage:
						print("Created folder:", path)
				except IOError:
					print("Error while creating the folder at:", path)
		else:
			print("NB: This interface assume that a folder name does not contians dot !")
		return res

	def removeLocal(self, path: str) -> bool:
		""" Remove the specified path. It can be a file or even a folder. """
		#Try to remove file
		try:
			os.remove(path)
			if self.printMessage:
				print("Removed file:", path)
		except IsADirectoryError:

			#Try to remove folder and its content
			try:
				shutil.rmtree(path) 
			except OSError:
				print ("Not able to remove:", path)
				return False
		return True

	def saveLocalFile(self, file: GoogleDriveFile, path: str) -> bool:
		""" Save the file at the given location. """
		#parent, filename = self.__pathAndFile(path)
		#if self.existsLocal(parent) and self.isPathFile(filename):
		try:
			file.GetContentFile(path.strip("/"))	
			if self.printMessage:
				print("Saved file to:", path)
		except (NotADirectoryError, FileNotFoundError) as err:
			print(err)
			return False
		return True


	#################################   Create & Delete   ######################################################

	def createFolder(self, path: str, parentID: str=None) -> str:
		""" Create a folder at the given location. """
		parent, folderName = self.__pathAndFile(path)
		if self.isPathFolder(folderName) and path!="":
			if parentID is None:
				parentID = self.getLastFolderID(parent)
			
			if parentID is not None and not self.exists(path, parentID):
				# the folder does not exist yet
				if parentID=="root":
					newFolder = self.drive.CreateFile({'title': folderName, "parents":  ['root'],			"mimeType": "application/vnd.google-apps.folder"})
				else:
					newFolder = self.drive.CreateFile({'title': folderName, "parents":  [{"id": parentID}], "mimeType": "application/vnd.google-apps.folder"})
				newFolder.Upload()
				if self.printMessage:	
					print("Created folder", self.info(newFolder))
				return newFolder['id']
		return None

	def delete(self, path: str, parentID: str=None) -> bool:
		""" Delete the file/folder at the given location. """
		if path!="" and self.exists(path, parentID):
			parent, filename = self.__pathAndFile(path)
			if parentID is None:
				parentID = self.getLastFolderID(parent)
			if parentID is not None:
				file = self.downloadGdFile(path, parentID)
				return self.__del(file)
		return False

	def __del(self, file: GoogleDriveFile, permanentlyDelete: bool=False) -> bool:
		try:
			if permanentlyDelete:
				file.Delete()	# Permanently delete the file.
			else:
				file.Trash()	# Move file to trash.
			if self.printMessage:	
				print('Deleted' + self.info(file))	
		except Exception as err:
			print(err)
			return False
		return True


	#################################   Upload Functions   #####################################################

	def upload(self, pathFrom: str, pathTo: str, parentID: str=None) -> bool:
		""" Upload the source path and the entire subtree (if folder) to the destination path. """
		res = False
		if self.isPathFile(pathFrom):
			#manage file
			try:
				with open(pathFrom, "r") as fLocal:
					res = self.uploadFile(fLocal, pathTo, parentID)
			except IOError:
				print(IOError, 'Error while reading the file given.')
		else:
			#manage folder
			res = self.__uploadFolder(pathFrom, pathTo, parentID)

		return res

	def __uploadFolder(self, pathFrom: str, pathTo: str, parentID: str=None) -> bool:
		""" Upload a folder (and the entire subtree) from the source path to the destination path. """
		newFolderID = None
		res = False
		if parentID is None:
			#if not defined yet precompute the ID of the folder and parent
			elements = self.getPathElements(pathFrom)
			if elements is not None:
				#the folder exists
				newFolderID = elements[-1]['id']
				parentID = self.parentID(elements[-1])

		if parentID is not None:
			#still updating folder ID
			if newFolderID is None:
				newFolderID = self.getID(pathTo, parentID)
				if newFolderID is None:
					newFolderID = self.createFolder(pathTo, parentID)

			if newFolderID is not None:
				res = True
				#for each file in folder upload it
				for el in os.scandir(pathFrom):
					newPathTo = '/'.join([pathTo, el.path.replace(pathFrom, '').strip('/')])
					#print("\ncall on: from:\t", el.path, "\t-> to:", newPathTo, ", main folder ID:", newFolderID)
					tmp =  self.upload(el.path, newPathTo, newFolderID) 

					#update res (now True) it is sufficient a False to make fail the entire function
					res = res and tmp	
		return res
					
	def uploadFile(self, file: "OS file", pathTo: str, parentID: str=None) -> bool:
		""" Upload the given file to the destination path. """
		parent, filename = self.__pathAndFile(pathTo)
		res = True
		if parentID is None:
			#compute parentID
			parentID = self.getLastFolderID(parent)
		
		self.delete(pathTo, parentID) #delete the previous file
		if parentID is "root":
			newFile = self.drive.CreateFile({'title': filename, "parents":  ['root']})
		else:
			newFile = self.drive.CreateFile({'title': filename, "parents":  [{"id": parentID}] })
		
		try:
			#upload may fail due to internet connection (and other reasons)
			newFile.SetContentString(file.read()) 
			newFile.Upload()
		except Exception as errLoading:
			print("Error while loading file (wrong path):", errLoading)
			res = False

		if self.printMessage:
			if res:
				print('Uploaded' + self.info(newFile))
			else:
				print('Faild uploading' + self.info(newFile))
		return res


	#################################   Download Functions   ###################################################
		
	def downloadGdFile(self, path: str, parentID: str=None) -> GoogleDriveFile:
		""" Download the google drive file/folder at the given location. None if it does not exist. """
		if parentID is None:
			elements = self.getPathElements(path)
			if len(elements)>0:
				return elements[-1]
		else:
			file_list = self.drive.ListFile({'q': "'%s' in parents and trashed=false" % str(parentID)}).GetList()
		
			parent, filename = self.__pathAndFile(path)
			for f in file_list:
				if f['title'] == filename:
					return(f)
		return(None)

	def download(self, pathFrom: str, pathTo: str, parentID: str=None) -> bool:
		""" Download the source path [online] (and the entire subtree) to the destination path [local OS]. """
		#initialize variables
		actualFile = None
		if parentID is None:
			elements = self.getPathElements(pathFrom)
			
			if elements is not None:
				actualFile = elements[-1]
				parentID = self.parentID(elements[-1])
		else:
			actualFile = self.downloadGdFile(pathFrom, parentID)

		#do the first recursive call
		res = False
		parent, filename = self.__pathAndFile(pathTo)
		if	actualFile is not None and self.existsLocal(parent):
			res = self.__save(actualFile, pathTo.strip('/'))

		return res

	def __save(self, file: GoogleDriveFile, pathTo: str) -> bool:
		""" Recursive function that save on the local OS the given file and its entire subtree. """
		res = False

		#different operation according to file or folder
		if self.isFile(file):
			res = self.saveLocalFile(file, pathTo)
		else:
			self.createLocalFolder(pathTo)
			file_list = self.drive.ListFile({'q': "'%s' in parents and trashed=false" % file['id']}).GetList()
			
			res = True
			#recursive call foreach sub element of the folder
			for subFile in file_list:
				newPathTo = '/'.join([pathTo, subFile['title']])
				tmp = self.__save(subFile, newPathTo)
				res = res and tmp	#update the return value
		return res


	################################# - - - THE END - - - ######################################################

def main():
	gDrive = GDriveInterface(storeCredentials=True, printMessage=True)


if __name__ == "__main__":
	main()