import os


# Defaults


# Functions
def createElem():
    pass

# def xml_add_framerate
# def xml_add_label


class MediaFile:
    def __init__(self, filepath):

        # Run ffprobe
        # JSON it
        # Gather relevant metadata and save it as self.attributes
        # Return MediaFile object
        pass


class MasterClips:
    def __init__(self, media_items):
        # Given a list of MediaFile objects...

        # Create a <clip> Element for a Masterclip
        # Add all relevant metadata
        # Add video-specific and audio-specific metadata
        # Store them temporarily as self._master_clips
        pass

    def generate(self):
        return self._master_clips
        # Return ET Element <clip id="masterclip-#">
        # Return all as a list

        # Take all media items in, and return all media items out
        # Do not split video and audio separately
        pass


class AutoSequence:
    def __init__(self, media_items):
        # Given a list of MediaFile objects

        # Create a <sequence>
        # Establish the video format based on the first clip
        # Num of video tracks: 1
        # Num of audio tracks: per the highest audio track count (use max()) channeltype mono

        # Get timecode_startFrame of all clips, get earliest start (use min())
        # Establish desired duration (endFrame + duration - startFrame)
        pass

    def generate(self, sequence_name):
        # add the name
        return self._autosequence


class Project:
    def __init__(self, project_name):
        self.project = ET.Element('project')
        # add name
        # add root bin, self.root
        pass

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

    def generateProjectXML(self):
        tree = ET.ElementTree(self.project)
        # Write the tree somewhere!
        # Make sure to include <xmeml version="4">, DOCTYPE and UTF-8



# -----

def main():
    TEMP_LIST_OF_FILES = []
    CREATE_SEPARATE_AUTOSEQUENCES = True

    media_items = []
    for filepath in TEMP_LIST_OF_FILES:
        media_item = MediaItem(filepath)
        media_items.append(media_item)

    project = Project('AutoSeq_V1')
    bin_masterclips_video = project.create_bin('Masterclips_Video')
    bin_masterclips_audio = project.create_bin('Masterclips_Audio')
    bin_sequences = project.create_bin('Sequences')

    if CREATE_SEPARATE_AUTOSEQUENCES:
        video_items = [ item for item in media_items if item.mediaType == 'video' ]
        audio_items = [ item for item in media_items if item.mediaType == 'audio' ]
        target_items = set(video_items, audio_items)

    else:
        target_items = set(media_items)

    n_sequence = 0
    for group_of_media_items in target_items:
        n_sequence += 1
        autosequence = AutoSequence(group_of_media_items).generate('AutoSeq_' + str(n_sequence))
        # Add it to a bin
        bin_sequences.append(autosequence)

    project.generateProjectXML()

if __name__ == "__main__":
    main()
