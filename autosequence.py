# premiere-autosequence
# Copyright (c) 2019 - Sebastian Reategui
# Available to use under MIT License.

import os
import xml.etree.ElementTree as ET

# APPLICATION ASSETS
from lib_autosequence import *
import timecode


def main():
    TEMP_LIST_OF_FILES = [
        "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 2\\A002_06081938_C029.mov",
    ]
    TEMP_PROJECT_XML_DESTINATION = 'samples\\sample_out_5.xml'
    CREATE_SEPARATE_AUTOSEQUENCES = True

    media_items = []
    print('Media files given: ', len(TEMP_LIST_OF_FILES))
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

    masterclips_video = MasterClips(project, video_items)
    masterclips_audio = MasterClips(project, audio_items)

    for item in video_items:
        bin_masterclips_video.append(item.masterclip)
    for item in audio_items:
        bin_masterclips_audio.append(item.masterclip)


    """
    # Start to make AutoSequences
    """
    if CREATE_SEPARATE_AUTOSEQUENCES:
        # Haven't yet found a way to make a combined timeline with both video & audio

        if len(video_items) > 0:
            autosequence_video = AutoSequence(project, video_items, 'AutoSeq_V').generate()
            bin_sequences.append(autosequence_video)
        if len(audio_items) > 0:
            autosequence_audio = AutoSequence(project, audio_items, 'AutoSeq_A').generate()
            bin_sequences.append(autosequence_audio)

    project.generateProjectXML(TEMP_PROJECT_XML_DESTINATION)

if __name__ == "__main__":
    main()
