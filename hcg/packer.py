
import os
import struct
from hashlib import md5
from binascii import crc32

from PIL import Image

from hcg.image import HCGImage
# from hcg.utils import sampling_bbox, split_rect
from hcg.utils import BytesIO

P_UINT64 = struct.Struct("<Q")
P_CRC32 = struct.Struct("<I")
P_HEADER = struct.Struct("<HQQII")

PACKAGE_COMMENT = """This file is create via personal package tool.
If you got this file and want to expend it, please visit https://github.com/yagami-cerberus"""


class HCHPacker(object):
    _offset_magic = 16
    _offset_head_index = None
    _offset_data = None
    _offset_tail_index = None
    
    def __init__(self, filepath):
        self.f = open(filepath, "wb")
        self.f.write(b"HCG001\r\n")
    
    def write_comment_header(self, message=PACKAGE_COMMENT):
        comment_length = len(message)
        self.f.write(("%06x\r\n" % comment_length).encode())
        self.f.write(message.encode())
        
        self._offset_head_index = self._offset_magic + comment_length
    
    def write_body(self, images):
        assert self._offset_head_index, "Write archive comment first"

        images.sort()
        images_meta = self._write_header_index(images)
        
        for i in images:
            self.f.write(i.get_data())
        
        self.f.write(b"\x00\x00\x00\x00\x00\x00\x00\x00")
        
        self._write_tail_index(images, images_meta)
        
        self.f.write(P_UINT64.pack(self._offset_tail_index))
    
    def _write_header_index(self, images):
        assert self._offset_head_index, "Write archive comment first"
        assert self._offset_data == None, "Its gone..."
        
        index_offset = 8 # 8 is image_index_length
        data_size = 0
        
        images_meta = {}
        
        for i in images:
            key = i.key.encode() # To bytes
            keylen = len(key)
            
            meta = images_meta[i] = {
                "key": key,
                "keylen": keylen,
                "index_offset": self._offset_head_index + index_offset,
                "data_heap": data_size,
            }
            
            if i.ref:
                meta["ref_index_offset"] = images_meta[i.ref]["index_offset"]
            else:
                meta["ref_index_offset"] = 0
            
            index_offset += (26 + keylen)
            data_size += i.size
        
        self._offset_data = self._offset_head_index + index_offset + 4 # 4 is header CRC32
        self._offset_tail_index = self._offset_data + data_size + 8 # 8 is ZERO-padding
        
        header_buffer = BytesIO()
        
        for i in images:
            meta = images_meta[i]
            header_buffer.write(
                P_HEADER.pack(
                    meta["keylen"],
                    self._offset_data + meta["data_heap"],
                    meta["ref_index_offset"],
                    i.size,
                    i.crc32
                )
            )
            header_buffer.write(meta["key"])
        
        self._write_index(header_buffer.getvalue())
        return images_meta
    
    def _write_tail_index(self, images, images_meta):
        assert self._offset_data

        index_offset = 8
        
        for i in images:
            meta = images_meta[i]
            meta["index_offset"] = self._offset_tail_index + index_offset

            if i.ref:
                meta["ref_index_offset"] = images_meta[i.ref]["index_offset"]
            else:
                meta["ref_index_offset"] = 0
        
            index_offset += (26 + meta["keylen"])
    
        index_buffer = BytesIO()
        
        for i in images:
            meta = images_meta[i]
            index_buffer.write(
                P_HEADER.pack(
                    meta["keylen"],
                    self._offset_data + meta["data_heap"],
                    meta["ref_index_offset"],
                    i.size,
                    i.crc32
                )
            )
            index_buffer.write(meta["key"])

        self._write_index(index_buffer.getvalue())

    def _write_index(self, header_data):
        h_length = len(header_data)
        h_crc32 = crc32(header_data) & 0xffffffff
        
        self.f.write(P_UINT64.pack(h_length))
        self.f.write(header_data)
        self.f.write(P_CRC32.pack(h_crc32))
    
    def close(self):
        self.f.close()

class HCGPackImage(HCGImage):
    def __init__(self, key, filename):
        super(HCGPackImage, self).__init__(key)
        
        with open(filename, "rb") as f:
            buf = f.read()
        
        self._img = Image.open(filename)
        
        self._orig_filename = filename
        self._orig_size = len(buf)
        
        self._size = len(buf)
        self._crc32 = crc32(buf) & 0xffffffff
    
    def get_data(self):
        fn = self.has_diff and self._rdu_filename or self._orig_filename
        with open(fn, "rb") as f:
            buf = f.read()
        return buf
    
    def get_image(self):
        if self.has_diff:
            return Image.open(self._rdu_filename)
        else:
            return self._img
    
    def get_origin_image(self):
        return self._img
    
    def make_ref(self, ref_image, tempfolder, threshold=0.5):
        buf = self.create_diff_image(ref_image)
        
        if float(len(buf)) / self._orig_size < threshold:
            tempfile = os.path.join(
                tempfolder,
                "%s.png" % md5(self.key.encode()).hexdigest()
            )
            
            with open(tempfile, "wb") as f:
                f.write(buf)
            
            self._ref = ref_image
            self._crc32 = crc32(buf) & 0xffffffff
            self._size = os.path.getsize(tempfile)
            
            self._rdu_filename = tempfile
            
            return True
        else:
            return False
    