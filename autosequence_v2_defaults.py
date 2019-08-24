DEFAULT_AUDIO_SAMPLE_RATE = 48000
DEFAULT_AUDIO_BIT_DEPTH = 16
DEFAULT_AUDIO_CHANNELS = 2

DEFAULT_VIDEO_FRAME_RATE = 25
DEFAULT_FRAME_RATE_NTSC = 'FALSE'
DEFAULT_VIDEO_TIMECODE_DISPLAYFORMAT = 'NDF'
VALID_FRAME_RATES = [ 23.976, 23.98, 24, 25, 29.97, 30 ]

DEFAULT_SEQUENCE_COLOURDEPTH = 24 # bit
DEFAULT_SEQUENCE_AUDIO_OUTPUT_CHANNELS = 2

DEFAULT_LABEL_COLOUR_VIDEO = 'Iris'
DEFAULT_LABEL_COLOUR_AUDIO = 'Caribbean'
DEFAULT_LABEL_COLOUR_SEQUENCE = 'Rose'
DEFAULT_LABEL_COLOUR_BIN = 'Mango'

DEFAULT_XMEML_VERSION = '4'

DEFAULT_SEQUENCE_ATTRIBUTES = {
    "TL.SQAudioVisibleBase": "0",
    "TL.SQVideoVisibleBase": "0",
    "TL.SQVisibleBaseTime": "0",
    "TL.SQAVDividerPosition": "0.5",
    "TL.SQHideShyTracks": "0",
    "TL.SQHeaderWidth": "236",
    "Monitor.ProgramZoomOut": "1923967987200000",
    "Monitor.ProgramZoomIn": "0",
    "TL.SQTimePerPixel": "5.8178647023939369",
    "MZ.EditLine": "1897723054080000",
    "MZ.Sequence.PreviewFrameSizeHeight": "1080",
    "MZ.Sequence.PreviewFrameSizeWidth": "1678",
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
    "MZ.ZeroPoint": "10601662579200000",
    "explodedTracks": "true",
}

DEFAULT_SEQUENCE_VIDEO_TRACK_ATTRIBUTES = {
    "TL.SQTrackShy": "0",
    "TL.SQTrackExpandedHeight": "25",
    "TL.SQTrackExpanded": "0",
    "MZ.TrackTargeted": "1",
}

DEFAULT_SEQUENCE_AUDIO_TRACK_ATTRIBUTES = {
    "TL.SQTrackAudioKeyframeStyle": "0",
    "TL.SQTrackShy": "0",
    "TL.SQTrackExpandedHeight": "25",
    "TL.SQTrackExpanded": "0",
    "MZ.TrackTargeted": "1",
    "PannerCurrentValue": "0.5",
    "PannerStartKeyframe": "-91445760000000000,0.5,0,0,0,0,0,0", "PannerName": "Balance",
    "currentExplodedTrackIndex": "0",
    "totalExplodedTrackCount": "1",
    "premiereTrackType": "Stereo",
}
