
__all__ = ["BytesIO"]

try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO

