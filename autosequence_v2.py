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
        # Add video-specific and audio-specific metadata
        # Store them temporarily as self._master_clips
        """

        self._master_clips = []

        for media_item in media_items:

            clip = ET.Element('clip')
            clip.set('explodedTracks', 'true')
            duration = createElem(clip, 'duration', media_item.duration)
            ismasterclip = createElem(clip, 'ismasterclip', 'TRUE')
            name = createElem(clip, 'name', media_item.name)

            # Increment the masterclipID, and assign it back to the [media_item]
            # Add it to the id="" attribute
            # And describe it in text as <masterclipid>
            media_item.masterclipID = project.incrementID('masterclip')
            clip.set('id', media_item.masterclipID )
            masterclipid_tag = createElem(clip, 'masterclipid', media_item.masterclipID)

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
                clipitem.set('id', project.incrementID('clipitem'))
                clipitem.append(masterclipid_tag)
                clipitem.append(rate)
                alphatype = createElem(clipitem, 'alphatype', media_item.alphatype)
                pixelaspectratio = createElem(clipitem, 'pixelaspectratio', media_item.pixelaspectratio)
                anamorphic = createElem(clipitem, 'anamorphic', media_item.anamorphic)

                file_tag = createElem(clipitem, 'file')
                # Increment the fileID, and assign it back to the [media_item]
                # Add it to the id="" attribute
                media_item.fileID = project.incrementID('file')
                file_tag.set('id', media_item.fileID )

                file_tag.append(name)
                file_tag.append(rate)
                file_tag.append(duration)
                pathurl = createElem(file_tag, 'pathurl', media_item.pathurl)

                # Create the <media><video> tags
                # But, leave them empty
                file_tag_media = createElem(file_tag, 'media')
                file_tag_media_video = createElem(file_tag_media, 'video')
                file_tag_media_audio = createElem(file_tag_media, 'audio')
                file_tag_media_audio2 = createElem(file_tag_media, 'audio')

            elif media_item.mediaType == 'audio':


                media_audio = createElem(media, 'audio')
                media_audio_track = createElem(media_audio, 'track')

                clipitem = createElem(media_audio_track, 'clipitem')
                clipitem.set('id', project.incrementID('clipitem'))
                clipitem.append(masterclipid_tag)
                clipitem.append(rate)

                file_tag = createElem(clipitem, 'file')
                media_item.fileID = project.incrementID('file')
                file_tag.set('id', media_item.fileID )

                file_tag.append(name)
                file_tag.append(rate)
                pathurl = createElem(file_tag, 'pathurl', media_item.pathurl)

                file_tag_media = createElem(file_tag, 'media')

            """
            # Create an <audio> tag inside <media> for every single audio channel
            # Applies for both video and audio master clips.
            # THIS SECTION
            # MAKES A GIANT ASSUMPTION THAT ALL CHANNELS 1:1 EQUAL TRACKS
            # I.E. EVERYTHING IS MONO AND SINGULAR AND STEREO DOESN'T EXIST
            for n in range(media_item.audio_channels):
                n_channel_index = n + 1

                file_tag_media_audio = createElem(file_tag_media, 'audio')
                tag_channelcount = createElem(file_tag_media_audio, 'channelcount', '1')
                tag_audiochannel = createElem(file_tag_media_audio, 'audiochannel')
                tag_sourcechannel = createElem(tag_audiochannel, 'sourcechannel', n_channel_index)
            """
            """
            # NOT USED AT THE MOMENT
            # Create a <link> reference for every audio channel which represents a separate clip, linked to each other
            for n in range(media_item.audio_channels):
                n_trackindex = n + 1
            """

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
        self.root = createElem(tag_project_root_bin, 'children')
        tag_project_name = createElem(tag_project_root_bin, 'name', project_name)

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

    """ necessary?
    def add_item_to_bin(self, item, bin):
        # Find the bin by name, then go above to its parent and then down to children)
        target = self.root.findall('./bin/name/' + bin + '/../children')
        target.append(item)
        return True
    """

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

        """ Write to stdout
        # ET.dump(tree)
        """


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
