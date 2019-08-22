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
DEFAULT_VIDEO_TIMECODE_DISPLAYFORMAT = 'NDF'
TIMEBASE = timecode.Timecode(DEFAULT_VIDEO_FRAME_RATE)
DEFAULT_SEQUENCE_COLOURDEPTH = 24 # bit

VALID_FRAME_RATES = [ 23.976, 23.98, 24, 25, 29.97, 30 ]

DEFAULT_LABEL_COLOUR_VIDEO = 'Iris'
DEFAULT_LABEL_COLOUR_AUDIO = 'Mango'
DEFAULT_LABEL_COLOUR_SEQUENCE = 'Rose'

# PROTOTYPE FILE DATA
# TEMPORARY
list_of_files = [
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_018.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA\\190511_D01\\AUDIO\\PM\\190511\\190511_001.WAV",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\T001C010_190511_R6XC.[1043405-1045094].mov",
"Q:\\Projects\\PRODIGAL_SON\\MEDIA_TRANS\\190511_D01\\A002C001_190511_R6XC.[1230177-1232759].mov",
]


class MediaItem(object):


    def __init__(self, filepath):
        # Establish its filepath
        if os.path.isfile(filepath):
            self.filepath = filepath
            self.filename = os.path.basename(self.filepath)
            self.pathurl = 'file://localhost/' + quote( self.filepath.replace(os.sep, '/') )
            self.name = os.path.splitext(self.filename)[0]
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

        print(self.name, self.mediaType)
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
                    self.startFrame = str(self._timebase.toFrames(found_timecode))
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
                    self.pixelaspectratio = 'square'
                else:
                    # Otherwise stick the ratio there in it
                    self.pixelaspectratio = video_stream['sample_aspect_ratio']
            if 'field_order' in video_stream:
                if video_stream['field_order'] == 'progressive':
                    self.fielddominance = 'none'
                else:
                    # This could potentially be problematic and not be the correct value.
                    # Whatever, I'm not forward thinking enough to facilitate interlaced media.
                    self.fielddominance = video_stream['field_order']
            else:
                self.fielddominance = 'none'

            # Need to connect these to Ffprobe and be accurate
            self.alphatype = 'none'
            self.anamorphic = 'FALSE'

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



## INDEPENDENT FUNCTIONS
##


def createElem(parent, tag, value=''):
    # Creates a subelement of your parent
    # Set its text value to something, or empty if unspecified
    # ****NOTE***: CONVERTS TO STRING
    # And then gives this subelement back to you to use
    t = ET.SubElement(parent, tag)
    t.text = str(value)
    return t

def xml_add_framerate(frameRate, ntsc='FALSE'):
    # Give it an XML element
    # And it will immediately attach:
    #   <rate><timebase>25</timebase><ntsc>FALSE</ntsc></rate>
    rate = ET.Element('rate')
    timebase = ET.SubElement(rate, 'timebase')
    timebase.text = str(frameRate)
    n = createElem(rate, 'ntsc')
    n.text = ntsc
    return rate

def xml_add_label(colour):
    # Returns: <labels><label2>colour</label2></labels>
    labels = ET.Element('labels')
    label2 = ET.SubElement(labels, 'label2')
    label2.text = colour
    return labels



