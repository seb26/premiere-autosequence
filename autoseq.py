# Converts frames to SMPTE timecode of arbitrary frame rate and back.
# For DF calculations use 29.976 frame rate.
# Igor Ridanovic, igor@HDhead.com
# Modified by me, into a Class format with a defined framerate


class Timecode:

    def __init__(self, fps):
        self.fps = fps

    def validateTC(self, tc):
        """Validates SMPTE timecode"""
        if len(tc) != 11:
            raise ValueError ('Malformed SMPTE timecode', tc)
        if int(tc[9:]) > self.fps:
            raise ValueError ('SMPTE timecode to frame rate mismatch', tc, self.fps)

    def toFrames(self, tc):
        """Converts SMPTE timecode to frame count. Integer."""
        self.validateTC(tc)
        return int(round((int(tc[:2])*3600 +
                int(tc[3:5])*60 +
                int(tc[6:8]))*self.fps +
                int(tc[9:])))

    def toTC(self, x):
        """Converts frame count to SMPTE timecode. String."""
        spacer = ':'
        frHour = self.fps * 3600
        frSec = self.fps * 60
        hr = int(x // frHour)
        mn = int((x - hr * frHour) // frSec)
        sc = int((x - hr * frHour - mn * frSec) // self.fps)
        fr = int(round(x -  hr * frHour - mn * frSec - sc * self.fps))

        return(
        str(hr).zfill(2) + spacer +
        str(mn).zfill(2) + spacer +
        str(sc).zfill(2) + spacer +
        str(fr).zfill(2))

timebase = Timecode(25)
print(  timebase.toTC(2500), timebase.toFrames('12:20:13:00') )
