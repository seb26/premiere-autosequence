# premiere-autosequence
# Copyright (c) 2019 - Sebastian Reategui
# Available to use under MIT License.

import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from urllib.parse import quote

# APPLICATION ASSETS
import timecode
from lib_autosequence_defaults import *


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

def xml_add_link_reference(clipitemid, mediatype, trackindex, clipindex=1):
    link = ET.Element('link')
    linkclipref = createElem(link, 'linkclipref', clipitemid)
    mediatype = createElem(link, 'mediatype', mediatype)
    trackindex = createElem(link, 'trackindex', trackindex)
    clipindex = createElem(link, 'clipindex', clipindex)
    if mediatype == 'audio':
        # For some reason, audio items attract this attribute
        groupindex = createElem(link, 'groupindex', '1')
    return link


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
        print(self.filename, ': running ffprobe...')
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
                    self.pixelaspectratio = DEFAULT_VIDEO_ATTRIBUTES['pixelaspectratio']
                else:
                    # Otherwise stick the ratio there in it
                    self.pixelaspectratio = video_stream['sample_aspect_ratio']
            if 'field_order' in video_stream:
                if video_stream['field_order'] == 'progressive':
                    self.fielddominance = 'none' # Explicitly none
                else:
                    # This could potentially be problematic and not be the correct value.
                    # Whatever, I'm not forward thinking enough to facilitate interlaced media.
                    self.fielddominance = video_stream['field_order']
            else:
                self.fielddominance = DEFAULT_VIDEO_ATTRIBUTES['fielddominance']

            # Need to connect these to Ffprobe and be accurate
            self.alphatype = DEFAULT_VIDEO_ATTRIBUTES['alphatype']
            self.anamorphic = DEFAULT_VIDEO_ATTRIBUTES['anamorphic']


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
                self.timecode_displayformat = DEFAULT_VIDEO_TIMECODE_DISPLAYFORMAT

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

            # Rate, and also save this XML element for reuse later
            rate = xml_add_framerate(media_item.frameRate)
            clip.append(rate)
            media_item.frameRateTag = rate

            # To store <link> references
            if hasattr(media_item, 'link_references'):
                if len(media_item.link_references) > 0:
                    pass
                else:
                    media_item.link_references = []
            else:
                media_item.link_references = []

            # Create an umbrella group for media
            tag_media = createElem(clip, 'media')
            # Flag to determine if a <file> entry has already been declared
            FILE_TAG_DECLARED = False

            """
            # VIDEO CLIP-SPECIFIC
            """
            if media_item.mediaType == 'video':
                tag_video = createElem(tag_media, 'video')
                tag_video_track = createElem(tag_video, 'track')
                video_clipitem = createElem(tag_video_track, 'clipitem')
                video_clipitem_id = project.incrementID('clipitem')
                video_clipitem.set('id', video_clipitem_id)

                video_clipitem.append(masterclipid_tag)
                video_clipitem.append(name)
                video_clipitem.append(rate)
                # Quickly bash out elements for these three attributes
                for attrib in [ 'alphatype', 'pixelaspectratio', 'anamorphic' ]:
                    createElem(video_clipitem, attrib, getattr(media_item, attrib))

                # Define the <file> entry
                video_clipitem_file = createElem(video_clipitem, 'file')
                media_item.fileID = project.incrementID('file')
                FILE_TAG_DECLARED = True
                video_clipitem_file.set('id', media_item.fileID)
                video_clipitem_file.append(name)
                video_clipitem_file.append(rate)
                video_clipitem_file.append(duration)
                video_clipitem_file_pathurl = createElem(video_clipitem_file, 'pathurl', media_item.pathurl)

                # Create these but leave them empty
                video_clipitem_file_media = createElem(video_clipitem_file, 'media')
                video_clipitem_file_media_video = createElem(video_clipitem_file_media, 'video')

                # If there is embedded camera audio...
                # Store some audio information INSIDE THE <VIDEO> TRACK.
                if media_item.audio_channels > 0:
                    video_clipitem_file_media_audio = createElem(video_clipitem_file_media, 'audio')
                    tag_channelcount = createElem(video_clipitem_file_media_audio, 'channelcount', media_item.audio_channels)
                    # Add a <link> reference
                    video_clipitem_linkref = xml_add_link_reference(video_clipitem_id, 'video', '1')
                    media_item.link_references.append(video_clipitem_linkref)

            # Apply the following for ALL audio including camera embedded.
            if media_item.audio_channels > 0:
                tag_audio = createElem(tag_media, 'audio')

                if not FILE_TAG_DECLARED:
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
                        n_audio_channel = n + 1
                        audio_track_clipitem_file_media_audio = createElem(audio_track_clipitem_file_media, 'audio')
                        audio_track_clipitem_file_media_audio_channelcount = createElem(audio_track_clipitem_file_media_audio, 'channelcount', '1') # Mono assumption!
                        audio_track_clipitem_file_media_audio_audiochannel = createElem(audio_track_clipitem_file_media_audio, 'audiochannel')
                        audio_track_clipitem_file_media_audio_audiochannel_sourcechannel = createElem(audio_track_clipitem_file_media_audio_audiochannel, 'sourcechannel', n_audio_channel)

                # Apply the following steps FOR EACH CHANNEL OF AUDIO
                for n in range(media_item.audio_channels):
                    n_audio_channel = n + 1
                    audio_track = createElem(tag_audio, 'track')
                    audio_track_clipitem = createElem(audio_track, 'clipitem')
                    audio_track_clipitem.append(masterclipid_tag)
                    audio_track_clipitem.append(name)
                    audio_track_clipitem.append(rate)

                    audio_track_clipitem_id = project.incrementID('clipitem')
                    audio_track_clipitem.set('id', audio_track_clipitem_id)
                    audio_track_clipitem_linkref = xml_add_link_reference(audio_track_clipitem_id, 'audio', n_audio_channel)
                    media_item.link_references.append(audio_track_clipitem_linkref)

                    if not FILE_TAG_DECLARED:
                        # If we haven't yet declared a <file>...
                        if n == 1:
                            # And we are looping over the FIRST audio channel,
                            # THEN: Add in the <file> element we made above
                            audio_track_clipitem.append(audio_track_clipitem_file)
                        else:
                            # Thereafter, merely reference <file> using its ID as normal
                            audio_track_fileTag = createElem(audio_track, 'file')
                            audio_track_fileTag.set('id', media_item.fileID)
                    else:
                        # Merely reference <file> using its ID as normal
                        audio_track_fileTag = createElem(audio_track, 'file')
                        audio_track_fileTag.set('id', media_item.fileID)

                    audio_track_clipitem_sourcetrack = createElem(audio_track_clipitem, 'sourcetrack')
                    createElem(audio_track_clipitem_sourcetrack, 'mediatype', 'audio')
                    audio_track_clipitem_sourcetrack_trackindex = createElem(audio_track_clipitem_sourcetrack, 'trackindex', n_audio_channel)

            # Write all the link references to the XML item as well
            if media_item.mediaType == 'video':
                for item in media_item.link_references:
                    video_clipitem.append(item)

            if media_item.audio_channels > 0:
                all_audio_tracks = tag_audio.findall('track/clipitem')
                for track in all_audio_tracks:
                    for item in media_item.link_references:
                        track.append(item)

            # Finished. Save the master clip back to the media_item.
            media_item.masterclip = clip


