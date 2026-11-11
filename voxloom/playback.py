from __future__ import annotations

import numpy as np
import sounddevice as sd

from .diagnostics import LOG


class Playback:
    def __init__(self):
        self.stream = None
        self.position = 0
        self.end = 0
        self.data = None
        self.rate = 48000
        self.underflows = 0

    @property
    def playing(self):
        try:
            return self.stream is not None and self.stream.active
        except Exception:
            LOG.exception("Audio output became unavailable")
            self.pause()
            return False

    def play(self, data, rate, start, end):
        self.pause()
        self.data, self.rate = data, rate
        self.position, self.end = start, end
        channels = min(data.shape[1], 2)

        def callback(out, frames, time_info, status):
            if status.output_underflow:
                self.underflows += 1
            count = min(frames, self.end - self.position)
            out.fill(0)
            if count:
                if self.data.shape[1] > 2:
                    mixed = self.data[self.position : self.position + count].mean(
                        axis=1
                    )
                    out[:count] = mixed[:, None]
                else:
                    out[:count] = self.data[
                        self.position : self.position + count, :channels
                    ]
                np.clip(out, -1, 1, out=out)
                self.position += count
            if count < frames or self.position >= self.end:
                raise sd.CallbackStop

        try:
            self.stream = sd.OutputStream(
                samplerate=rate, channels=channels, dtype="float32", callback=callback
            )
            self.stream.start()
        except Exception:
            self.pause()
            raise

    def pause(self):
        if self.stream is not None:
            stream = self.stream
            self.stream = None
            try:
                stream.stop()
            except Exception:
                LOG.exception("Audio output could not be stopped")
            finally:
                try:
                    stream.close()
                except Exception:
                    LOG.exception("Audio output could not be closed")
