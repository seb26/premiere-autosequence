import subprocess
import json
import os
import re
import functools
import xml.etree.ElementTree as ET
from urllib.parse import quote


# APPLICATION ASSETS
import timecode
from ffprobe_xml_structure import *


# DEFAULTS
DEFAULT_AUDIO_SAMPLE_RATE = 48000
DEFAULT_VIDEO_FRAME_RATE = 25
TIMEBASE = timecode.Timecode(DEFAULT_VIDEO_FRAME_RATE)

VALID_FRAME_RATES = [ 23.976, 23.98, 24, 25, 29.97, 30 ]

# PROTOTYPE FILE DATA
# TEMPORARY
list_of_files = [
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_018.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_001.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_002.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_003.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_004.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_005.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_006.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_007.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_008.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_009.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_010.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_011.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_012.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_013.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_014.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_015.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_016.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_017.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\T001C010_190511_R6XC.[1043405-1045094].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\A002C001_190511_R6XC.[1230177-1232759].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\A002C002_190511_R6XC.[1238357-1239433].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\A002C003_190511_R6XC.[1240863-1243708].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\A002C004_190511_R6XC.[1245536-1249161].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\A002C005_190511_R6XC.[1252221-1255242].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\A002C006_190511_R6XC.[1280886-1283330].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\A002C007_190511_R6XC.[1284452-1286174].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\A003C001_190511_R6XC.[1540211-1544727].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\A003C002_190511_R6XC.[1562614-1566466].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\A003C003_190511_R6XC.[1572393-1580542].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\A003C004_190511_R6XC.[1582384-1587340].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\A003C005_190511_R6XC.[1680865-1684154].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\A003C006_190511_R6XC.[1687928-1691424].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\T001C001_190510_R6XC.[0771071-0773182].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\T001C002_190510_R6XC.[0775552-0777995].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\T001C004_190510_R6XC.[0812500-0814970].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\T001C005_190510_R6XC.[0844782-0846615].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\T001C006_190510_R6XC.[0945567-0954891].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\T001C007_190511_R6XC.[0975322-0977760].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\T001C008_190511_R6XC.[0998481-0999978].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\T001C009_190511_R6XC.[1020697-1022390].mov",
]


