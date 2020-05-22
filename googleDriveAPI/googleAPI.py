from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from googleapiclient.discovery import build
import os

#pyDrive docs: https://pythonhosted.org/PyDrive/filemanagement.html

def googleLogin_withCredentials():
	gauth = GoogleAuth()
	# Try to load saved client credentials
	gauth.LoadCredentialsFile("myCredentials.txt")
	if gauth.credentials is None:
		# Authenticate if they're not there
		gauth.LocalWebserverAuth()
	elif gauth.access_token_expired:
		# Refresh them if expired
		gauth.Refresh()
	else:
		# Initialize the saved creds
		gauth.Authorize()

	# Save the current credentials to a file
	gauth.SaveCredentialsFile("myCredentials.txt")

	drive = GoogleDrive(gauth)
	return drive

def googleLogin():
	g_login = GoogleAuth()
	g_login.LocalWebserverAuth()
	drive = GoogleDrive(g_login)
	return drive

def fileInfo(f):
	return('\tfile: title: %s, id: %s' % (f['title'], f['id']))

def locateFile(drive, filename):
	# Auto-iterate through all files in the root folder.
	file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
	for f in file_list:
		if f['title'] == filename:
			print('Found' + fileInfo(f))
			return(f)
	return(None)


def deleteFile(drive, filename):
	f = locateFile(drive, filename)
	if f is None:
		print(filename, "not found and not deleted.")
	else:
		f.Trash()		# Move file to trash.
		#f.Delete()		# Permanently delete the file.
		print('Trashed' + fileInfo(f))

def updateFile(drive, path):
	filename = os.path.basename(open(path,"r").name)
	fDrive = locateFile(drive, filename=filename)
	if fDrive is None:
		uploadFile(drive, path=path)
	else:
		with open(path,"r") as fLocal:
			fDrive.SetContentString(fLocal.read())
			fDrive.Upload()
			print('Updated' + fileInfo(fDrive))

def uploadFile(drive, path):
	with open(path,"r") as fLocal:
		fDrive = drive.CreateFile({'title':os.path.basename(fLocal.name) })  #basename is the name without the path
		fDrive.SetContentString(fLocal.read()) 
		fDrive.Upload()
		print('Uploaded' + fileInfo(fDrive))


def main():
	filename = "testUpload.txt"
	drive = googleLogin_withCredentials()
	updateFile(drive, filename)

	


if __name__ == "__main__":
	main()