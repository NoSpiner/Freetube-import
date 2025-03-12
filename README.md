# Freetube-import
Creates Freetube .db style playlist files from a list of youtube urls (.txt) or from .csv files exported from 'Google takeout'.

Run the scrip with a path to a valid list of youtube urls, or youtube's .csv playlist file. Then import the .db file into Freetube.

      python create_db.py <file>

Help message:

      usage: create_db.py [-h] [-l] filepath

      Import youtube playlists

      positional arguments:
        filepath          path to a valid .txt or .csv playlist file

      optional arguments:
        -h, --help        show this help message and exit
        -l, --log-errors  Also lists the videos that failed the metadata fetch

Works without YouTube api through YouTube-search library. Also works atleast on piped links, probably also on lists of Invidious links and other links that follow the standard youtube url format.

While the script should work perfectly for 95% of the videos, some channel names in the playlist view can however get messed up. This is due to incorrect metadata fetch. Clicking the link to the video's channel in playlist view also does not work, but does work after opening the video. 
These are the costs for avoiding the hassle with google's own api.

###  Dependencies 

       pip install youtube-search
https://pypi.org/project/youtube-search/

      pip install tqdm
https://pypi.org/project/tqdm/
