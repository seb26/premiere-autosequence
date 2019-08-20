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
