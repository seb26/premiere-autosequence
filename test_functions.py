DEFAULT_LABEL_COLOUR_VIDEO = 'Iris'
DEFAULT_LABEL_COLOUR_AUDIO = 'Mango'
DEFAULT_LABEL_COLOUR_SEQUENCE = 'Rose'


## INDEPENDENT FUNCTIONS
##

def xml_add_framerate(framerate, ntsc=False):
    # Give it an XML element
    # And it will immediately attach:
    #   <rate><timebase>25</timebase><ntsc>FALSE</ntsc></rate>
    rate = ET.Element('rate')
    timebase = ET.Subelement(rate, framerate)
    n = ET.Subelement(rate, ntsc)
    return rate

def xml_add_label(colour):
    # Returns: <labels><label2>colour</label2></labels>
    labels = ET.Element('labels')
    label2 = ET.Subelement(a, 'label2')
    label2.text = colour
    return labels

def createElem(parent, tag, value=''):
    # Creates a subelement of your parent
    # Set its text value to something, or empty if unspecified
    # And then gives this subelement back to you to use
    t = ET.Subelement(parent, tag)
    t.text = value
    return t




class BuildXML:

    def __init__(self):

        # Collect a centralised ID space
        self.index = {}
        for count in [ 'masterclipID', 'clipitemID', 'fileID' ]:
            # Set all IDs to 1 to start with
            self.index[count] = 1

    def _increment(self, indexType):
        self.index[indexType] += 1
        index_label = indexType + '-' + self.index[indexType]
        return index_label

    def xml_masterclip_video(media_item):
        clip = ET.Element('clip')
        duration = createElem(clip, 'duration', media_item.duration)
        ismasterclip = createElem(clip, 'ismasterclip', 'True')
        name = createElem(clip, 'name', media_item.name)

        # Increment the masterclipID, and assign it back to the [media_item]
        # Add it to the id="" attribute
        # And describe it in text as <masterclipid>
        media_item.masterclipID = self._increment('masterclipID')
        clip.set('id', media_item.masterclipID )
        masterclipid_tag = createElem(clip, 'masterclipid', media_item.masterclipID)
        clip.set('explodedTracks', 'True')

        label = xml_add_label(DEFAULT_LABEL_COLOUR_VIDEO)
        clip.append(label)

        rate = xml_add_framerate(clip, media_item.framerate)
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
        clip.set('id', media_item.fileID )
        
        file_tag.append(name)
        file_tag.append(rate)
        file_tag.append(duration)
        pathurl = createElem(file_tag, 'pathurl', media_item.pathurl)
        timecode = createElem(file_tag, 'timecode')
        timecode.append(rate)
        timecode_string = createElem(timecode, 'string', media_item.timecode_string)
        timecode_frame = createElem(timecode, 'frame', media_item.timecode_frame_n)
        timecode_displayformat = createElem(timecode, 'displayformat')
        # reel?

        file_tag_media = createElem(file_tag, 'media')
        file_tag_media_video = createElem(file_tag_media, 'video')
        video_samplecharacteristics = createElem(file_tag_media_video, 'samplecharacteristics')
        width = createElem(video_samplecharacteristics, 'width', media_item.width)
        height = createElem(video_samplecharacteristics, 'height', media_item.height)
        fielddomiance = createElem(video_samplecharacteristics, 'fielddomiance', media_item.fielddomiance)
        video_samplecharacteristics.append(rate)
        video_samplecharacteristics.append(anamorphic)
        video_samplecharacteristics.append(pixelaspectratio)