class MediaFile(object):


    def __init__(self, filepath):
        # Establish its filepath
        if os.path.isfile(filepath):
            self.filepath = filepath
            self.filename = os.path.basename(self.filepath)
            self.fileURL = 'file://localhost/' + quote( self.filepath.replace(os.sep, '/') )
        else:
            print(filepath, ': this file does not exist.')
            return None

        # Probe it and its probe result to the object
        data = subprocess.run(
            [
                'ffprobe', self.filepath,
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                '-v', 'quiet'
            ],
            shell=True,
            capture_output=True
        )
        # Save the probe data
        self.probe = json.loads(data.stdout)

        video_streams = [ stream for stream in self.probe['streams'] if stream['codec_type'] == 'video' ]
        audio_streams = [ stream for stream in self.probe['streams'] if stream['codec_type'] == 'audio' ]

        if len(video_streams) >= 1:
            # Consider it video
            self.mediaType = 'video'
        elif len(video_streams) == 0 and len(audio_streams) >= 1:
            # Consider it audio
            self.mediaType = 'audio'
        elif len(video_streams) == 0 and len(audio_streams) == 0:
            self.mediaType = None
            print(self.filepath, ': this file contains neither video or audio streams')
            return None

        print(self.mediaType)
        # But does it have embedded audio?
        self.audioStreams = len(audio_streams)

        if self.mediaType == 'video':
            # Work with only the first video stream, if multiple
            video_stream = video_streams[0]

            self.frameCount = video_stream['nb_frames']
            # Trim off "1/" before FPS, and make it an integer.
            self.frameRate = int(video_stream['codec_time_base'][2:])
            self.duration = video_stream['duration_ts']

            # Create a timebase object, with which we can make TC/frame conversions
            self._timebase = timecode.Timecode(self.frameRate)
            found_timecode = None

            # Search for the timecode inside the video stream
            if 'timecode' in video_stream['tags']:
                found_timecode = video_stream['tags']['timecode']

            # If it's not there, check outside in the Format
            elif 'timecode' in self.probe['format']['tags']:
                found_timecode = self.probe['format']['tags']['timecode']

            if found_timecode:
                try:
                    self._timebase.validateTC(found_timecode)
                    self.timecode = found_timecode
                    self.startFrame = self._timebase.toFrames(found_timecode)
                except ValueError:
                    # Well, it had something, but it didn't validate
                    print(self.filepath, ': this file doesn\'t have embedded timecode.')
                    self.startFrame = 0
                    self.timecode = '00:00:00:00'
            else:
                # Couldn't find it.
                print(self.filepath, ': this file doesn\'t have embedded timecode.')
                self.startFrame = 0
                self.timecode = '00:00:00:00'

            # More video attributes
            for attrib in [ 'codec_name', 'width', 'height' ]:
                setattr(self, attrib, video_stream[attrib])

            # More complicated attributes
            if 'sample_aspect_ratio' in video_stream:
                if video_stream['sample_aspect_ratio'] == '1:1':
                    self.pixelAspectRatio = 'square'
                else:
                    # Otherwise stick the ratio there in it
                    self.pixelAspectRatio = video_stream['sample_aspect_ratio']
            if 'field_order' in video_stream:
                if video_stream['field_order'] == 'progressive':
                    self.fieldDominance = 'none'
                else:
                    # This could potentially be problematic and not be the correct value.
                    # Whatever, I'm not forward thinking enough to facilitate interlaced media.
                    self.fieldDominance = video_stream['field_order']

        if self.audioStreams > 0:
            # If there is any audio at all, catalog it
            # Base most of the attributes on the very first audio stream
            # Ignore subsequent audio streams (note, this doesn't refer to channels)
            audio_stream = audio_streams[0]
            self.audio_sample_rate = int(audio_stream['sample_rate'])
            self.audioChannels = audio_stream['channels']
            self.audioBitDepth = audio_stream['bits_per_raw_sample']

        if self.mediaType == 'audio':
            # Establish the timecode & duration, only for audio files
            # Not video with embedded audio

            BEXT_DATA = {}
            if 'comment' in self.probe['format']['tags']:
                comment = self.probe['format']['tags']['comment']
                if comment[0] == 'z':
                    # If it starts with z, it's probably BEXT chunks
                    # Create keys and values for the BEXT data
                    for k, v in [ line.split('=') for line in comment.splitlines() ]:
                        BEXT_DATA[k] = v

            if 'zSPEED' in BEXT_DATA.keys():
                # Regex match in the format: ##.###AA (e.g. 25.000ND)
                match = re.match( r"(\d*?\.\d*)(\w*)", BEXT_DATA['zSPEED'], re.I )
                if match:
                    rate, dropframe = match.groups()
                    # Try end up with a clean integer. Only float if it's a decimal.
                    if float(rate).is_integer():
                        framerate = int( float(rate) )
                    else:
                        framerate = float(rate)
                    # Check if it's a valid frame rate and then assign it
                    if framerate in VALID_FRAME_RATES:
                        self.frameRate = framerate

            if not hasattr(self, 'frameRate'):
                # If we didn't manage to find the frame rate
                self.frameRate = DEFAULT_VIDEO_FRAME_RATE

            # Search for an audio time-of-day timecode
            # Time_reference is usually the number of samples since midnight.
            if 'time_reference' in self.probe['format']['tags']:
                self._timebase = timecode.Timecode(self.frameRate)
                samples_since_midnight = int(self.probe['format']['tags']['time_reference'])
                seconds_since_midnight = samples_since_midnight / self.audio_sample_rate
                self.startFrame = int(seconds_since_midnight * self.frameRate)
                self.timecode = self._timebase.toTC(self.startFrame)

            # Audio duration is: File duration (seconds, float) * Video frame rate
            # e.g. 60 second recording * 25 FPS = 1,500 frames
            # Finish with int() because we always need a whole number of frames.
            self.duration = int( float(audio_stream['duration']) * self.frameRate )


    # Compare on the basis of start frame
    def __lt__(self, other):
        return self.startFrame < other.startFrame
    def __eq__(self, other):
        return self.startFrame == other.startFrame



