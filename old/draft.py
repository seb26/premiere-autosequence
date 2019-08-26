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
