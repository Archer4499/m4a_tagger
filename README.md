# m4a_tagger
A Python app for adding/updating tags on m4a files using info from Dbpedia, Wikipedia and Discogs.  
Tested in Python 3.3 on Windows and Mac OS.

Libraries used:  
* TkInter for the user interface.
* [Mutagen 1.31](https://mutagen.readthedocs.org) (pip install mutagen) for reading and writing tags.
* And the folowing for retrieving new tags:
  * [lxml 3.7.3](http://lxml.de) (pip install lxml)
  * [Discogs client 2.0.2](https://github.com/discogs/discogs_client) (pip install discogs_client)
  * modified version of [Wptools](https://github.com/siznax/wptools) (included), pycurl is needed for wptools:
    * [pycurl](https://pycurl.io) (pip install pycurl)

Install:  
* Run the following commands:

    ````
    git clone https://github.com/Archer4499/m4a_tagger
    pip install mutagen
    pip install lxml
    pip install discogs_client
    pip install pycurl
    ````

* Create a "token.txt" file in the containing only a user token from the Discogs [developer](https://www.discogs.com/settings/developers) page

This project is licensed under the terms of the MIT license.