media_files = { 'video': [], 'audio': [] }

for filepath in list_of_files:
    media_file = MediaFile(filepath)

    if media_file.mediaType == 'video':
        media_files['video'].append(media_file)

    elif media_file.mediaType == 'audio':
        media_files['audio'].append(media_file)

    else:
        continue

    # DEBUGGING: print metadata to stdout
    # print('STARTFRAME', media_file.startFrame, type(media_file.startFrame))
    # print(media_file.filename, media_file.frameRate, media_file.duration, media_file.timecode)

# Sort by start timecode (startFrame)
media_files['video'].sort()
media_files['audio'].sort()






##
## BUILD THE XML
##

def setElem(target, element, value):
    """Given an element (1. target),
    quickly add an <element> to it (2. element),
    and then set its text contents (3. value). CONVERTS TO STRING.

    Returns the element at the end, if you need it"""
    e = target.find(element)
    e.text = str(value)
    return e


def buildXML():
    # Create a parsable XML from the structure written above
    tree = ET.ElementTree( ET.fromstring(pr_xml_base_structure) )
    root = tree.getroot()

    # [ ROOT BIN
    top_bin = root.find('bin')
    setElem(top_bin, 'name', 'AUTOSEQ_1')
    # [ ROOT BIN - Contents
    top_bin_items = top_bin.find('children')
    # >> [ MASTER CLIPS
    bin_master_clips = top_bin_items.find('bin')
    bin_master_clips_items = bin_master_clips.find('children')
    setElem(bin_master_clips, 'name', 'AUTOSEQ_1_MASTER_CLIPS')



    # Quickly set up the sequence
    # [ ROOT BIN - Sequence
    sequence = top_bin_items.find('sequence')
    sequence.set('id', 'AUTOSEQ_1')
    setElem(sequence, 'name', 'AUTOSEQ_1')

    # Apply the default sequence attributes
    for k, v in pr_xml_default_sequence_attributes.items():
        sequence.set(k, v)
    # Create some 1x basic video
    for k, v in pr_xml_default_sequence_video_track_attributes.items():
        video_track = sequence.find('media').find('video').find('track')
        video_track.set(k, v)

    # And 1x mono audio track
    for k, v in pr_xml_default_sequence_audio_track_attributes.items():
        audio_track = sequence.find('media').find('audio').find('track')
        audio_track.set(k, v)


    # Then get the intended duration of the sequence
    # This is:
    #       Find which is earliest, video or audio
    #       Find which is latest, video or audio
    #       Latest startTC + duration - Earliest startTC
    #       == Total sequence duration
    earliest_clip = min(media_files['video'][0], media_files['audio'][0])
    earliest_clip_startFrame = earliest_clip.startFrame
    latest_clip = max(media_files['video'][-1], media_files['audio'][-1])
    latest_clip_endFrame = latest_clip.startFrame + latest_clip.duration

    sequence_total_duration = latest_clip_endFrame - earliest_clip_startFrame
    setElem(sequence, 'duration', str(sequence_total_duration))

    index = 1
    for media in media_files['video']:

        # Begin establishing a Master Clip with a new ID for it
        masterID = 'MASTER_' + str(index)
        masterID_component = masterID + '_COMPONENT_1'
        masterID_file = masterID + '_FILE_1'

        # Create a new master clip, blank from the template
        master_clip_root = ET.fromstring(pr_xml_video_masterclip)
        master_clip_root.set('id', masterID)

        # Set its name and other attributes
        setElem(master_clip_root, 'name', media.filename)
        setElem(master_clip_root, 'masterclipid', masterID)
        setElem(master_clip_root.find('rate'), 'timebase', media.frameRate)
        setElem(master_clip_root, 'duration', media.duration)
        setElem(master_clip_root, 'in', '0')
        setElem(master_clip_root, 'out', media.duration)
        set

        # Go inside and add directly to the video track
        master_clip_track = master_clip_root.find('media')[0][0][0]
        master_clip_track.set('id', masterID_component)
        setElem(master_clip_track, 'name', media.filename)
        setElem(master_clip_track, 'masterclipid', masterID)
        setElem(master_clip_track.find('rate'), 'timebase', media.frameRate)

        # And then set the <file> attributes as well
        master_clip_file = master_clip_track.find('file')
        master_clip_file.set('id', masterID_file)
        setElem(master_clip_file, 'name', media.filename)
        setElem(master_clip_file, 'pathurl', media.fileURL)
        setElem(master_clip_file.find('rate'), 'timebase', media.frameRate)

        master_clip_file_characteristics = master_clip_file.find('media').find('video').find('samplecharacteristics')
        setElem(master_clip_file_characteristics.find('rate'), 'timebase', media.frameRate)
        setElem(master_clip_file_characteristics, 'width', media.width)
        setElem(master_clip_file_characteristics, 'height', media.height)
        setElem(master_clip_file_characteristics, 'pixelaspectratio', media.pixelAspectRatio)
        setElem(master_clip_file_characteristics, 'fielddominance', media.fieldDominance)

        # Append it to the Master clips bin
        bin_master_clips_items.append(master_clip_root)

        # Establish the sequence with the characteristics of the first clip
        if index == 1:
            setElem(sequence.find('rate'), 'timebase', media.frameRate)
            sequence_timecode = sequence.find('timecode')
            setElem(sequence_timecode.find('rate'), 'timebase', media.frameRate)

            # The sequence starts at the startFrame of the first clip
            sequence_startFrame = media.startFrame
            setElem(sequence_timecode, 'frame', sequence_startFrame)
            setElem(sequence_timecode, 'string', media.timecode)

            video_track_format = sequence.find('media').find('video').find('format').find('samplecharacteristics')
            video_track_format.append(master_clip_file_characteristics)
            setElem(video_track_format.find('codec'), 'name', media.codec_name)

        # Begin writing to the timeline
        clip_timeline_start = media.startFrame - sequence_startFrame
        clip_timeline_end = clip_timeline_start + media.duration
        clip_timeline_in = "0"
        clip_timeline_out = media.duration

        add_clip_to_timeline = ET.fromstring(pr_xml_video_clip_on_timeline)
        setElem(add_clip_to_timeline, 'masterclipid', masterID)
        # Re-add the file details from the masterclip
        add_clip_to_timeline.find('file').append(master_clip_file)
        add_clip_to_timeline.find('file').set('id', masterID_file)
        setElem(add_clip_to_timeline, 'name', media.filename)
        setElem(add_clip_to_timeline, 'duration', media.duration)
        setElem(add_clip_to_timeline.find('rate'), 'timebase', media.frameRate)
        setElem(add_clip_to_timeline, 'start', clip_timeline_start)
        setElem(add_clip_to_timeline, 'end', clip_timeline_end)
        setElem(add_clip_to_timeline, 'in', clip_timeline_in)
        setElem(add_clip_to_timeline, 'out', clip_timeline_out)
        video_track.append(add_clip_to_timeline)

        # Move onto next media file
        index += 1

    tree.write('samples\\sample_out_3.xml')

buildXML()
