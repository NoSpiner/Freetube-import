import uuid
import time
from pathlib import Path
import json
import argparse
from tqdm import tqdm
import re
import sys
import requests
import os
import logging
import html
import urllib.parse
from datetime import datetime
from typing import Optional, Union, TypeAlias
try:
    from youtube_search import YoutubeSearch
except ImportError:
    from .youtube_search import YoutubeSearch


VideoDict: TypeAlias = dict[str, Union[str, int]]

class VideoInfo:

    def __init__(
            self,
            video_id: str,
            title: str = "",
            author_name: str = "",
            author_id: str = "",
            length_s: int = 0,
            date_added_ms: Optional[int] = None
        ):

        self.id = video_id
        self.title = title
        self.author_name = author_name
        self.author_id = author_id
        self.length_s = length_s
        self.date_added_ms = date_added_ms or int(time.time() * 1000)

    def to_dict(self) -> VideoDict:
        return {
            "videoId": self.id,
            "title": self.title,
            "author": self.author_name,
            "authorId": self.author_id,
            "published": "",
            "lengthSeconds": self.length_s,
            "timeAdded": self.date_added_ms,
            "type": "video",
            "playlistItemId": str(uuid.uuid4())
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


PlaylistDict: TypeAlias = dict[str, Union[str, int, list[VideoDict]]]

class PlaylistInfo:

    def __init__(
            self,
            name: str,
            videos: Optional[list[VideoInfo]] = None,
            date_created_ms: Optional[int] = None,
            date_last_updated_ms: Optional[int] = None
        ):

        self.name = name
        self.videos = videos or []

        current_time_ms = int(time.time() * 1000)

        self.date_created_ms = date_created_ms or current_time_ms
        self.date_last_updated_ms = date_last_updated_ms or current_time_ms


    def to_dict(self) -> PlaylistDict:
        return {
            "playlistName": self.name,
            "videos": [v.to_dict() for v in self.videos],
            "_id": "ft-playlist--" + str(uuid.uuid4()),
            "createdAt": self.date_created_ms,
            "lastUpdatedAt": self.date_last_updated_ms
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


def YT_authordata(yt_id) -> dict | None:
    try:
        if yt_id[0] == "_":
            return YoutubeSearch('https://www.youtube.com/watch?v=//'+yt_id, max_results = 1).to_dict()[0]
        return YoutubeSearch('https://www.youtube.com/watch?v='+yt_id, max_results = 1).to_dict()[0]
    except IndexError:
        logger.warning(f"Youtube-search failed for https://www.youtube.com/watch?v={yt_id}")
        return None


def yt_video_data_fallback(url) -> dict | None:
    logger.debug(f"fallback fundtion called: https://www.youtube.com/watch?v={url}")
    url_quoted = urllib.parse.quote_plus(url)
    web_request = requests.get("https://www.youtube.com/watch?v="+url_quoted)
    site_html = web_request.text
    try:
        title = re.search(r'<title\s*.*?>(.*?)</title\s*>', site_html, re.IGNORECASE)
        if title:
            title = html.unescape(title.group(1).split("- YouTube")[0])
        if len(title) < 2:
            logger.warning(f"{url}: Fallback function. getting video title failed")
            return None

        author = re.search(r'"author":"(.*?)"', site_html, re.IGNORECASE)
        if author:
            author = author.group(1)
        else:
            author = "channel"
            logger.warning(f"{url}: Fallback function. getting channel name failed")

        channelId = re.search(r'"channelId":"(.*?)"', site_html, re.IGNORECASE)
        if channelId:
            channelId = channelId.group(1)
        else:
            channelId = "UCGBhVKHvwL386p13_-n3YPg"
            logger.warning(f"{url}: Fallback function. getting channel Id failed")

        endTimeMs = re.search(r'"endTimeMs":"(.*?)"', site_html, re.IGNORECASE)
        if endTimeMs:
            endTimeMs = int(endTimeMs.group(1))/1000
        else:
            endTimeMs = "0:00"
            logger.warning(f"{url}: Fallback function. getting video duration failed")

    except Exception as e:
        logger.error(f"yt_video_data_fallback() failed: {e}")
        return None
    return dict(title=title,
                author=html.unescape(author),
                channelId=channelId,
                lengthSeconds=endTimeMs
                )


def get_duration(time) -> int:
    try:
        time_parts = re.split(r"[.:]", time)
        seconds = int(time_parts[-1])
        minutes = int(time_parts[-2])
        hours = 0
        if len(time_parts) == 3:
            hours = int(time_parts[0])
        return seconds+minutes*60+hours*3600
    except Exception as e:
        logger.error(f"get_duration() failed {e}")
        return 0


def yt_date_to_timestamp_ms(date: str) -> int:
    dt = datetime.fromisoformat(date)
    return int(dt.timestamp() * 1000)


def process_txt(path) -> list[VideoInfo]:
    with open(path, "r", encoding='utf-8') as inputfile:
        lines = inputfile.readlines()
        Videos: list[VideoInfo] = []
        for l in lines:
            if l.strip() == "":
                continue

            video_id = re.split(r"\?v=|youtu\.be/|shorts/", l)
            try:
                video_id = video_id[1].rstrip()
                Videos.append(VideoInfo(video_id=video_id))
            except IndexError:
                pass
    logger.debug(f"{path} .txt file processed")
    return Videos


def process_csv(path) -> list[VideoInfo]:
    with open(path, "r", encoding='utf-8') as inputfile:
        lines = inputfile.readlines()
        Videos: list[VideoInfo] = []
        data_start = False
        for l in lines:
            if l.strip() == "":
                continue

            if not data_start:
                data_start = True
                continue
            if data_start:
                parts = l.split(",")
                video_id = parts[0].strip()
                date_added_str = parts[1].strip()
                if not len(video_id) == 11:
                    continue
                Videos.append(
                    VideoInfo(
                        video_id=video_id,
                        date_added_ms=yt_date_to_timestamp_ms(date_added_str)
                    )
                )
    logger.debug(f"{path} .csv file processed")
    return Videos


def process_stdin() -> list[VideoInfo]:
    lines = sys.stdin.readlines()
    Videos: list[VideoInfo] = []
    for l in lines:
        if l.strip() == "":
            continue

        video_id = re.split(r"\?v=|youtu\.be/|shorts/", l)
        try:
            video_id = video_id[1].rstrip()
            Videos.append(VideoInfo(video_id=video_id))
        except IndexError:
            pass
    logger.debug(f"Std input read with {len(Videos)} items")
    return Videos


def parse_videos(playlist_filepath, stdin) -> tuple[list[VideoInfo], str]:
    if stdin and not playlist_filepath:
        Videos = process_stdin()
        playlistname = f"playlist-{int(time.time())}"

    else:
        if not Path(playlist_filepath).is_file():
            logger.critical(f"{playlist_filepath} is not a file.")
            exit(1)
        playlistname = str(Path(playlist_filepath).name)
        # a playlist name could have a dot in it so use splitext instead of splitting on a '.'
        playlistformat = os.path.splitext(playlistname)[1][1:].strip().lower()
        playlistname = os.path.splitext(playlistname)[0]
        Videos = []
        if playlistformat == "txt":
            Videos = process_txt(playlist_filepath)
        elif playlistformat == "csv":
            Videos = process_csv(playlist_filepath)
        else:
            logger.critical(f"{playlistformat} is invalid file format.")
            exit(1)
    print(f"Reading file {playlist_filepath}, the playlistfile has {len(Videos)} entries", file=sys.stderr)
    return Videos, playlistname


def write_output(playlist :PlaylistInfo, stdin = False, write_counter=0):
    if len(playlist.videos) != 0 and not stdin:
        outputfile = open(playlist.name+".db", "w", encoding='utf-8')
        outputfile.write(json.dumps(playlist.to_dict(), separators = (',', ':'))+"\n")
        outputfile.close()
        logger.info(f"{playlist.name}.db written({write_counter}/{len(playlist.videos)})")
        print(f"Task failed successfully! {playlist.name}.db written, with {write_counter} entries", file=sys.stderr)
    elif stdin:
        print(json.dumps(playlist.to_dict(), separators = (',', ':')))
        logger.info(f"written({write_counter}/{len(playlist.videos)}) into standard output")
    else:
        print("No entries to write", file=sys.stderr)

def print_errors(failed_ID,failed_yt_search):
    if len(failed_ID) != 0:
        print("[Failed playlist items]", file=sys.stderr)
        for video_id in failed_ID:
            print('https://www.youtube.com/watch?v='+video_id, file=sys.stderr)
            
    if len(failed_yt_search) != 0:
        print("[Videos with possibly broken metadata]")
        for video_id in failed_yt_search:
            print('https://www.youtube.com/watch?v='+video_id, file=sys.stderr)

# Does the actual parsing and writing
def process_playlist(playlist_filepath, log_errors=False, list_broken_videos=False,stdin=False, pl_name=""):
    Videos, playlistname = parse_videos(playlist_filepath, stdin)
    if pl_name:
        playlistname = pl_name
    print(f"writing to file {playlistname}.db", file=sys.stderr)
    playlist = PlaylistInfo(name=playlistname)
    write_counter = 0
    failed_yt_search = []
    failed_ID = []
    latest_added_timestamp_ms = 0
    for video in tqdm(Videos, disable=logging.getLogger(__name__).isEnabledFor(logging.DEBUG)):
        videoinfo = YT_authordata(video.id)
        
        # Fetch data with youtube_search 
        if videoinfo and video.id == videoinfo['id']:
            video_title = videoinfo['title']
            channel_name = videoinfo['channel']
            channel_id = videoinfo['channelId']
            if not channel_id:
                channel_id = "UC2hkwpSfrl6iniQNbwFXMog"
            video_duration = get_duration(videoinfo["duration"])
        
        # Uses fallback function to fetch video data directly from the video page
        elif fallback_data := yt_video_data_fallback(video.id):
            logger.info(f"using fallback for https://www.youtube.com/watch?v={video.id}")
            video_title = fallback_data["title"]
            channel_name = fallback_data["author"]
            channel_id = fallback_data["channelId"]
            video_duration = fallback_data["lengthSeconds"]
            if list_broken_videos: 
                failed_yt_search.append(video.id)

        else:
            logger.warning(f"error with https://www.youtube.com/watch?v={video.id}")
            if log_errors: 
                failed_ID.append(video.id)
            continue
        
        video.title = video_title
        video.author_name = channel_name
        video.author_id = channel_id
        video.length_s = video_duration

        if video.date_added_ms:
            latest_added_timestamp_ms = max(latest_added_timestamp_ms, video.date_added_ms)

        playlist.videos.append(video)
        write_counter += 1
        logger.info(f"https://www.youtube.com/watch?v={video.id} written successfully")
    
    playlist.date_last_updated_ms = latest_added_timestamp_ms
    write_output(playlist,stdin,write_counter)
    print_errors(failed_ID, failed_yt_search)



def main():
    # set logging to DEBUG for debug mode
    logger.setLevel(logging.ERROR)
    logging.basicConfig(format='[%(levelname)s] - %(message)s')
    parser = argparse.ArgumentParser(description="Import youtube playlists")
    parser.add_argument("filepath", type=str, help="path to a valid .txt or .csv playlist file or files", nargs="*")
    parser.add_argument('-a', '--list-all',action='store_true', help="Takes all .txt and csv files as input from the current working directory.")
    parser.add_argument('-b', '--list-broken-videos',action='store_true', help="Lists videos that were added but have possibly broken metadata (for debugging).")
    parser.add_argument('-e', '--log-errors',action='store_true', help="Also lists the videos that failed the metadata fetch")
    parser.add_argument('-s', '--stdin',action='store_true', help="Takes stdin as input and outputs dirextly to stdout")
    parser.add_argument('-n', '--name', required=False, help="sets a name for playlist, otherwise uses input filename")

    flags = parser.parse_args(args=None if sys.argv[1:] else ['--help'])

    playlist_files = flags.filepath
    log_errors = flags.log_errors
    list_broken_videos = flags.list_broken_videos
    stdin = flags.stdin
    pl_name = flags.name

    # list txt and csv files in current working directory
    if flags.list_all:
        playlist_files = []
        for i in os.listdir(os.getcwd()):
            if os.path.isfile(i):
                if i.split(".")[-1] in ("txt", "csv"):
                    playlist_files.append(i)

    if len(playlist_files) == 1:
        process_playlist(playlist_files[0], log_errors, list_broken_videos,stdin, pl_name)
        exit(0)
    elif len(playlist_files) > 1:
        for i, playlist in enumerate(playlist_files, start=1):
            filename = str(Path(playlist).name)
            print(f"[{i}/{len(playlist_files)}] {filename}", file=sys.stderr)
            try:
                process_playlist(playlist, log_errors, list_broken_videos, stdin)
            except Exception as e:
                logger.critical(f"{filename} Failed: {e}")
            print(" ", file=sys.stderr)
        exit(0)
    elif stdin:
        process_playlist("", stdin=stdin, pl_name=pl_name)


logger = logging.getLogger(__name__)

if __name__ == "__main__":
    main()
