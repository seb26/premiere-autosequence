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
DEFAULT_AUDIO_BIT_DEPTH = 16
DEFAULT_AUDIO_CHANNELS = 2

DEFAULT_VIDEO_FRAME_RATE = 25
DEFAULT_VIDEO_TIMECODE_DISPLAYFORMAT = 'NDF'
TIMEBASE = timecode.Timecode(DEFAULT_VIDEO_FRAME_RATE)
VALID_FRAME_RATES = [ 23.976, 23.98, 24, 25, 29.97, 30 ]

DEFAULT_SEQUENCE_COLOURDEPTH = 24 # bit
DEFAULT_SEQUENCE_AUDIO_OUTPUT_CHANNELS = 2

DEFAULT_LABEL_COLOUR_VIDEO = 'Iris'
DEFAULT_LABEL_COLOUR_AUDIO = 'Caribbean'
DEFAULT_LABEL_COLOUR_SEQUENCE = 'Rose'
DEFAULT_LABEL_COLOUR_BIN = 'Mango'

DEFAULT_XMEML_VERSION = '4'

# PROTOTYPE FILE DATA
# TEMPORARY
TEMP_LIST_OF_FILES = [
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

TEMP_OUTPUT_XML_TO = 'samples\sample_out_4.xml'



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
                    self.startFrame = self._timebase.toFrames(found_timecode)
                    self.timecode_displayformat = DEFAULT_VIDEO_TIMECODE_DISPLAYFORMAT
                except ValueError:
                    # Well, it had something, but it didn't validate
                    print(self.filepath, ': this file doesn\'t have embedded timecode.')
                    self.startFrame = 0
                    self.timecode = '00:00:00:00'
                    self.timecode_displayformat = DEFAULT_VIDEO_TIMECODE_DISPLAYFORMAT
            else:
                # Couldn't find it.
                print(self.filepath, ': this file doesn\'t have embedded timecode.')
                self.startFrame = 0
                self.timecode = '00:00:00:00'
                self.timecode_displayformat = DEFAULT_VIDEO_TIMECODE_DISPLAYFORMAT

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
            self.audio_channels = audio_stream['channels']
            self.audio_bit_depth = audio_stream['bits_per_raw_sample']
        else:
            # Otherwise, be explicit
            self.audio_channels = 0

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

            else:
                # No timecode found at all
                self.startFrame = 0
                self.timecode = '00:00:00:00'
                self.timecode_displayformat = DEFAULT_VIDEO_TIMECODE_DISPLAYFORMAT

            # Audio duration is: File duration (seconds, float) * Video frame rate
            # e.g. 60 second recording * 25 FPS = 1,500 frames
            # Finish with int() because we always need a whole number of frames.
            self.duration = int( float(audio_stream['duration']) * self.frameRate )


    # Compare on the basis of start frame
    def __eq__(self, other):
        return self.startFrame == other.startFrame
    def __lt__(self, other):
        return self.startFrame < other.startFrame
    def __le__(self, other):
        return self.startFrame <= other.startFrame
    def __gt__(self, other):
        return self.startFrame > other.startFrame
    def __ge__(self, other):
        return self.startFrame >= other.startFrame



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
    # Refer explicitly to the DEFAULT_LABEL_COLOUR series of attributes if you want them.
    labels = ET.Element('labels')
    label2 = ET.SubElement(labels, 'label2')
    label2.text = colour
    return labels



class BuildXML:

    def __init__(self):

        # Collect a ID space, centralised
        self.index = {}
        for count in [ 'masterclip', 'clipitem', 'file', 'sequence', 'autoseq' ]:
            # Set all IDs to 0 to start with
            # First time they get used, they will be incremented to 1
            self.index[count] = 0

    def _incrementID(self, indexType):
        self.index[indexType] += 1
        return indexType + '-' + str(self.index[indexType])

    def xml_bin_create(self, text_label, colour=None):
        # Sets up a bin, when you give it a name, or optional colour (explicit)
        bin = ET.Element('bin')
        bin_name = createElem(bin, 'name', text_label)
        if colour:
            bin_label = xml_add_label(colour)
        else:
            bin_label = xml_add_label(DEFAULT_LABEL_COLOUR_BIN)
            bin.append(bin_label)

        bin_children = createElem(bin, 'children')
        return bin

    def xml_bin_add_item(self, bin, item):
        # Adds a given item to your bin, by putting it inside its <children> tag
        bin.find('children').append(item)
        return


    def xml_new_masterclip(self, media_item):
        clip = ET.Element('clip')
        duration = createElem(clip, 'duration', media_item.duration)
        ismasterclip = createElem(clip, 'ismasterclip', 'TRUE')
        name = createElem(clip, 'name', media_item.name)

        # Increment the masterclipID, and assign it back to the [media_item]
        # Add it to the id="" attribute
        # And describe it in text as <masterclipid>
        media_item.masterclipID = self._incrementID('masterclip')
        clip.set('id', media_item.masterclipID )
        masterclipid_tag = createElem(clip, 'masterclipid', media_item.masterclipID)
        clip.set('explodedTracks', 'true')

        label = xml_add_label(DEFAULT_LABEL_COLOUR_VIDEO)
        clip.append(label)

        rate = xml_add_framerate(media_item.frameRate)
        clip.append(rate)

        media = createElem(clip, 'media')

        ##
        ## VIDEO VERSUS AUDIO
        if media_item.mediaType == 'video':
            media_video = createElem(media, 'video')
            media_video_track = createElem(media_video, 'track')

            clipitem = createElem(media_video_track, 'clipitem')
            # Unlike masterclipID, clipitemID is never referenced outside of the masterclip
            # They are essentially single use
            # For every audio clip inside a master clip, please increment a new ID
            clipitem.set('id', self._incrementID('clipitem'))
            clipitem.append(masterclipid_tag)
            clipitem.append(rate)
            alphatype = createElem(clipitem, 'alphatype', media_item.alphatype)
            pixelaspectratio = createElem(clipitem, 'pixelaspectratio', media_item.pixelaspectratio)
            anamorphic = createElem(clipitem, 'anamorphic', media_item.anamorphic)

            file_tag = createElem(clipitem, 'file')
            # Increment the fileID, and assign it back to the [media_item]
            # Add it to the id="" attribute
            media_item.fileID = self._incrementID('file')
            file_tag.set('id', media_item.fileID )

            file_tag.append(name)
            file_tag.append(rate)
            file_tag.append(duration)
            pathurl = createElem(file_tag, 'pathurl', media_item.pathurl)

            # LEAVE the <media><video><audio> tags completely empty.
            file_tag_media = createElem(file_tag, 'media')
            file_tag_media_video = createElem(file_tag_media, 'video')

        elif media_item.mediaType == 'audio':
            media_audio = createElem(media, 'audio')
            media_audio_track = createElem(media_audio, 'track')

            clipitem = createElem(media_audio_track, 'clipitem')
            clipitem.set('id', self._incrementID('clipitem'))
            clipitem.append(masterclipid_tag)
            clipitem.append(rate)

            file_tag = createElem(clipitem, 'file')
            media_item.fileID = self._incrementID('file')
            file_tag.set('id', media_item.fileID )

            file_tag.append(name)
            file_tag.append(rate)
            file_tag.append(duration)
            pathurl = createElem(file_tag, 'pathurl', media_item.pathurl)

            file_tag_media = createElem(file_tag, 'media')

            # Create an <audio> tag inside <media> for every single audio channel
            # THIS SECTION
            # MAKES A GIANT ASSUMPTION THAT ALL CHANNELS 1:1 EQUAL TRACKS
            # I.E. EVERYTHING IS MONO AND SINGULAR AND STEREO DOESN'T EXIST
            for n in range(media_item.audio_channels):
                n_channel_index = n + 1

                file_tag_media_audio = createElem(file_tag_media, 'audio')
                samplecharx_channelcount = createElem(video_samplecharx, 'channelcount', '1')
                samplecharx_audiochannel = createElem(samplecharx_channelcount, 'audiochannel')
                samplecharx_sourcechannel = createElem(samplecharx_audiochannel, 'sourcechannel', n_channel_index)

                """
                # NOT USED AT THE MOMENT
                # Create a <link> reference for every audio channel which represents a separate clip, linked to each other
                for n in range(media_item.audio_channels):
                    n_trackindex = n + 1
                """

        return clip


    def _determineAutosequenceTiming(self):

        if len(self.media_items['video']) > 0 and len(self.media_items['audio']) == 0:
            search_items = media_items['video']
        # If there are audio clips, but no video
        if len(self.media_items['video']) == 0 and len(self.media_items['audio']) > 0:
            search_items = media_items['audio']
        # If there are both video and audio clips
        if len(self.media_items['video']) > 0 and len(self.media_items['audio']) > 0:
            search_items = self.media_items['video']
            search_items.append(self.media_items['audio'])
            search_items.sort()

        # FIND OUT Sequence length, and start timecode
        # Algorithm is:
        #       Find which is earliest, video or audio
        #       Find which is latest, video or audio
        #       Latest startTC + duration - Earliest startTC
        #       == Total sequence duration
        earliest_clip = search_items[0]
        # DEBUG: print('earliest', earliest_clip.name, earliest_clip.startFrame, earliest_clip.timecode)
        earliest_clip_startFrame = earliest_clip.startFrame
        latest_clip = search_items[-1]
        latest_clip_endFrame = latest_clip.startFrame + latest_clip.duration

        self.sequence_timecode_startFrame = earliest_clip.startFrame
        self.sequence_length = latest_clip_endFrame - earliest_clip_startFrame

        # FIND OUT Number of audio tracks to create
        # Grab all the numbers of tracks, and find the highest
        count_all_the_audio_tracks = [ item.audio_channels for item in search_items ]
        highest = max(count_all_the_audio_tracks)
        if highest < 1:
            # If there are basically no audio tracks at all (less than 1)
            # Still put in one audio track
            self.sequence_total_audio_tracks = 1
        else:
            self.sequence_total_audio_tracks = highest


    def _initiateSequence(self):
        sequence = ET.Element('sequence')
        sequenceID = self._incrementID('sequence')
        sequence.set('id', sequenceID )
        # Set some important attributes
        for k, v in preset_xml_default_sequence_attributes.items():
            sequence.set(k, v)

        duration = createElem(sequence, 'duration', str(self.sequence_length))
        name = createElem(sequence, 'name', self._incrementID('autoseq'))

        # Now, begin to establish the format of the sequence
        # Take as many attributes as possible from the media_item we were given
        # Shortcut: using media_item to reference the first clip
        media_item = self.media_items[0]
        rate = xml_add_framerate(media_item.frameRate)
        sequence.append(rate)
        label = xml_add_label(DEFAULT_LABEL_COLOUR_SEQUENCE)
        sequence.append(label)

        # By design, sequences created using this function will have the
        # start timecode of the first media_item
        timecode_tag = createElem(sequence, 'timecode')
        timecode_tag.append(rate)
        timecode_tag_string = createElem(timecode_tag, 'string', media_item.timecode)
        timecode_tag_frame = createElem(timecode_tag, 'frame', media_item.startFrame)
        timecode_tag_displayformat = createElem(timecode_tag, 'displayformat', media_item.timecode_displayformat)

        media = createElem(sequence, 'media')

        ## VIDEO
        ##
        video = createElem(media, 'video')
        video_format = createElem(video, 'format')
        video_format_samplecharx = createElem(video_format, 'samplecharacteristics')
        video_format_samplecharx.append(rate)
        codec = createElem(video_format_samplecharx, 'codec')
        codec_name = createElem(codec, 'name', media_item.codec_name)
        width = createElem(video_format_samplecharx, 'width', media_item.width)
        height = createElem(video_format_samplecharx, 'height', media_item.height)
        fielddominance = createElem(video_format_samplecharx, 'fielddominance', media_item.fielddominance)
        pixelaspectratio = createElem(video_format_samplecharx, 'pixelaspectratio', media_item.pixelaspectratio)
        anamorphic = createElem(video_format_samplecharx, 'anamorphic', media_item.anamorphic)
        colordepth = createElem(video_format_samplecharx, 'colordepth', DEFAULT_SEQUENCE_COLOURDEPTH)

        video_track = createElem(video, 'track')
        video_track_enabled = createElem(video_track, 'enabled', 'TRUE')
        video_track_locked = createElem(video_track, 'locked', 'FALSE')
        # Set attributes
        for k, v in preset_xml_default_sequence_video_track_attributes.items():
            video_track.set(k, v)

        ## AUDIO
        ##
        audio = createElem(media, 'audio')

        # Generate the correct number of audio tracks
        audio_track_index = 0
        for n in range(self.sequence_total_audio_tracks):
            audio_track_index += 1
            audio_track = createElem(audio, 'track')
            audio_track_enabled = createElem(audio_track, 'enabled', 'TRUE')
            audio_track_locked = createElem(audio_track, 'locked', 'FALSE')
            # Set attributes
            for k, v in preset_xml_default_sequence_audio_track_attributes.items():
                audio_track.set(k, v)

        self.sequence = sequence
        return

    def _fillSequence(self):

        # Start work on a sequence
        sequence_track_video = self.sequence.find('media').find('video').find('track')

        # Add them to the sequence
        for media_item in media_items['video']:
            # Determine the clip's position on the timeline
            clipitem_start_at = media_item.startFrame - self.sequence_timecode_startFrame
            clipitem_end_at = clipitem_start_at + media_item.duration
            # Generate a clip
            clipitem = ET.Element('clipitem')
            clipitem.set('id', self._incrementID('clipitem'))
            masterclipid_tag = createElem(clipitem, 'masterclipid', media_item.masterclipID)
            name = createElem(clipitem, 'name', media_item.name)
            enabled = createElem(clipitem, 'enabled', 'TRUE')
            duration = createElem(clipitem, 'duration', media_item.duration)
            rate = xml_add_framerate(media_item.frameRate)
            file = createElem(clipitem, 'file')
            file.set('id', media_item.fileID)
            label = xml_add_label(DEFAULT_LABEL_COLOUR_VIDEO)
            clipitem.append(label)

            alphatype = createElem(clipitem, 'alphatype', media_item.alphatype)

            # Clip timeline position is defined in the parameters
            # Clip source TC is 0 and duration, to run the clip for its full duration
            clipitem_in_at = '0'
            clipitem_out_at = media_item.duration
            # TODO: Consider how CLASHES occur and what to do to prevent
            tag_start = createElem(clipitem, 'start', clipitem_start_at)
            tag_end = createElem(clipitem, 'end', clipitem_end_at)
            tag_in = createElem(clipitem, 'in', clipitem_in_at)
            tag_out = createElem(clipitem, 'out', clipitem_out_at)

            #
            # Add it to the video track
            sequence_track_video.append(sequence_clip)

                def xml_autoseq_audio_generate_clipitems(self, media_items, clipitem_start_at, clipitem_end_at, sequence):

                    sequence_audio_tracks = sequence.find('media').find('audio')
                    # Make a list of all audio tracks, and then access them specifically via [#] index
                    sequence_specific_audio_track = [ track for track in sequence_audio_tracks ]

                    # For every audio masterclip
        for media_item in media_items['audio']:

            # For every audio channel in that masterclip
            for n in range(media_item.audio_channels):
                n_audio_channel_index += 1

                clipitem = ET.Element('clipitem')
                clipitem.set('id', self._incrementID('clipitem'))
                masterclipid_tag = createElem(clipitem, 'masterclipid', media_item.masterclipID)
                name = createElem(clipitem, 'name', media_item.name)
                enabled = createElem(clipitem, 'enabled', 'TRUE')
                duration = createElem(clipitem, 'duration', media_item.duration)
                rate = xml_add_framerate(media_item.frameRate)
                file = createElem(clipitem, 'file')
                file.set('id', media_item.fileID)
                label = xml_add_label(DEFAULT_LABEL_COLOUR_VIDEO)
                clipitem.append(label)

                # Clip timeline position is defined in the parameters
                # Clip source TC is 0 and duration, to run the clip for its full duration
                clipitem_in_at = '0'
                clipitem_out_at = media_item.duration
                # TODO: Consider how CLASHES occur and what to do to prevent
                tag_start = createElem(clipitem, 'start', clipitem_start_at)
                tag_end = createElem(clipitem, 'end', clipitem_end_at)
                tag_in = createElem(clipitem, 'in', clipitem_in_at)
                tag_out = createElem(clipitem, 'out', clipitem_out_at)

                # Limitation: Everything is mono
                clipitem.set('premiereChannelType', 'mono')
                tag_sourcetrack = createElem(clipitem, 'sourcetrack')
                tag_sourcetrack_mediatype = createElem(tag_sourcetrack, 'mediatype', 'audio')
                tag_sourcetrack_trackindex = createElem(tag_sourcetrack, 'trackindex', n_audio_channel_index)

                # Add the clipitem to the correct track
                # Minus 1 because the List of audio tracks is Zero-indexed
                sequence_specific_audio_track[n_audio_channel_index - 1].append(clipitem)

                return

    def buildAutoSequence(self, sequence_name, mediaType='video'):
        # TODO: write its name
        # assign it an ID
        self._initiateSequence()

        if mediaType == 'video':
            self._fillSequence()
        return self.sequence

media_items = { 'video': [], 'audio': [] }

for filepath in TEMP_LIST_OF_FILES:
    media_item = MediaItem(filepath)

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




##
## BUILD XML
##
build = BuildXML()

# Create a bin for master clips
bin_for_master_clips = build.xml_bin_create('AutoSeq_MasterClips')
# Then create the master clips
for media_item in media_items['video']:
    clip = build.xml_masterclip_video(media_item)
    build.xml_bin_add_item(bin_for_master_clips, clip)

# Initiate an Autosequence generator
# Using *all* media_items
autosequence = BuildAutosequence(media_items)
# Build an Autosequence for *all* media_items gathered
sequence_V = build.buildAutosequence('AutoSeq_Sequence_V', 'video')
sequence_A = build.buildAutosequence('AutoSeq_Sequence_A', 'audio')

# Add it to a bin
bin_for_sequence = build.xml_bin_create('AutoSeq_Sequence1')
bin_for_sequence.find('children').append(sequence_V, sequence_A)

# Define what will go into the XML document
xmeml_document = ET.Element('xmeml')
xmeml_document.set('version', DEFAULT_XMEML_VERSION)
project = createElem(xmeml_document, 'project')
project_name = createElem(project, 'name', 'AutoSeq_Project')
project_items = createElem(project, 'children')
# Add the bins!
project_items.append(bin_for_master_clips)
project_items.append(bin_for_sequence)

tree = ET.ElementTree(xmeml_document)
tree.write(TEMP_OUTPUT_XML_TO, encoding='UTF-8', xml_declaration=True)

"""
# DEBUGGER
for child in sequence_clip:
    print(child.tag, child.text)
    ET.dump(child)
    print(child.tag, '^^^^^^')
"""
