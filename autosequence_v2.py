import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from urllib.parse import quote

# APPLICATION ASSETS
import timecode
from autosequence_v2_defaults import *


"""
# Independent functions
# Mainly as shortcuts for tedious XML operations
"""
def createElem(parent, tag, value=''):
    # Creates a subelement of your parent
    # Set its text value to something, or empty if unspecified
    # ****NOTE***: CONVERTS TO STRING
    # And then gives this subelement back to you to use
    t = ET.SubElement(parent, tag)
    t.text = str(value)
    return t

def xml_add_framerate(frameRate, ntsc=DEFAULT_FRAME_RATE_NTSC):
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




class MediaItem:
    def __init__(self, filepath):
        """
        # Run ffprobe
        # JSON it
        # Gather relevant metadata and save it as self.attributes
        # Return MediaFile object
        """

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

        # Quickly access the number of streams
        self.videoStreams = len(video_streams)
        self.audioStreams = len(audio_streams)

        """
        # VIDEO: Gather metadata
        """
        if self.mediaType == 'video':
            # Work with only the first video stream, if multiple
            video_stream = video_streams[0]

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
                    self.startTC = found_timecode
                    self.startFrame = self._timebase.toFrames(found_timecode)
                    self.timecode_displayformat = DEFAULT_VIDEO_TIMECODE_DISPLAYFORMAT
                except ValueError:
                    # Well, it had something, but it didn't validate
                    print(self.filepath, ': this file doesn\'t have embedded timecode.')
                    self.startFrame = 0
                    self.startTC = '00:00:00:00'
                    self.timecode_displayformat = DEFAULT_VIDEO_TIMECODE_DISPLAYFORMAT
            else:
                # Couldn't find it.
                print(self.filepath, ': this file doesn\'t have embedded timecode.')
                self.startFrame = 0
                self.startTC = '00:00:00:00'
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


        """
        # AUDIO: Gather data on any audio, video or not
        """
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


        """
        # AUDIO: Gather data specifically on audio-only media
        """
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
                self.startTC = self._timebase.toTC(self.startFrame)

            else:
                # No timecode found at all
                self.startFrame = 0
                self.startTC = '00:00:00:00'
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


