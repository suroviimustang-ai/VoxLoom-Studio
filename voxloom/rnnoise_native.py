"""Minimal C API adapter for the RNNoise binary distributed by pyrnnoise.

The resampler and frame packing live in VoxLoom; audiolab is not imported.
See THIRD_PARTY_NOTICES.md and bundled licenses for RNNoise / pyrnnoise.
"""

import ctypes as ct
import sys
from importlib.metadata import distribution

import numpy as np

from .i18n import tr
from .processing import resource_root


def library_name(platform=None):
    platform = sys.platform if platform is None else platform
    names = {
        "win32": "rnnoise.dll",
        "darwin": "librnnoise.dylib",
        "linux": "librnnoise.so",
    }
    if platform not in names:
        raise RuntimeError(tr("RNNoise: unsupported platform {v0}", v0=platform))
    return names[platform]


def library_path():
    name = library_name()
    bundled = resource_root() / "native" / name
    if bundled.is_file():
        return bundled
    path = distribution("pyrnnoise").locate_file("pyrnnoise/" + name)
    if not path.is_file():
        raise RuntimeError(
            tr(
                "RNNoise: library {v0} is missing. Check the dependencies for your operating system.",
                v0=name,
            )
        )
    return path


def process(audio: np.ndarray) -> np.ndarray:
    lib = ct.CDLL(str(library_path()))
    lib.rnnoise_create.argtypes = [ct.c_void_p]
    lib.rnnoise_create.restype = ct.c_void_p
    lib.rnnoise_destroy.argtypes = [ct.c_void_p]
    lib.rnnoise_destroy.restype = None
    lib.rnnoise_get_frame_size.argtypes = []
    lib.rnnoise_get_frame_size.restype = ct.c_int
    lib.rnnoise_process_frame.argtypes = [
        ct.c_void_p,
        ct.POINTER(ct.c_float),
        ct.POINTER(ct.c_float),
    ]
    lib.rnnoise_process_frame.restype = ct.c_float
    size = lib.rnnoise_get_frame_size()
    if size != 480 or len(audio) % size:
        raise RuntimeError(tr("RNNoise: incompatible frame size."))
    state = lib.rnnoise_create(None)
    if not state:
        raise RuntimeError(tr("RNNoise: could not initialize the model state."))
    out = np.ascontiguousarray(np.clip(audio, -1, 1) * 32768, dtype=np.float32)
    try:
        for start in range(0, len(out), size):
            ptr = out[start : start + size].ctypes.data_as(ct.POINTER(ct.c_float))
            lib.rnnoise_process_frame(state, ptr, ptr)
    finally:
        lib.rnnoise_destroy(state)
    return out / 32768