class AutoSequence:
    def __init__(self, project, media_items, desired_sequence_name):
        """
        # Given a list of MediaItem objects
        # Create a <sequence>
        # With video format based on the first clip
        # With num of video tracks: 1
        # With num of audio tracks: per the highest audio track count (use max()) channeltype mono
        # With all clips appearing staggered on the timeline at their start timecode
        """

        if len(media_items) == 0:
            raise Exception('AutoSequence was called with no media_items. Check your items before calling it.')
            return

        """
        # DETERMINE AUTOSEQUENCE START, END, LENGTH & AUDIO CHANNELS
        """
        earliest_clip = min(media_items)
        latest_clip = max(media_items)

        autoseq_start = earliest_clip.startFrame
        autoseq_end = latest_clip.startFrame + latest_clip.duration
        autoseq_duration = autoseq_end - autoseq_start
        autoseq_framerate = earliest_clip.frameRate
        autoseq_framerate_tag = earliest_clip.masterclip.find('rate')
        autoseq_framerate_displayformat = earliest_clip.timecode_displayformat
        # DEBUG: print(autoseq_start, autoseq_end, autoseq_duration)

        # Create timecode (HH:MM:SS:FF) versions of the above values
        autoseq_timebase = timecode.Timecode(earliest_clip.frameRate)
        autoseq_start_tc = autoseq_timebase.toTC(autoseq_start)
        # DEBUG: print(autoseq_start_tc)

        # Check every clip's quantity of audio channels, and take the highest number
        # We will make *that* number of audio tracks total
        autoseq_audio_channels = max([ media_item.audio_channels for media_item in media_items ])

        """
        # DETERMINE <format> for video
        """
        autoseq_video_format = ET.Element('format')
        autoseq_video_format_samplecharx = createElem(autoseq_video_format, 'samplecharacteristics')
        autoseq_video_format_samplecharx.append(autoseq_framerate_tag)

        # Only attempt these attributes if media_item is a video
        # Otherwise they won't be defined
        if earliest_clip.mediaType == 'video':
            autoseq_video_format_samplecharx_codec = createElem(autoseq_video_format_samplecharx, 'codec')
            createElem(autoseq_video_format_samplecharx_codec, 'name', earliest_clip.codec_name)
            # Add these attributes quickly
            for attrib in [ 'width', 'height', 'anamorphic', 'pixelaspectratio', 'fielddominance' ]:
                createElem(autoseq_video_format_samplecharx, attrib, getattr(earliest_clip, attrib))
        else:
            # Default values for Audio
            for k, v in DEFAULT_VIDEO_ATTRIBUTES.items():
                createElem(autoseq_video_format_samplecharx, k, v)

        """
        # Create the sequence
        """
        sequence = ET.Element('sequence')
        sequence.set('id', project.incrementID('sequence'))

        # Add the default attributes
        # TODO: maybe edit the width and height? To actually match format of first clip
        for k, v in DEFAULT_SEQUENCE_ATTRIBUTES.items():
            sequence.set(k, v)

        sequence_name = createElem(sequence, 'name', desired_sequence_name)
        sequence.append(earliest_clip.frameRateTag)
        sequence_duration = createElem(sequence, 'duration', autoseq_duration)
        sequence_timecode_tag = createElem(sequence, 'timecode')
        sequence_timecode_tag.append(autoseq_framerate_tag)
        createElem(sequence_timecode_tag, 'frame', autoseq_start)
        createElem(sequence_timecode_tag, 'timecode', autoseq_start_tc)
        createElem(sequence_timecode_tag, 'displayformat', autoseq_framerate_displayformat)

        """
        # Establish some tracks
        """
        sequence_media = createElem(sequence, 'media')
        sequence_video_tag = createElem(sequence_media, 'video')
        # Add the video format we calculated earlier
        sequence_video_tag.append(autoseq_video_format)
        sequence_video_track = createElem(sequence_video_tag, 'track')
        for k, v in DEFAULT_SEQUENCE_AUDIO_TRACK_ATTRIBUTES.items():
            sequence_video_track.set(k, v)

        sequence_audio_tag = createElem(sequence_media, 'audio')
        sequence_audio_tracks = {}
        for n in range(autoseq_audio_channels):
            n_audio_channel = n + 1
            current_track = ET.Element('track')

            for k, v in DEFAULT_SEQUENCE_AUDIO_TRACK_ATTRIBUTES.items():
                current_track.set(k, v)

            # Save the track back to our map (sequence_audio_tracks)
            sequence_audio_tracks[n_audio_channel] = current_track

        # Used in <link><clipindex>
        sequence_clip_link_count = 1
        """
        # Iterate over media_items and:
        # - Create <clipitem>s
        # - Add them to the correct tracks
        """
        for media_item in media_items:


            masterclipid = media_item.masterclip.find('masterclipid')
            name = media_item.masterclip.find('name')
            duration = media_item.masterclip.find('duration')
            rate = media_item.masterclip.find('rate')
            file_tag = ET.Element('file')
            file_tag.set('id', media_item.fileID)

            # Clip start/end times MUST be offset by the autosequence's start time
            frame_start = media_item.startFrame - autoseq_start
            frame_end = frame_start + media_item.duration
            frame_in = 0
            frame_out = media_item.duration

            # Planned sequence data to be written
            # To be written ALTOGETHER AT THE END when the media_item is finished
            planned_sequence_video_track = []
            planned_sequence_audio_tracks = []

            # Local clip references
            # Local because they refer only to this media item
            local_link_references = []
            sequence_clip_link_count += 1

            if media_item.mediaType == 'video':
                clipitem_video = ET.Element('clipitem')
                clipitem_video_id = project.incrementID('clipitem')
                clipitem_video.set('id', clipitem_video_id)
                clipitem_video.append(masterclipid)
                clipitem_video.append(name)
                clipitem_video.append(duration)
                clipitem_video.append(file_tag)
                createElem(clipitem_video, 'enabled', 'TRUE')
                createElem(clipitem_video, 'alphatype', media_item.alphatype)

                createElem(clipitem_video, 'start', frame_start)
                createElem(clipitem_video, 'end', frame_end)
                createElem(clipitem_video, 'in', frame_in)
                createElem(clipitem_video, 'out', frame_out)

                # Quickly save a <link> reference
                clipitem_video_linkref = xml_add_link_reference(clipitem_video_id, 'video', '1', sequence_clip_link_count)
                local_link_references.append(clipitem_video_linkref)

                # Write the whole <clipitem> to the sequence directly
                planned_sequence_video_track.append(clipitem_video)

            # If the item contains ANY audio...
            if media_item.audio_channels > 0:
                # Create a new audio <clipitem> for every single audio channel
                for n in range(media_item.audio_channels):
                    n_audio_channel = n + 1

                    clipitem_audio = ET.Element('clipitem')
                    clipitem_audio_id = project.incrementID('clipitem')
                    clipitem_audio.set('id', clipitem_audio_id)
                    clipitem_audio.append(masterclipid)
                    clipitem_audio.append(name)
                    clipitem_audio.append(duration)
                    clipitem_audio.append(file_tag)
                    createElem(clipitem_audio, 'enabled', 'TRUE')

                    createElem(clipitem_audio, 'start', frame_start)
                    createElem(clipitem_audio, 'end', frame_end)
                    createElem(clipitem_audio, 'in', frame_in)
                    createElem(clipitem_audio, 'out', frame_out)

                    clipitem_audio_sourcetrack = createElem(clipitem_audio, 'sourcetrack')
                    createElem(clipitem_audio_sourcetrack, 'mediatype', 'audio')
                    createElem(clipitem_audio_sourcetrack, 'trackindex', n_audio_channel)

                    # Create link reference
                    clipitem_audio_linkref = xml_add_link_reference(clipitem_audio_id, 'audio', n_audio_channel, sequence_clip_link_count)
                    local_link_references.append(clipitem_audio_linkref)

                    # Plan to write it to the audio tracks
                    planned_sequence_audio_tracks.append( ( n_audio_channel, clipitem_audio) )

            # Recap the <link> references that we created throughout
            # Search through the "planned" video/audio tracks
            for item in local_link_references:
                if media_item.mediaType == 'video':
                    for clipitem_video in planned_sequence_video_track:
                        clipitem_video.append(item)

                if media_item.audio_channels > 0:
                    for n_audio_channel, clipitem_audio in planned_sequence_audio_tracks:
                        clipitem_audio.append(item)

            # Once finished, write these planned tracks to the sequence in the rest of the tree
            for clipitem_v in planned_sequence_video_track:
                sequence_video_track.append(clipitem_v)

            # Map audio channels to tracks
            for n_audio_channel, clipitem_a in planned_sequence_audio_tracks:
                sequence_audio_tracks[n_audio_channel].append(clipitem_a)

        # Write all audio tracks to the sequence
        for track_number in sorted(sequence_audio_tracks):
            sequence_audio_tag.append(sequence_audio_tracks[track_number])

        """
        # DEBUG: SHow me the contents of the audio tracks right now
        for k, v in sequence_audio_tracks.items():
            ET.dump(v)
        """

        # Save it to the object
        self.autosequence = sequence

    def generate(self):
        return self.autosequence


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
