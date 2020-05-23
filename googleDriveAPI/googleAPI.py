from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from googleapiclient.discovery import build
import os

#pyDrive docs: https://pythonhosted.org/PyDrive/filemanagement.html

class GDriveInterface:

	def __init__(self, storeCredentials=True):
		self.googleLogin(storeCredentials)

	def googleLogin(self, storeCredentials=True):
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

	def fInfo(self, f):
		#Work for both file and folder
		#print('location: %s, parents: %s' % (f['mimeType'], f['parents']))
		return('\tfile -> title: %s, id: %s, parents ID: %s' % (f['title'], f['id'], f['parents'][0].get('id')))

	def __stringListCompare(self, str, strList):
		for el in strList:
			if el==str:
				return True
		return False

	def __separate_pathAndFile(self, path):
		#The __ notation is a convention stating that this function is private to the class
		foldersNameList = path.strip('/').split('/')
		
		parent = '/'.join(foldersNameList[:-1])
		filename = foldersNameList[-1]
		return(parent, filename)

	def getPathIDs(self, path):
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

	def getFolderID(self, path):
		fIDs = self.getPathIDs(path)
		if len(fIDs)>0:
			return(fIDs[-1])
		else:
			return(None)
		
	def getFileID(self, path):
		file = self.getFile(path)
		if file is None:
			return None
		else:
			return file['id']

	def getFileIn(self, pathID, filename):
		#It is a very efficient version of get file (simply because the location is already known)
		if pathID is None:
			file_list = self.drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
		else:
			file_list = self.drive.ListFile({'q': "'%s' in parents and trashed=false" % str(pathID)}).GetList()
		for f in file_list:
			if f['title'] == filename:
				return(f)
		return(None)

	def getFile(self, path):
		parent, filename = self.__separate_pathAndFile(path)
		parentID = self.getFolderID(parent)
		
		# Auto-iterate through all files in the root folder.
		if parentID is None:
			file_list = self.drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
		else:
			file_list = self.drive.ListFile({'q': "'%s' in parents and trashed=false" % str(parentID)}).GetList()

		for f in file_list:
			if f['title'] == filename:
				print('Found' + self.fInfo(f))
				return(f)
		return(None)


	#def deleteFile(self, filename):
	#	f = self.locateFile(filename)
	#	if f is None:
	#		print(filename, "not found and not deleted.")
	#	else:
	#		f.Trash()		# Move file to trash.
	#		#f.Delete()		# Permanently delete the file.
	#		print('Trashed' + self.fInfo(f))

	#def updateFile(self, path):
	#	filename = os.path.basename(open(path,"r").name)
	#	fDrive = self.locateFile(filename)
	#	if fDrive is None:
	#		self.uploadFile(path=path)
	#	else:
	#		with open(path,"r") as fLocal:
	#			fDrive.SetContentString(fLocal.read())
	#			fDrive.Upload()
	#			print('Updated' + self.fInfo(fDrive))

	#def uploadFile(self, path):
	#	with open(path,"r") as fLocal:
	#		fDrive = self.drive.CreateFile({'title':os.path.basename(fLocal.name) })  #basename is the name without the path
	#		fDrive.SetContentString(fLocal.read()) 
	#		fDrive.Upload()
	#		print('Uploaded' + self.fInfo(fDrive))

	def createDir(self, path):
		folderPath, folderName = self.__separate_pathAndFile(path)
		pathID = self.getFolderID(folderPath)

		if self.getFileIn(pathID, folderName) is None:
			if pathID is None:
				newFolder = self.drive.CreateFile({'title': folderName, "parents":  ['root'], "mimeType": "application/vnd.google-apps.folder"})
			else:
				newFolder = self.drive.CreateFile({'title': folderName, "parents":  [{"id": pathID}], "mimeType": "application/vnd.google-apps.folder"})
			newFolder.Upload()
			print("Created folder", self.fInfo(newFolder))

	def createLocalDir(self, path):
		if not os.path.isdir(path):
			os.mkdir(path)


def main():
	filename = "testUpload.txt"

	gDrive = GDriveInterface(True)
	#tmp = gDrive.getFolderID("pippo/minni/ciao")
	#tmp = gDrive.getFileID("pippo/minni/ciao/test.txt")
	#print("tmp", tmp)

	#gDrive.createDir("12345")

	#gDrive.getFile("testUpload.txt")
	#updateFile(drive, filename)

	


if __name__ == "__main__":
	main()