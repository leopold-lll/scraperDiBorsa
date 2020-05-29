# [Scraper di Borsa](https://github.com/leopold-lll/scraperDiBorsa/blob/master/scraper.py)
This repository contains a scraper procedure to collect a few public data from the website of [Borsa Italiana](https://www.borsaitaliana.it/borsa/azioni/listino-a-z.html?initial=A). The goal is to scrape the maximal and minimal values of a list of company titles and store them on local files.

The code could simply be run periodically (i.e. each day) with a wrapper method placed on a server or online platforms such as [pythonanywhere](https://www.pythonanywhere.com).

# [Google Drive API Interface](https://github.com/leopold-lll/scraperDiBorsa/blob/master/googleDriveAPI/googleDriveAPI.py)
As an extension of this code exists a class used as an interface to [pyDrive](https://pypi.org/project/PyDrive/). A library that simplifies access to the [Google Drive API](https://developers.google.com/drive/api/v3/about-sdk). 
The class implements a few main methods, such as:
- upload    (both file and folder)
- download  (both file and folder)
- delete    (both file and folder)
- createFolder

This little library was created and tested, but it's not perfectly optimized and I can't guarantee that it's completely "bug-free"...

Despite that, if you need it,
**Feel free to use it :D**