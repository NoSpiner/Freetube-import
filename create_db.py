import uuid
import time
from sys import argv
from pathlib import Path
from youtube_search import YoutubeSearch
import json
import argparse
from tqdm import tqdm

def YT_authordata(yt_id):
    results = YoutubeSearch('https://www.youtube.com/watch?v='+yt_id, max_results=1).to_dict()
    return results

def process_txt(path):
    with open(path, "r") as inputfile:
        Videos=inputfile.readlines()
        Video_IDs=[]
        for i in Videos:
            id=i.split("?v=")
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
            if i.split(",")[0]=="Video ID":
                data_start=True
                continue
            if data_start:
                Video_IDs.append(i.split(",")[0])
    return Video_IDs

parser = argparse.ArgumentParser(description="Import youtube playlists")
parser.add_argument("filepath", type=str, help="path to a valid .txt or .csv playlist file")
parser.add_argument('-l', '--log-errors',action='store_true', help="Also lists the videos that failed the metadata fetch")
flags = parser.parse_args()
playlistname=str(Path(flags.filepath).name)
playlistformat=playlistname.split(".")[1]
playlistname=playlistname.split(".")[0]
playlist_UUID=uuid.uuid4()
current_time_ms = int(time.time() * 1000)
Video_IDs=[]
if playlistformat=="txt":
    Video_IDs=process_txt(flags.filepath)
elif playlistformat=="csv":
    Video_IDs=process_csv(flags.filepath)
else:
    print(f"{playlistformat} is invalid file format.")
    exit(1)

outputfile=open(playlistname+".db","w")
print(f"Reading file {flags.filepath}, the playlistfile has {len(Video_IDs)} entries")
print(f"writing to file {playlistname}.db")
playlist_dict=dict(
    playlistName=playlistname,
    videos=[],
    _id="ft-playlist--"+str(playlist_UUID),
    createdAt=current_time_ms,
    lastUpdatedAt=current_time_ms
)
counter=0
failed_ID=[]
for i in tqdm(Video_IDs):
#for i in Video_IDs:
    video_UUID=uuid.uuid4()
    current_time_ms = int(time.time()*1000)
    videoinfo=YT_authordata(i)
    if len(videoinfo)==0:
        failed_ID.append(i)
        continue
    video_dict=dict(
        videoId=i,
        title=videoinfo[0]['title'],
        author=videoinfo[0]['channel'],
        authorId="UC2hkwpSfrl6iniQNbwFXMog",
        published="",
        lengthSeconds="0:00",
        timeAdded=current_time_ms,
        type="video",
        playlistItemId=str(video_UUID)
    )
    playlist_dict["videos"].append(video_dict)
    counter+=1
outputfile.write(json.dumps(playlist_dict,separators=(',', ':'))+"\n")
outputfile.close()
if len(failed_ID) !=0 and flags.log_errors:
    print(f"Task failed successfully! {playlistname}.db written, with {counter} entries")
    print("[Failed playlist items]")
    for i in failed_ID:
        print('https://www.youtube.com/watch?v='+i)
else:
    print(f"Task failed successfully! {playlistname}.db written, with {counter} entries")
