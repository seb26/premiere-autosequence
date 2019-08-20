import subprocess
import json
import pprint

list_of_files = [
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071220_C001.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071221_C002.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071223_C003.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071229_C004.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071243_C005.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\AUDIO\\F8_SD2\\130619\\130619_001.WAV",
    "Q:\\Projects\\HAZEN_ALPHA\\AUDIO\\F8_SD2\\130619\\130619_002.WAV",
    "Q:\\Projects\\HAZEN_ALPHA\\AUDIO\\F8_SD2\\130619\\130619_003.WAV",
    "Q:\\Projects\\HAZEN_ALPHA\\AUDIO\\F8_SD2\\130619\\130619_004.WAV",
    "Q:\\Projects\\HAZEN_ALPHA\\AUDIO\\F8_SD2\\130619\\130619_005.WAV",
]

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

    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    if video_stream is None:
        print(item, ': No video stream found')

    audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
    if audio_stream is None:
        print(item, ': No audio stream found')

    if video_stream:
        frames = video_stream['nb_frames']
        framerate = video_stream['time_base']
        if 'timecode' in video_stream['tags']:
            timecode = video_stream['tags']['timecode']
        else:
            timecode = 'NA'
        print(item, frames, framerate, timecode)
    else:
        if audio_stream:
            audio_sample_rate = int(audio_stream['sample_rate'])
        else:
            audio_sample_rate = 48000

        if 'time_reference' in probe['format']['tags']:
            samples_since_midnight = int(probe['format']['tags']['time_reference'])
            frames = samples_since_midnight / audio_sample_rate
            print(frames)