class MasterClips:
    def __init__(self, project, media_items):
        """
        # Given a list of MediaFile objects...

        # Create a <clip> Element for a Masterclip
        # Give it a MasterclipID and save this back to the item
        # Add all relevant metadata
        # Add video-specific metadata
        # For every audio channel (regardless of Video or Audio clip), create appropriate tracks

        # Store the master clip as a list under self._master_clips
        """

        self._master_clips = []

        for media_item in media_items:
            clip = ET.Element('clip')
            clip.set('explodedTracks', 'true')

            # Increment the masterclipID, and assign it back to the [media_item]
            # Add it to the id="" attribute
            # And describe it in text as <masterclipid>
            media_item.masterclipID = project.incrementID('masterclip')
            clip.set('id', media_item.masterclipID )
            masterclipid_tag = createElem(clip, 'masterclipid', media_item.masterclipID)

            # Other initial attributes
            duration = createElem(clip, 'duration', media_item.duration)
            ismasterclip = createElem(clip, 'ismasterclip', 'TRUE')
            name = createElem(clip, 'name', media_item.name)
            rate = xml_add_framerate(media_item.frameRate)
            clip.append(rate)

            tag_media = createElem(clip, 'media')

            """
            # VIDEO CLIP-SPECIFIC
            """
            if media_item.mediaType == 'video':
                tag_video = createElem(tag_media, 'video')
                tag_video_track = createElem(tag_video, 'track')
                video_clipitem = createElem(tag_video_track, 'clipitem')
                video_clipitem.set('id', project.incrementID('clipitem'))

                video_clipitem.append(masterclipid_tag)
                video_clipitem.append(name)
                video_clipitem.append(rate)
                # Quickly bash out elements for these three attributes
                for attrib in [ 'alphatype', 'pixelaspectratio', 'anamorphic' ]:
                    createElem(video_clipitem, attrib, getattr(media_item, attrib))

                # Define the <file> entry
                video_clipitem_file = createElem(video_clipitem, 'file')
                media_item.fileID = project.incrementID('file')
                video_clipitem_file.set('id', media_item.fileID)
                video_clipitem_file.append(name)
                video_clipitem_file.append(rate)
                video_clipitem_file.append(duration)
                video_clipitem_file_pathurl = createElem(video_clipitem_file, 'pathurl', media_item.pathurl)

                # Create these but leave them empty
                video_clipitem_file_media = createElem(video_clipitem_file, 'media')
                video_clipitem_file_media_video = createElem(video_clipitem_file_media, 'video')

                # If there is embedded camera audio...
                if media_item.audio_channels > 0:
                    video_clipitem_file_media_audio = createElem(video_clipitem_file_media, 'audio')
                    tag_channelcount = createElem(video_clipitem_file_media_audio, 'channelcount', media_item.audio_channels)

                # Also create <audio><track>s
                tag_audio = createElem(tag_media, 'audio')

                n_index_audio_channel = 0
                for n in range(media_item.audio_channels):
                    n_index_audio_channel += 1
                    tag_audio_track = createElem(tag_audio, 'track')
                    tag_audio_track.set('id', project.incrementID('clipitem'))
                    tag_audio_track.append(masterclipid_tag)
                    tag_audio_track.append(name)
                    tag_audio_track.append(rate)
                    tag_audio_track_file = createElem(tag_audio_track, 'file')
                    tag_audio_track_file.set('id', media_item.fileID)

                    tag_audio_track_sourcetrack = createElem(tag_audio_track, 'sourcetrack')
                    tag_audio_track_sourcetrack_mediatype = createElem(tag_audio_track_sourcetrack, 'mediatype', 'audio')
                    tag_audio_track_sourcetrack_trackindex = createElem(tag_audio_track_sourcetrack, 'trackindex', n_index_audio_channel)



            elif media_item.mediaType == 'audio':
                tag_audio = createElem(tag_media, 'audio')

                # Pre-create the <file> item
                # Soon, it will be attached to the very first track of audio
                audio_track_clipitem_file = ET.Element('file')
                media_item.fileID = project.incrementID('file')
                audio_track_clipitem_file.set('id', media_item.fileID)
                audio_track_clipitem_file_pathurl = createElem(audio_track_clipitem_file, 'pathurl', media_item.pathurl)
                audio_track_clipitem_file.append(name)
                audio_track_clipitem_file.append(rate)
                audio_track_clipitem_file.append(duration)
                audio_track_clipitem_file_media = createElem(audio_track_clipitem_file, 'media')

                for n in range(media_item.audio_channels):
                    audio_track_clipitem_file_media_audio = createElem(audio_track_clipitem_file_media, 'audio')
                    audio_track_clipitem_file_media_audio_channelcount = createElem(audio_track_clipitem_file_media_audio, 'channelcount', '1') # Mono assumption!
                    audio_track_clipitem_file_media_audio_audiochannel = createElem(audio_track_clipitem_file_media_audio, 'audiochannel')
                    audio_track_clipitem_file_media_audio_audiochannel_sourcechannel = createElem(audio_track_clipitem_file_media_audio_audiochannel, 'sourcechannel', n + 1)

                # Apply the following steps FOR EACH CHANNEL OF AUDIO
                for n in range(media_item.audio_channels):
                    audio_track = createElem(tag_audio, 'track')
                    audio_track_clipitem = createElem(audio_track, 'clipitem')
                    audio_track_clipitem.set('id', project.incrementID('clipitem'))
                    audio_track_clipitem.append(masterclipid_tag)
                    audio_track_clipitem.append(name)
                    audio_track_clipitem.append(rate)

                    if n == 0:
                        # If it's the first audio track
                        # Add in the <file> element we made above
                        audio_track_clipitem.append(audio_track_clipitem_file)
                    else:
                        # Thereafter, merely reference <file> using its ID as normal
                        audio_track_fileTag = createElem(audio_track, 'file')
                        audio_track_fileTag.set('id', media_item.fileID)

                    audio_track_clipitem_sourcetrack = createElem(audio_track_clipitem, 'sourcetrack')
                    createElem(audio_track_clipitem_sourcetrack, 'mediatype', 'audio')
                    audio_track_clipitem_sourcetrack_trackindex = createElem(audio_track_clipitem_sourcetrack, 'trackindex', n + 1)

            # Finished. Save the master clip to the object.
            self._master_clips.append(clip)


    def generate(self):
        return self._master_clips

        # Take all media items in, and return all media items out
        # Do not split video and audio separately (at least inside here)
        pass


