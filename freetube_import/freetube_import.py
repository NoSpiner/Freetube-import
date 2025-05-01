import uuid
import time
from pathlib import Path
from .youtube_search import YoutubeSearch
import json
import argparse
from tqdm import tqdm
import re
import sys
import requests
import os

def YT_authordata(yt_id)->list:
    if yt_id[0]=="_":
        return YoutubeSearch('https://www.youtube.com/watch?v=//'+yt_id, max_results=1).to_dict()
    return YoutubeSearch('https://www.youtube.com/watch?v='+yt_id, max_results=1).to_dict()

def yt_video_title_fallback(url):
    web_request = requests.get("https://www.youtube.com/watch?v="+url)
    site_html = web_request.text
    title = re.search(r'<title\s*.*?>(.*?)</title\s*>', site_html, re.IGNORECASE)
    return title.group(1).split("- YouTube")[0]

def get_duration(time):
    try:
        time_parts=re.split(r"[.:]",time)
        seconds=int(time_parts[-1])
        minutes=int(time_parts[-2])
        hours=0
        if len(time_parts)==3:
            hours=int(time_parts[0])
        return seconds+minutes*60+hours*3600
    except Exception as e:
        print(e)
        return "0:00"

def process_txt(path):
    with open(path, "r") as inputfile:
        Videos=inputfile.readlines()
        Video_IDs=[]
        for i in Videos:
            id=re.split(r"\?v=|youtu\.be/",i)
            try:
                id=id[1].rstrip()
                Video_IDs.append(id)
            except IndexError:
                pass
    return Video_IDs

def process_csv(path):
    with open(path, "r") as inputfile:
        Videos=inputfile.readlines()
        Video_IDs=[]
        data_start=False
        for i in Videos:
            if not data_start:
                data_start=True
                continue
            if data_start:
                if not len(i.split(",")[0].strip())==11:
                    continue
                Video_IDs.append(i.split(",")[0].strip())
    return Video_IDs

#Does the actual parsing and writing
def process_playlist(playlist_filepath, log_errors=False,list_broken_videos=False):
    playlistname=str(Path(playlist_filepath).name)
    playlistformat=playlistname.split(".")[1]
    playlistname=playlistname.split(".")[0]
    Video_IDs=[]
    if playlistformat=="txt":
        Video_IDs=process_txt(playlist_filepath)
    elif playlistformat=="csv":
        Video_IDs=process_csv(playlist_filepath)
    else:
        print(f"{playlistformat} is invalid file format.")
        return
    print(f"Reading file {playlist_filepath}, the playlistfile has {len(Video_IDs)} entries")
    print(f"writing to file {playlistname}.db")
    playlist_UUID=uuid.uuid4()
    current_time_ms = int(time.time() * 1000)
    playlist_dict=dict(
        playlistName=playlistname,
        videos=[],
        _id="ft-playlist--"+str(playlist_UUID),
        createdAt=current_time_ms,
        lastUpdatedAt=current_time_ms
    )
    write_counter=0
    failed_yt_search=[]
    failed_ID=[]
    for i in tqdm(Video_IDs):
    #for i in Video_IDs:
        video_UUID=uuid.uuid4()
        current_time_ms = int(time.time()*1000)
        videoinfo=YT_authordata(i)
        if len(videoinfo)==0:
            failed_ID.append(i)
            continue
        video_title=videoinfo[0]['title']
        channel_id=videoinfo[0]['channelId']
        if channel_id==None:
            channel_id="UC2hkwpSfrl6iniQNbwFXMog"
        video_duration=get_duration(videoinfo[0]["duration"])
        try:
            videoinfo_ID=videoinfo[0]['url_suffix'].split("?v=")[1].split("&pp=")[0]
            if videoinfo_ID!=i:
                video_title=yt_video_title_fallback(i)
                if len(video_title)<2:
                    failed_ID.append(i)
                    continue
                video_duration="0:00"
                failed_yt_search.append(i)
        except:
            failed_ID.append(i)
            continue
        video_dict=dict(
            videoId=i,
            title=video_title,
            author=videoinfo[0]['channel'],
            authorId=channel_id,
            published="",
            lengthSeconds=video_duration,
            timeAdded=current_time_ms,
            type="video",
            playlistItemId=str(video_UUID)
        )
        playlist_dict["videos"].append(video_dict)
        write_counter+=1
    if len(playlist_dict["videos"]) !=0:
        outputfile=open(playlistname+".db","w")
        outputfile.write(json.dumps(playlist_dict,separators=(',', ':'))+"\n")
        outputfile.close()
        print(f"Task failed successfully! {playlistname}.db written, with {write_counter} entries")
    else:
        print("No entries to write")
    if len(failed_ID) !=0 and log_errors:
        print("[Failed playlist items]")
        for i in failed_ID:
            print('https://www.youtube.com/watch?v='+i)
    if len(failed_yt_search) !=0 and list_broken_videos:
        print("[Videos with possibly broken metadata]")
        for i in failed_yt_search:
            print('https://www.youtube.com/watch?v='+i)

def main():
    parser = argparse.ArgumentParser(description="Import youtube playlists")
    parser.add_argument("filepath", type=str, help="path to a valid .txt or .csv playlist file or files", nargs="*")
    parser.add_argument('-a', '--list-all',action='store_true', help="Takes all .txt and csv files as input from the current working directory.")
    parser.add_argument('-b', '--list-broken-videos',action='store_true', help="Lists videos that were added but have possibly broken metadata (for debugging).")
    parser.add_argument('-e', '--log-errors',action='store_true', help="Also lists the videos that failed the metadata fetch")

    flags = parser.parse_args(args=None if sys.argv[1:] else ['--help'])

    playlist_files=flags.filepath
    log_errors=flags.log_errors
    list_broken_videos=flags.list_broken_videos
    #list txt and csv files in current working directory
    if flags.list_all:
        playlist_files=[]
        for i in os.listdir(os.getcwd()):
            if os.path.isfile(i):
                if i.split(".")[-1] in ("txt", "csv"):
                    playlist_files.append(i)

    if len(playlist_files)==1:
        process_playlist(playlist_files[0],log_errors,list_broken_videos)
        exit(0)
    for i,playlist in enumerate(playlist_files,start=1):
        filename=str(Path(playlist).name)
        print(f"[{i}/{len(playlist_files)}] {filename}")
        try:
            process_playlist(playlist,log_errors,list_broken_videos)
        except Exception as e:
            print(f"{filename} Failed: {e}")
        print(" ")

if __name__ == "__main__":
    main()
