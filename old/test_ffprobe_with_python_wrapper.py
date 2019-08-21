#!/usr/bin/env python
from __future__ import unicode_literals, print_function
import argparse
import ffmpeg
import sys

"""
parser = argparse.ArgumentParser(description='Get video information')
parser.add_argument('in_filename', help='Input filename')
args = parser.parse_args()
"""


# "Q:\Avid MediaFiles\MXF\2\A001_06071223_C003.mxf"

list_of_files = [
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071220_C001.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071221_C002.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071223_C003.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071229_C004.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071243_C005.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071244_C006.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071251_C007.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071317_C008.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071319_C009.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071325_C010.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071329_C011.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071332_C012.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071335_C013.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071336_C014.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071707_C015.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071717_C016.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071722_C017.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071726_C018.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071737_C019.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071740_C020.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071743_C021.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071748_C022.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071750_C023.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071754_C024.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071759_C025.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071810_C026.mov",
]

for item in list_of_files:

    try:
        probe = ffmpeg.probe(item)
    except ffmpeg.Error as e:
        print(e.stderr, file=sys.stderr)
        sys.exit(1)

    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    if video_stream is None:
        print('No video stream found', file=sys.stderr)
        sys.exit(1)

    audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
    if audio_stream is None:
        print('No audio stream found', file=sys.stderr)

    num_frames = int(video_stream['duration_ts'])
    if 'timecode' in video_stream['tags']:
        print(video_stream['tags']['timecode'])
    print(num_frames)



    """
    width = int(video_stream['width'])
    height = int(video_stream['height'])
    num_frames = int(video_stream['nb_frames'])
    print('width: {}'.format(width))
    print('height: {}'.format(height))
    print('num_frames: {}'.format(num_frames))
    """
