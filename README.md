![PyPI](https://img.shields.io/pypi/v/freetube-import?label=pypi%20package)![PyPI - Downloads](https://img.shields.io/pypi/dm/freetube-import)



# Freetube-import
Creates Freetube .db style playlist files from a list of youtube urls (.txt) or from .csv files exported from 'Google takeout'.

Run the scrip with a path to a valid list of youtube urls, or youtube's .csv playlist file. Then import the .db file into Freetube.



Install via pip:

      pip install freetube-import

https://pypi.org/project/freetube-import/

usage:

      freetube-import <file>... <file2> <file3>

Or if you prefer just cloning the script.

      python freetube_import.py <file>... <file2> <file3>



Help message:

      usage: freetube-import [-h] [-l] [-a] [filepath ...]
      Import youtube playlists
      positional arguments:
        filepath          path to a valid .txt or .csv playlist file or files
      options:
        -h, --help            show this help message and exit
        -a, --list-all        Takes all .txt and csv files as input from the current working directory.
        -b, --list-broken-videos
                        Lists videos that were added but have possibly broken metadata (for debugging).
        -e, --log-errors      Also lists the videos that failed the metadata fetch

Works without YouTube api through a custom version of [YouTube-search library](https://github.com/joetats/youtube_search/). Also works atleast on piped links, probably also on lists of Invidious links and other links that follow the standard youtube url format.

While the script should work perfectly for 95% of the videos, some channel names in the playlist view can however get messed up. This is due to incorrect metadata fetch. 
These are the costs for avoiding the hassle with google's own api.

###  Dependencies 

       pip install requests
https://pypi.org/project/requests/

      pip install tqdm
https://pypi.org/project/tqdm/
