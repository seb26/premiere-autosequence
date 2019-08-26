import re


probe = {
    'format': {
        'tags': {
            "comment": "zSPEED=25.000ND\r\nzTAKE=001\r\nzUBITS=00000000\r\nzSCENE=130619\r\nzTAPE=130619\r\nzCIRCLED=FALSE\r\nzTRK3=Boom\r\nzTRK4=Wirele\r\nzTRK7=BOOM S\r\nzTRK8=Wirele\r\nzNOTE=\r\n"
        }
    }
}

BEXT_DATA = {}
if 'comment' in probe['format']['tags']:
    comment = probe['format']['tags']['comment']
    if comment[0] == 'z':
        # If it starts with z, it's probably BEXT chunks
        for k, v in [ line.split('=') for line in comment.splitlines() ]:
            BEXT_DATA[k] = v

if 'zSPEED' in BEXT_DATA.keys():
    # Regex match in the format: ##.###AA (e.g. 25.000ND)
    match = re.match( r"(\d*?\.\d*)(\w*)", BEXT_DATA['zSPEED'], re.I )
    if match:
        framerate, dropframe = match.groups()
        framerate = float(framerate)
        if framerate in VALID_FRAME_RATES:
            self.frameRate = framerate
