import subprocess
import json
import pprint
import xml.etree.ElementTree as ET

import timecode

DEFAULT_AUDIO_SAMPLE_RATE = 48000
DEFAULT_VIDEO_FRAME_RATE = 25

timebase = timecode.Timecode(25)

list_of_files = [
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071220_C001.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071221_C002.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071223_C003.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071229_C004.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071243_C005.mov",
]


##
## PROBE THE FILES WITH ffprobe
##
files_probed = []
for item in list_of_files:

    data = subprocess.run(
        [
            'ffprobe', item,
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            '-v', 'quiet'
        ],
        shell=True,
        capture_output=True
    )
    probe = json.loads(data.stdout)

    FOUND_VIDEO = False
    FOUND_AUDIO = False

    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    if video_stream is not None:
        FOUND_VIDEO = True

    audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
    if audio_stream is not None:
        FOUND_AUDIO = True

    if FOUND_VIDEO and FOUND_AUDIO == False:
        print(item, ': this file contains neither video or audio streams')

    files_probed.append( (item, probe) )



##
## ANALYSE THE BASIC METADATA
##

for clip_filepath, probe in files_probed:

    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)

    if video_stream:
        frames = video_stream['nb_frames']
        framerate = video_stream['time_base']
        if 'timecode' in video_stream['tags']:
            timecode = video_stream['tags']['timecode']
        else:
            timecode = 'NA'
        print(clip_filepath, frames, framerate, timecode)
    else:
        if audio_stream:
            audio_sample_rate = int(audio_stream['sample_rate'])
        else:
            audio_sample_rate = DEFAULT_AUDIO_SAMPLE_RATE

        if 'time_reference' in probe['format']['tags']:
            samples_since_midnight = int(probe['format']['tags']['time_reference'])
            seconds = samples_since_midnight / audio_sample_rate
            frames = seconds * DEFAULT_VIDEO_FRAME_RATE
            print(clip_filepath, audio_sample_rate, frames, timebase.toTC(frames))

##
## BUILD THE XML
##

# Create a parsable XML from the structure written above
tree = ET.ElementTree( ET.fromstring(pr_xml_base_structure) )
root = tree.getroot()

bin_master_clips = root.find('bin')

print(bin_master_clips)
