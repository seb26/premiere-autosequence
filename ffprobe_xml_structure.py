pr_xml_base_structure = """
<!DOCTYPE xmeml>
<xmeml version="4">
    <bin>
        <name />
        <labels>
            <label2>Mango</label2>
        </labels>
        <children>
            <bin>
                <name />
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
                    <string />
                    <frame />
                    <displayformat>NDF</displayformat>
                </timecode>
                <media>
                    <video>
                        <format>
							<samplecharacteristics>
								<rate>
									<timebase />
									<ntsc>FALSE</ntsc>
								</rate>
								<codec>
									<name />
								</codec>
								<width />
								<height />
								<pixelaspectratio />
								<fielddominance />
							</samplecharacteristics>
						</format>
                        <track>
                            <enabled>TRUE</enabled>
							<locked>FALSE</locked>
                        </track>
                    </video>
                    <audio>
                        <track>
                            <enabled>TRUE</enabled>
							<locked>FALSE</locked>
                            <outputchannelindex />
                        </track>
                    </audio>
                </media>
            </sequence>


        </children>
    </bin>
</xmeml>
"""

pr_xml_default_sequence_attributes = {
    "TL.SQAudioVisibleBase": "0",
    "TL.SQVideoVisibleBase": "0",
    "TL.SQVisibleBaseTime": "0",
    "TL.SQAVDividerPosition": "0.5",
    "TL.SQHideShyTracks": "0",
    "TL.SQHeaderWidth": "236",
    "Monitor.ProgramZoomOut": "365386775040000",
    "Monitor.ProgramZoomIn": "0",
    "TL.SQTimePerPixel": "2.2205228758169935",
    "MZ.EditLine": "359280230400000",
    "MZ.Sequence.PreviewFrameSizeHeight": "1080",
    "MZ.Sequence.PreviewFrameSizeWidth": "1920",
    "MZ.Sequence.AudioTimeDisplayFormat": "200",
    "MZ.Sequence.PreviewRenderingClassID": "1297106761",
    "MZ.Sequence.PreviewRenderingPresetCodec": "1297107278",
    "MZ.Sequence.PreviewRenderingPresetPath": "EncoderPresets\\SequencePreview\\d8484cf3-c96c-4622-ab1f-ac1a16e196f9\\I-Frame Only MPEG.epr",
    "MZ.Sequence.PreviewUseMaxRenderQuality": "false",
    "MZ.Sequence.PreviewUseMaxBitDepth": "false",
    "MZ.Sequence.EditingModeGUID": "d8484cf3-c96c-4622-ab1f-ac1a16e196f9",
    "MZ.Sequence.VideoTimeDisplayFormat": "101",
    "MZ.WorkOutPoint": "72272632320000",
    "MZ.WorkInPoint": "0",
    "MZ.ZeroPoint": "11281612608000000",
    "explodedTracks": "true",
}

pr_xml_default_sequence_video_track_attributes = {
    "TL.SQTrackShy": "0",
    "TL.SQTrackExpandedHeight": "25",
    "TL.SQTrackExpanded": "0",
    "MZ.TrackTargeted": "1",
}

pr_xml_default_sequence_audio_track_attributes = {
    "TL.SQTrackAudioKeyframeStyle": "0",
    "TL.SQTrackShy": "0",
    "TL.SQTrackExpandedHeight": "25",
    "TL.SQTrackExpanded": "0",
    "MZ.TrackTargeted": "1",
    "PannerCurrentValue": "0.5",
    "PannerStartKeyframe": "-91445760000000000,0.5,0,0,0,0,0,0", "PannerName": "Balance",
    "currentExplodedTrackIndex": "0",
    "totalExplodedTrackCount": "1",
    "premiereTrackType": "Mono",
}

pr_xml_video_masterclip = """
<clip explodedTracks="true">
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
                    <alphatype>none</alphatype>
                    <pixelaspectratio>square</pixelaspectratio>
                    <anamorphic>FALSE</anamorphic>
                    <file>
                        <name />
                        <pathurl />
                        <rate>
                            <timebase />
                            <ntsc>FALSE</ntsc>
                        </rate>
                        <media>
                            <video>
                                <samplecharacteristics>
                                    <rate>
                                        <timebase />
                                        <ntsc>FALSE</ntsc>
                                    </rate>
                                    <width />
                                    <height />
                                    <pixelaspectratio />
                                    <fielddominance />
                                </samplecharacteristics>
                            </video>
                            <audio>
                                <samplecharacteristics>
                                    <depth />
                                    <samplerate />
                                </samplecharacteristics>
                                <channelcount />
                            </audio>
                        </media>
                    </file>
                </clipitem>
            </track>
        </video>
    </media>
	<logginginfo>
        <description />
        <scene />
        <shottake />
        <lognote />
    </logginginfo>
    <labels>
        <label2>Iris</label2>
    </labels>
</clip>
"""

pr_xml_audio_masterclip = """
<clip explodedTracks="true">
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
        <audio>
            <track>

            </track>
        </audio>
    </media>
	<logginginfo>
        <description />
        <scene />
        <shottake />
        <lognote />
    </logginginfo>
    <labels>
        <label2>Iris</label2>
    </labels>
</clip>
"""

pr_xml_audio_masterclip_clipitem = """
                <clipitem>
                    <masterclipid />
                    <name />
                    <rate>
                        <timebase />
                        <ntsc>FALSE</ntsc>
                    </rate>
                    <file>
                        <name />
                        <pathurl />
                        <rate>
                            <timebase />
                            <ntsc>FALSE</ntsc>
                        </rate>
                        <duration />
                        <timecode>
                            <rate>
                                <timebase />
                                <ntsc>TRUE</ntsc>
                            </rate>
                            <string />
                            <frame />
                            <displayformat />
                            <reel>
                                <name />
                            </reel>
                        </timecode>
                        <media>
                            <audio>
                                <samplecharacteristics>
                                    <depth />
                                    <samplerate />
                                </samplecharacteristics>
                                <channelcount />
                                <audiochannel>
                                    <sourcechannel>1</sourcechannel>
                                </audiochannel>
                            </audio>
                        </media>
                    </file>
                    <sourcetrack>
                        <mediatype>audio</mediatype>
                        <trackindex />
                    </sourcetrack>
                </clipitem>
"""

pr_xml_audio_clip_channel = """
                            <audio>
                                <samplecharacteristics>
                                    <depth />
                                    <samplerate />
                                </samplecharacteristics>
                                <channelcount />
                                <audiochannel>
                                    <sourcechannel>1</sourcechannel>
                                </audiochannel>
                            </audio>
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
