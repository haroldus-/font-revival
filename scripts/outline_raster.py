"""Rasterize exceptionally dense vector outlines without font-engine limits.

Cairo 1.18.0 is the pinned Linux reference renderer. Other families retain their
existing FreeType path. The A8 surface preserves transparent antialiased ink.
"""
import ctypes
import ctypes.util
from functools import lru_cache

from fontTools.pens.basePen import BasePen
from fontTools.svgLib.path import parse_path
from PIL import Image


@lru_cache(maxsize=1)
def cairo():
    file = ctypes.util.find_library('cairo')
    if not file:
        raise RuntimeError('Dense-outline rasterization requires Cairo 1.18.0 (libcairo2).')
    lib = ctypes.CDLL(file)
    ptr, integer, real = ctypes.c_void_p, ctypes.c_int, ctypes.c_double
    signatures = {
        'cairo_version_string': (ctypes.c_char_p, []),
        'cairo_image_surface_create': (ptr, [integer, integer, integer]),
        'cairo_image_surface_get_data': (ptr, [ptr]),
        'cairo_image_surface_get_stride': (integer, [ptr]),
        'cairo_create': (ptr, [ptr]), 'cairo_status': (integer, [ptr]),
        'cairo_status_to_string': (ctypes.c_char_p, [integer]),
        'cairo_translate': (None, [ptr, real, real]),
        'cairo_scale': (None, [ptr, real, real]),
        'cairo_set_source_rgba': (None, [ptr, real, real, real, real]),
        'cairo_move_to': (None, [ptr, real, real]),
        'cairo_line_to': (None, [ptr, real, real]),
        'cairo_curve_to': (None, [ptr, real, real, real, real, real, real]),
        'cairo_close_path': (None, [ptr]), 'cairo_fill': (None, [ptr]),
        'cairo_surface_flush': (None, [ptr]), 'cairo_destroy': (None, [ptr]),
        'cairo_surface_destroy': (None, [ptr]),
    }
    for name, (result, args) in signatures.items():
        function = getattr(lib, name); function.restype = result; function.argtypes = args
    if lib.cairo_version_string() != b'1.18.0':
        raise RuntimeError('Use pinned Cairo 1.18.0 for repeatable dense-outline PNGs.')
    return lib


def rasterize(svg, width, height, scale, origin=(0, 0)):
    lib = cairo()
    surface = lib.cairo_image_surface_create(2, width, height)  # A8
    context = lib.cairo_create(surface)
    try:
        lib.cairo_translate(context, *origin)
        lib.cairo_scale(context, scale, -scale)
        lib.cairo_set_source_rgba(context, 1, 1, 1, 1)

        class Pen(BasePen):
            def _moveTo(self, p): lib.cairo_move_to(context, *p)
            def _lineTo(self, p): lib.cairo_line_to(context, *p)
            def _curveToOne(self, a, b, c): lib.cairo_curve_to(context, *a, *b, *c)
            def _closePath(self): lib.cairo_close_path(context)
            def _endPath(self): pass

        parse_path(svg, Pen(None))
        lib.cairo_fill(context)
        status = lib.cairo_status(context)
        if status:
            raise ValueError(lib.cairo_status_to_string(status).decode())
        lib.cairo_surface_flush(surface)
        stride = lib.cairo_image_surface_get_stride(surface)
        address = lib.cairo_image_surface_get_data(surface)
        data = ctypes.string_at(address, stride * height)
        return Image.frombytes('L', (width, height), data, 'raw', 'L', stride)
    finally:
        lib.cairo_destroy(context)
        lib.cairo_surface_destroy(surface)
