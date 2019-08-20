import xml.etree.ElementTree as ET
import os


# TEMP DURING TESTING
import timecode

list_of_files = [

    { 'filepath': "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071220_C001.mov", 'framerate': 25, 'startTC': '12:20:13:00', 'startFrame': 1110325, 'duration': 923 },
    { 'filepath': "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071221_C002.mov", 'framerate': 25, 'startTC': '12:21:30:01', 'startFrame': 1112251, 'duration': 918 },
    { 'filepath': "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071223_C003.mov", 'framerate': 25, 'startTC': '12:23:25:20', 'startFrame': 1115145, 'duration': 1798 },
    { 'filepath': "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071229_C004.mov", 'framerate': 25, 'startTC': '12:29:23:13', 'startFrame': 1124088, 'duration': 2873 },
    { 'filepath': "Q:\\Projects\\HAZEN_ALPHA\\MEDIA_OCM\\DAY 1\\A001_06071243_C005.mov", 'framerate': 25, 'startTC': '12:43:47:10', 'startFrame': 1145685, 'duration': 601 },
]

pr_xml_base_structure = """
<bin>
    <name>AUTOSEQUENCE_1</name>
    <labels>
        <label2>Mango</label2>
    </labels>
    <children>
        <bin>
            <name>AUTOSEQUENCE_1_MASTER_CLIPS</name>
            <labels>
                <label2>Mango</label2>
            </labels>
            <children>
            </children>
        </bin>
        <sequence>
            <duration />
            <rate>
                <timebase />
                <ntsc>FALSE</ntsc>
            </rate>
            <name />
            <timecode>
                <rate>
                    <timebase />
                    <ntsc>FALSE</ntsc>
                </rate>
                <frame />
                <displayformat />
            </timecode>
            <media>
                <video>
                    <format />
                    <track />
                </video>
                <audio>
                    <track />
                </audio>
            </media>
        </sequence>
    </children>
</bin>
"""

pr_xml_video_masterclip = """
<clip>
    <masterclipid />
    <ismasterclip>TRUE</ismasterclip>
    <duration />
    <rate>
        <timebase />
        <ntsc>FALSE</ntsc>
    </rate>
    <in />
    <out />
    <name />
    <media>
        <video>
            <track>
                <clipitem>
                    <masterclipid />
                    <name />
                    <rate>
                        <timebase />
                        <ntsc>FALSE</ntsc>
                    </rate>
                    <alphatype />
                    <pixelaspectratio />
                    <anamorphic />
                    <file>
                        <name />
                        <pathurl />
                        <rate>
                            <timebase />
                            <ntsc>FALSE</ntsc>
                        </rate>
                        <media>
                            <video />
                            <audio />
                        </media>
                    </file>
                </clipitem>
            </track>
        </video>
    </media>
</clip>
"""

pr_xml_video_clip_on_timeline = """
<clipitem>
    <masterclipid />
    <name />
    <enabled>TRUE</enabled>
    <duration />
    <rate>
        <timebase />
        <ntsc>FALSE</ntsc>
    </rate>
    <start />
    <end />
    <in />
    <out />
    <alphatype />
    <file />
    <logginginfo>
        <description />
        <scene />
        <shottake />
        <lognote />
    </logginginfo>
    <labels>
        <label2>Iris</label2>
    </labels>
</clipitem>
"""

def setElem(target, element, value):
    """Given an element (1. target),
    quickly add an <element> to it (2. element),
    and then set its text contents (3. value).

    Returns the element at the end, if you need it"""
    e = target.find(element)
    e.text = value
    return e

# Create a parsable XML from the structure written above
tree = ET.ElementTree( ET.fromstring(pr_xml_base_structure) )
root = tree.getroot()

top_level = root.find('children')
bin_master_clips = top_level.find('bin').find('children')
sequence = top_level.find('sequence')

index = 0

# Get the duration of the entire intended sequence
# First, sort by timecode
# Then the duration is:
#       last_timecode + last_duration - first_timecode
files_sorted_by_startFrame = sorted(list_of_files, key=lambda k: k['startFrame'])
file_first = files_sorted_by_startFrame[0]
file_last = files_sorted_by_startFrame[-1]
sequence_total_duration = file_last['startFrame'] + file_last['duration'] - file_first['startFrame']

# Quickly set up the sequence
sequence.set('id', 'AUTOSEQUENCE_SEQUENCE_1')
setElem(sequence, 'duration', str(sequence_total_duration))
# FRAMERATE..................

for media in list_of_files:

    # TEMP ATTRIBUTES DURING TESTING
    filename = os.path.basename(media['filepath'])
    filepath = media['filepath']
    framerate = media['framerate']
    startTC = media['startTC']
    duration = media['duration']
    startFrame = timecode.Timecode(framerate).toFrames(startTC)

    print(startFrame)

    index += 1
    masterID = str(index) + '_' + filename
    masterID_component = masterID + '_COMPONENT_1'

    # Create a new master clip, blank from the template
    master_clip_root = ET.fromstring(pr_xml_video_masterclip)

    # Set its name and other attributes
    setElem(master_clip_root, 'name', filename)
    setElem(master_clip_root, 'masterclipid', masterID)
    master_clip_root.set('id', masterID)
    setElem(master_clip_root.find('rate'), 'timebase', str(framerate))
    setElem(master_clip_root, 'duration', str(duration))
    setElem(master_clip_root, 'in', '0')
    setElem(master_clip_root, 'out', str(duration))
    set

    # Go inside and add directly to the video track
    master_clip_track = master_clip_root.find('media')[0][0][0]
    setElem(master_clip_track, 'name', filename)
    setElem(master_clip_track, 'masterclipid', masterID)
    master_clip_track.set('id', masterID_component)
    master_clip_track.set('id', masterID)
    setElem(master_clip_track.find('rate'), 'timebase', str(framerate))

    # And then set the <file> attributes as well
    master_clip_file = master_clip_track.find('file')
    setElem(master_clip_file, 'name', filename)
    setElem(master_clip_file, 'pathurl', filepath)
    setElem(master_clip_file.find('rate'), 'timebase', str(framerate))

    # Append it to the Master clips bin
    bin_master_clips.append(master_clip_root)

    # Write it to the sequence


ET.dump(tree)