class AutoSequence:
    def __init__(self, media_items):
        # Given a list of MediaItem objects

        # Create a <sequence>
        # Establish the video format based on the first clip
        # Num of video tracks: 1
        # Num of audio tracks: per the highest audio track count (use max()) channeltype mono

        # Get timecode_startFrame of all clips, get earliest start (use min())
        # Establish desired duration (endFrame + duration - startFrame)
        self._autosequence = ET.Element('autosequence_goes_here')
        pass

    def generate(self, sequence_name):
        # add the name
        return self._autosequence


class Project:
    def __init__(self, project_name):
        self.project = ET.Element('project')

        tag_project_root_bin = createElem(self.project, 'bin')
        tag_project_name = createElem(tag_project_root_bin, 'name', project_name)
        self.root = createElem(tag_project_root_bin, 'children')

        """Centralised place for IDs"""
        self.index = {}
        for index_type in [ 'masterclip', 'clipitem', 'file', 'sequence' ]:
            # Set all IDs to 0 to start with
            # First time they get used, they will be incremented to 1
            self.index[index_type] = 0
        return

    def create_bin(self, bin_name):
        bin = createElem(self.root, 'bin')
        bin_name = createElem(bin, 'name', bin_name)
        bin_children = createElem(bin, 'children')
        return bin_children

    def incrementID(self, index_type):
        self.index[index_type] += 1
        return index_type + '-' + str(self.index[index_type])

    def generateProjectXML(self, output_file):
        self.xmeml_document = ET.Element('xmeml')
        self.xmeml_document.set('version', DEFAULT_XMEML_VERSION)
        self.xmeml_document.append(self.project)

        tree = ET.ElementTree(self.xmeml_document)
        tree.write(output_file, encoding='UTF-8', xml_declaration=True)
        # TODO: Make sure to include <xmeml version="4">, DOCTYPE and UTF-8


# -----


def main():
    TEMP_LIST_OF_FILES = [
        "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071243_C005.mov",
        "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071220_C001.mov",
        "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071221_C002.mov",
        "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071223_C003.mov",
        "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071229_C004.mov",
        "S:\\Projects\\HAZEN_ALPHA\\AUDIO\\F8_SD2\\130619\\130619_005.WAV",
        "S:\\Projects\\HAZEN_ALPHA\\AUDIO\\F8_SD2\\130619\\130619_001.WAV",
        "S:\\Projects\\HAZEN_ALPHA\\AUDIO\\F8_SD2\\130619\\130619_002.WAV",
        "S:\\Projects\\HAZEN_ALPHA\\AUDIO\\F8_SD2\\130619\\130619_003.WAV",
        "S:\\Projects\\HAZEN_ALPHA\\AUDIO\\F8_SD2\\130619\\130619_004.WAV",
    ]
    TEMP_PROJECT_XML_DESTINATION = 'samples\\sample_out_5.xml'
    CREATE_SEPARATE_AUTOSEQUENCES = True

    media_items = []
    for filepath in TEMP_LIST_OF_FILES:
        media_item = MediaItem(filepath)
        media_items.append(media_item)

    """
    # Sort by startFrame
    """
    media_items.sort()


    project = Project('AutoSeq_V1')
    bin_masterclips_video = project.create_bin('Masterclips_Video')
    bin_masterclips_audio = project.create_bin('Masterclips_Audio')
    bin_sequences = project.create_bin('Sequences')

    """
    # Create <master clips>
    """
    video_items = [ item for item in media_items if item.mediaType == 'video' ]
    audio_items = [ item for item in media_items if item.mediaType == 'audio' ]

    masterclips_video = MasterClips(project, video_items).generate()
    masterclips_audio = MasterClips(project, audio_items).generate()


    for item in masterclips_video:
        bin_masterclips_video.append(item)
    for item in masterclips_audio:
        bin_masterclips_audio.append(item)


    """
    # Start to make AutoSequences
    """
    if CREATE_SEPARATE_AUTOSEQUENCES:
        # Haven't yet found a way to make a combined timeline with both video & audio

        autosequence_video = AutoSequence(video_items).generate('AutoSeq_V')
        autosequence_audio = AutoSequence(audio_items).generate('AutoSeq_A')
        bin_sequences.append(autosequence_video)
        bin_sequences.append(autosequence_audio)

    project.generateProjectXML(TEMP_PROJECT_XML_DESTINATION)

if __name__ == "__main__":
    main()
