
import os
import struct
from binascii import crc32

from PIL import Image

from hcg.image import HCGImage
from hcg.utils import BytesIO

PINDEX = struct.Struct("<HQQII")

class HCGArchive(object):
    comments = None
    _images = None
    _images_dict = None
    _filename = None
    _head_index_offset = None
    
    def __init__(self, filename):
        self._filename = filename
        
        f = self.f = open(self._filename, "rb")
        
        magicnumber = f.read(8)
        if magicnumber != b"HCG001\r\n":
            raise RuntimeError("%s is not a HCG archive")

        comments_length = int(f.read(8).strip(), 16)
        
        self.comments = f.read(comments_length)
        self._head_index_offset = 16 + comments_length
        
    def _load_images(self):
        self._load_image_from_head_index()
    
    def _load_image_from_head_index(self):
        images = []
        images_dict = {}
        
        self.f.seek(self._head_index_offset)
        
        offset = 8
        header_index_size = struct.unpack("<Q", self.f.read(8))[0]
        
        index_set = {}
        index_ref = {}
        while offset < header_index_size:
            buf = self.f.read(26)
            keylen, data_ptr, ref_ptr, img_size, img_crc32 = PINDEX.unpack(buf)
            key = self.f.read(keylen).decode()
            
            img = HCGArchiveImage(self.f, key, data_ptr, img_size, img_crc32)
            images.append(img)
            images_dict[key] = img
            
            index_set[offset + self._head_index_offset] = img
            if ref_ptr:
                index_ref[img] = ref_ptr
            
            offset += 26 + keylen

        for img, ref_ptr in index_ref.items():
            img.set_ref(index_set[ref_ptr])
        
        self._images = images
        self._images_dict = images_dict
    
    def _get_index_crc32(self):
        index_size = struct.unpack("<Q", self.f.read(8))[0]
        buf = self.f.read(index_size)
        expected_crc32 = struct.unpack("<i", self.f.read(4))[0]
        real_crc32 = crc32(buf)
        return expected_crc32, real_crc32
        
    def validate_header_index(self):
        self.f.seek(self._head_index_offset)
        expected_crc32, real_crc32 = self._get_index_crc32()
        
        if real_crc32 != expected_crc32:
            raise RuntimeError("HCG archive header index broken")
    
    def validate_tail_index(self):
        self.f.seek(-8, 2)
        tail_index_pos = struct.unpack("<Q", self.f.read(8))[0]
        
        self.f.seek(tail_index_pos - 8)
        buf = self.f.read(8)
        
        if buf != b"\x00\x00\x00\x00\x00\x00\x00\x00":
            raise RuntimeError("HCG archive tail index broken")
            
        expected_crc32, real_crc32 = self._get_index_crc32()
        
        if real_crc32 != expected_crc32:
            raise RuntimeError("HCG archive tail index broken")
        
    def get_images(self):
        if not self._images: self._load_images()
        return list(self._images)

class HCGArchiveImage(HCGImage):
    def __init__(self, f, key, position, size, data_crc32):
        super(HCGArchiveImage, self).__init__(key)
        
        self._f = f
        self._position = position
        self._size = size
        self._crc32 = data_crc32
    
    def get_image(self):
        buf = BytesIO(self.get_data())
        return Image.open(buf)
        
    def get_data(self):
        self._f.seek(self._position)
        return self._f.read(self._size)
    
    def calculate_crc32(self):
        buf = self.get_data()
        return crc32(buf) & 0xffffffff
    