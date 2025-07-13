![PyPI](https://img.shields.io/pypi/v/freetube-import?label=pypi%20package)![PyPI - Downloads](https://img.shields.io/pypi/dm/freetube-import)



# Freetube-import
Creates [FreeTube](https://freetubeapp.io/) .db playlist files from a list of youtube urls (.txt) or from .csv files exported from 'Google takeout'.

Run the scrip with a path to a valid .txt file of youtube urls, or youtube's .csv playlist file. Then import the resulting .db file into FreeTube.



Install via pip:

      pip install freetube-import

https://pypi.org/project/freetube-import/

Basic usage:

      freetube-import <file>... <file2> <file3>

Help message:

      usage: freetube_import.py [-h] [-a] [-b] [-e] [-s] [filepath ...]

      Import youtube playlists

      positional arguments:
        filepath              path to a valid .txt or .csv playlist file or files

      optional arguments:
        -h, --help            show this help message and exit
        -a, --list-all        Takes all .txt and csv files as input from the current working directory.
        -b, --list-broken-videos
                        Lists videos that were added but have possibly broken metadata (for debugging).
        -e, --log-errors      Also lists the videos that failed the metadata fetch
        -s, --stdin           Takes stdin as input and outputs dirextly to stdout
        -n NAME, --name NAME  sets a name for playlist, otherwise uses input filename

While buggy and experimental `stdin` mode can used in scripts and automation. Not for average users.

       cat test.txt | freetube-import -s > std_test.db

It might be usefull to set a name that shows up in FreeTube. Otherwise in stdin mode a placeholder name is generated.

       cat test.txt | freetube-import -s -n playlist-name > std_test.db

pro tip: Try appending the ouput to FreeTube's own playlist.db file. So playlists get automatically added. (backup your files beforehand, close freetube, at your own risk)

      cat test.txt | freetube-import -s -n playlist-name >> your/path/FreeTube/playlists.db


Works without YouTube api through a custom version of [YouTube-search library](https://github.com/joetats/youtube_search/). Also works atleast on piped links, probably also on lists of Invidious links and other links that follow the standard youtube url format.

###  Dependencies 

       pip install requests
https://pypi.org/project/requests/

      pip install tqdm
https://pypi.org/project/tqdm/
