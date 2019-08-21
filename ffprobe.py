import subprocess
import json
import os
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

# PROTOTYPE FILE DATA
# TEMPORARY
list_of_files = [
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071220_C001.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071243_C005.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071221_C002.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071223_C003.mov",
    "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071229_C004.mov",
]


class MediaFile(object):


    def __init__(self, filepath):
        # Establish its filepath
        if os.path.isfile(filepath):
            self.filepath = filepath
            self.filename = os.path.basename(self.filepath)
            self.fileURL = 'file://localhost' + quote( self.filepath.replace(os.sep, '/') )
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
        probe = json.loads(data.stdout)

        # Save the probe data
        self.probe = probe

        # Determine if it has video and/or audio
        FOUND_VIDEO = False
        FOUND_AUDIO = False

        video_stream = next((stream for stream in self.probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream is not None:
            FOUND_VIDEO = True

        audio_stream = next((stream for stream in self.probe['streams'] if stream['codec_type'] == 'audio'), None)
        if audio_stream is not None:
            FOUND_AUDIO = True

        if FOUND_VIDEO and FOUND_AUDIO == False:
            print(item, ': this file contains neither video or audio streams')
            return None
            # Realistically, we should return None on this file
            # It won't be able to pass any of the remaining operations in this function


        # Put our critical metadata as attributes, easily accessible
        # First, video
        if video_stream:
            self.frameCount = video_stream['nb_frames']
            # Trim off "1/" before FPS, and make it an integer.
            self.frameRate = int(video_stream['codec_time_base'][2:])
            # Create a timebase object, with which we can make TC/frame conversions
            self.duration = video_stream['duration_ts']

            # TODO: improve timecode handling
            self._timebase = timecode.Timecode(self.frameRate)
            if 'timecode' in video_stream['tags']:
                self.timecode = video_stream['tags']['timecode']
                try:
                    self._timebase.validateTC(self.timecode)
                    self.startFrame = self._timebase.toFrames(self.timecode)
                except ValueError:
                    print(self.filepath, ': this file doesn\'t have embedded timecode.')
            else:
                self.timecode = None
                self.startFrame = '00:00:00:00'

            # More video attributes
            attributes_to_assign = [
                'codec_name',
                'width',
                'height',
            ]
            for attrib in attributes_to_assign:
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


        else:
            # Only add attributes for the audio, if there is no video
            # i.e. the audio is on its own, a BWF
            # No use at the moment for us to collect audio attributes for embedded camera audio
            # TODO: Process the iXML data in ['tags']['comment'] and get the SPEED
            if audio_stream:
                self.audio_sample_rate = int(audio_stream['sample_rate'])
            else:
                self.audio_sample_rate = DEFAULT_AUDIO_SAMPLE_RATE

            if 'time_reference' in probe['format']['tags']:
                self.samples_since_midnight = int(probe['format']['tags']['time_reference'])
                seconds = samples_since_midnight / audio_sample_rate
                self.frameCount = seconds * DEFAULT_VIDEO_FRAME_RATE
                self.timecode = DEFAULT_TIMEBASE.toTC(self.frameCount)


    def __lt__(self, other):
        # Compare on the basis of start frame
        return self.startFrame < other.startFrame
    def __eq__(self, other):
        return self.startFrame == other.startFrame



media_files = []

for filepath in list_of_files:
    media_file = MediaFile(filepath)
    # print(media_file.filename, media_file.frameRate, media_file.duration, media_file.timecode)
    media_files.append(media_file)

# Sort by start timecode (startFrame)
media_files.sort()






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
#       LastClip's Start TC [+] LastClip's duration [-] FirstClip's Start TC
# media_files must be sorted by Start TC before you can perform this action
# Otherwise the duration will be inaccurate
sequence_total_duration = media_files[-1].startFrame + media_files[-1].duration - media_files[0].startFrame
setElem(sequence, 'duration', str(sequence_total_duration))

index = 1
for media in media_files:

    # Establish the sequence with the characteristics of the first clip
    if index == 1:
        setElem(sequence.find('rate'), 'timebase', media.frameRate)
        sequence_timecode = sequence.find('timecode')
        setElem(sequence_timecode.find('rate'), 'timebase', media.frameRate)
        setElem(sequence_timecode, 'frame', media.startFrame)
        setElem(sequence_timecode, 'string', media.timecode)

        video_track_format = sequence.find('media').find('video').find('format').find('samplecharacteristics')
        setElem(video_track_format.find('rate'), 'timebase', media.frameRate)
        setElem(video_track_format.find('codec'), 'name', media.codec_name)
        setElem(video_track_format, 'width', media.width)
        setElem(video_track_format, 'height', media.height)
        setElem(video_track_format, 'pixelaspectratio', media.pixelAspectRatio)
        setElem(video_track_format, 'fielddominance', media.fieldDominance)

    masterID = 'MASTER_' + str(index)
    masterID_component = masterID + '_COMPONENT_1'
    masterID_file = masterID + '_FILE_1'

    # Create a new master clip, blank from the template
    master_clip_root = ET.fromstring(pr_xml_video_masterclip)

    # Set its name and other attributes
    setElem(master_clip_root, 'name', media.filename)
    setElem(master_clip_root, 'masterclipid', masterID)
    master_clip_root.set('id', masterID)
    setElem(master_clip_root.find('rate'), 'timebase', media.frameRate)
    setElem(master_clip_root, 'duration', media.duration)
    setElem(master_clip_root, 'in', '0')
    setElem(master_clip_root, 'out', media.duration)
    set

    # Go inside and add directly to the video track
    master_clip_track = master_clip_root.find('media')[0][0][0]
    setElem(master_clip_track, 'name', media.filename)
    setElem(master_clip_track, 'masterclipid', masterID)
    master_clip_track.set('id', masterID_component)
    setElem(master_clip_track.find('rate'), 'timebase', media.frameRate)

    # And then set the <file> attributes as well
    master_clip_file = master_clip_track.find('file')
    setElem(master_clip_file, 'name', media.filename)
    setElem(master_clip_file, 'pathurl', media.fileURL)
    setElem(master_clip_file.find('rate'), 'timebase', media.frameRate)
    master_clip_file.set('id', masterID_file)

    # Append it to the Master clips bin
    bin_master_clips_items.append(master_clip_root)

    # Write it to the sequence
    if index == 1:
        sequence_startFrame = media.startFrame

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

ET.dump(tree)