class BuildXML:

    def __init__(self):

        # Collect a centralised ID space
        self.index = {}
        for count in [ 'masterclipID', 'clipitemID', 'fileID', 'sequenceID', 'autoseqID' ]:
            # Set all IDs to 0 to start with
            # First time they get used, they will be incremented to 1
            self.index[count] = 0

    def _increment(self, indexType):
        self.index[indexType] += 1
        return indexType + '-' + str(self.index[indexType])

    def xml_masterclip_video(self, media_item):
        clip = ET.Element('clip')
        duration = createElem(clip, 'duration', str(media_item.duration))
        ismasterclip = createElem(clip, 'ismasterclip', 'True')
        name = createElem(clip, 'name', media_item.name)

        # Increment the masterclipID, and assign it back to the [media_item]
        # Add it to the id="" attribute
        # And describe it in text as <masterclipid>
        media_item.masterclipID = self._increment('masterclipID')
        clip.set('id', media_item.masterclipID )
        masterclipid_tag = createElem(clip, 'masterclipid', media_item.masterclipID)
        clip.set('explodedTracks', 'true')

        label = xml_add_label(DEFAULT_LABEL_COLOUR_VIDEO)
        clip.append(label)

        rate = xml_add_framerate(media_item.frameRate)
        clip.append(rate)

        media = createElem(clip, 'media')
        media_video = createElem(media, 'video')
        media_video_track = createElem(media_video, 'track')

        clipitem = createElem(media_video_track, 'clipitem')
        # Unlike masterclipID, clipitemID is never referenced outside of the masterclip
        # They are essentially single use
        # For every audio clip inside a master clip, please increment a new ID
        clipitem.set('id', self._increment('clipitemID'))

        clipitem.append(masterclipid_tag)
        clipitem.append(rate)
        alphatype = createElem(clipitem, 'alphatype', media_item.alphatype)
        pixelaspectratio = createElem(clipitem, 'pixelaspectratio', media_item.pixelaspectratio)
        anamorphic = createElem(clipitem, 'anamorphic', media_item.anamorphic)

        file_tag = createElem(clipitem, 'file')
        # Increment the fileID, and assign it back to the [media_item]
        # Add it to the id="" attribute
        media_item.fileID = self._increment('fileID')
        file_tag.set('id', media_item.fileID )

        file_tag.append(name)
        file_tag.append(rate)
        file_tag.append(duration)
        pathurl = createElem(file_tag, 'pathurl', media_item.pathurl)
        timecode = createElem(file_tag, 'timecode')
        timecode.append(rate)
        timecode_string = createElem(timecode, 'string', media_item.timecode)
        timecode_frame = createElem(timecode, 'frame', media_item.startFrame)
        timecode_displayformat = createElem(timecode, 'displayformat')
        # reel?

        file_tag_media = createElem(file_tag, 'media')
        file_tag_media_video = createElem(file_tag_media, 'video')
        video_samplecharx = createElem(file_tag_media_video, 'samplecharacteristics')
        video_samplecharx.append(rate)
        width = createElem(video_samplecharx, 'width', media_item.width)
        height = createElem(video_samplecharx, 'height', media_item.height)
        video_samplecharx.append(pixelaspectratio)
        video_samplecharx.append(anamorphic)
        fielddominance = createElem(video_samplecharx, 'fielddominance', media_item.fielddominance)

        return clip

    def xml_autosequence_duration(self, media_items):
        """
        # Then get the intended duration of the sequence
        # This is:
        #       Find which is earliest, video or audio
        #       Find which is latest, video or audio
        #       Latest startTC + duration - Earliest startTC
        #       == Total sequence duration
        earliest_clip = min(media_items['video'][0], media_items['audio'][0])
        earliest_clip_startFrame = earliest_clip.startFrame
        latest_clip = max(media_items['video'][-1], media_items['audio'][-1])
        latest_clip_endFrame = latest_clip.startFrame + latest_clip.duration

        sequence_total_duration = latest_clip_endFrame - earliest_clip_startFrame
        setElem(sequence, 'duration', str(sequence_total_duration))
        """
        return 90000

    def xml_sequence_from(self, media_item, sequence_length):
        sequence = ET.Element('sequence')
        sequenceID = self._increment('sequenceID')
        clip.set('id', sequenceID )
        # Other sequence attributes here!

        duration = createElem(sequence, 'duration', str(sequence_length))
        name = createElem(sequence, 'name', self._increment('autoseqID'))

        # Now, begin to establish the format of the sequence
        # Take as many attributes as possible from the media_item we were given
        rate = xml_add_framerate(media_item.frameRate)
        sequence.append(rate)
        label = xml_add_label(DEFAULT_LABEL_COLOUR_SEQUENCE)
        sequence.append(label)

        timecode_tag = createElem(sequence, 'timecode')
        timecode_tag.append(rate)
        timecode_tag_string = createElem(timecode_tag, 'string', media_item.timecode)
        timecode_tag_frame = createElem(timecode_tag, 'frame', media_item.startFrame)
        timecode_tag_displayformat = createElem(timecode_tag, 'displayformat', DEFAULT_VIDEO_TIMECODE_DISPLAYFORMAT)


        media = createElem(sequence, 'media')
        video = createElem(media, 'video')
        video_format = createElem(video, 'format')
        video_format_samplecharx = createElem(video_format, 'samplecharacteristics')
        video_format_samplecharx.append(rate)
        codec = createElem(video_format_samplecharx, 'codec')
        codec_name = createElem(codec, 'name', media_item.codec_name)
        width = createElem(video_format_samplecharx, 'width', media_item.width)
        height = createElem(video_format_samplecharx, 'height', media_item.height)
        fielddominance = createElem(video_samplecharx, 'fielddominance', media_item.fielddominance)
        pixelaspectratio = createElem(video_format_samplecharx, 'pixelaspectratio', media_item.pixelaspectratio)
        anamorphic = createElem(video_format_samplecharx, 'anamorphic', media_item.anamorphic)
        colordepth = createElem(video_format_samplecharx, 'colordepth', DEFAULT_SEQUENCE_COLOURDEPTH)

        video_track = createElem(video, 'track')
        video_track_enabled = createElem(video_track, 'enabled', 'TRUE')
        video_track_locked = createElem(video_track, 'locked', 'FALSE')

        ## AUDIO HERE






media_items = { 'video': [], 'audio': [] }

for filepath in list_of_files:
    media_items = MediaItem(filepath)

    if media_item.mediaType == 'video':
        media_items['video'].append(media_item)

    elif media_item.mediaType == 'audio':
        media_items['audio'].append(media_item)

    else:
        continue

    # DEBUGGING: print metadata to stdout
    # print('STARTFRAME', media_item.startFrame, media_item.frameCount)
    # print(media_item.filename, media_item.frameRate, media_item.duration, media_item.timecode)

# Sort by start timecode (startFrame)
media_items['video'].sort()
media_items['audio'].sort()


build = BuildXML()

# To get the length, just give it all your media_items
autosequence_length = build.xml_autosequence_duration(media_items['video'])

for media_item in media_items['video']:

    clip = build.xml_masterclip_video(media_item)
    sequence = build.xml_sequence_from(media_item, autosequence_length)

    # DEBUGGER
    """
    for child in clip:
        print(media_item.name, child.tag, child.text)
        ET.dump(child)
        print(media_item.name, '^^^^^^')
    """

    ET.dump(clip)
