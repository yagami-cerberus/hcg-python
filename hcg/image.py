
import os

from PIL import Image

from hcg.utils import BytesIO
from hcg.utils import sampling_bbox, split_rect

__all__ = ["HCGImage"]

class HCGImage(object):
    _ref = None
    _size = None
    _crc32 = None
    _sample = None
    
    def __init__(self, key):
        self.key = key

    @property
    def group(self):
        # This field is to evaluate if two images can be diff
        # If two HCGImage has same group, hcg tool will try to diff this two
        # images.
        img = self.get_image()
        return img.size + (img.mode, )
    
    @property
    def size(self):
        # Return image size, if this image has a reference, return compressed
        # contents size
        return self._size
    
    @property
    def crc32(self):
        # Return image crc32, if this image has a reference, return compressed
        # contents crc32
        return self._crc32
    
    @property
    def ref(self):
        # Retuen reference HCGImage object
        return self._ref
    
    @property
    def has_diff(self):
        return self._ref and True or False
    
    def set_ref(self, ref_image):
        self._ref = ref_image
    
    @property
    def sample(self):
        # This method create features for image, if two image has same group
        # ths sample must contains same dimension sample.
        if not self._sample:
            sample = []
            img = self.get_origin_image()
            w, h = img.size
            for bbox in split_rect(w, h):
                sample.append(sampling_bbox(img.getdata(), w, h, bbox))
            self._sample = sample
        return self._sample
    
    
    def get_image(self):
        # return PIL Image object, if image is compressed
        raise RuntimeError("Override this method.")
    
    def get_image_data(self):
        return self.get_image().tobytes()
    
    def get_origin_image(self):
        if self.has_diff:
            ref_img = self._ref.get_image()
            diff_img = self.get_image()
            
            ref_data = bytearray(ref_img.tobytes())
            data = bytearray(diff_img.tobytes())
            
            i, l = 0, len(data)
            assert len(data) == len(ref_data)
            while i < l:
                data[i] = (data[i] + ref_data[i]) % 256
                i += 1
            
            return Image.frombytes(ref_img.mode, ref_img.size, bytes(data))
        else:
            return self.get_image()

    def get_data(self):
        # return bytes data
        raise RuntimeError("Override this method.")
        
    def create_diff_image(self, ref_image):
        data = bytearray(self.get_image_data())
        ref_data = bytearray(ref_image.get_image_data())
        
        i, l = 0, len(data)
        while i < l:
            _ = data[i] - ref_data[i]
            if _ < 0: _ += 256
            data[i] = _
            i += 1
        
        img = Image.frombytes(self.obj.mode, self.obj.size, bytes(data))
        
        f = BytesIO()
        img.save(f, "png")
        buf = f.getvalue()
        f.close()
        return buf

    def extract_to(self, basepath):
        path = os.path.join(basepath, self.key)
        base = os.path.dirname(path)
        
        if not os.path.isdir(base):
            os.makedirs(base)
        
        if self.has_diff:
            img = self.get_origin_image()
            img.save(path)
        else:
            # To reduce quality loss (for jpeg), copy file directly rether then
            # load image to memory and recompress to jpeg or other not lossless
            # image format.
            buf = self.get_data()
            with open(path, "wb") as f:
                f.write(buf)
                
    def __lt__(self, other):
        return self.__cmp__(other) < 0
        
    def __le__(self, other):
        return self.__cmp__(other) <= 0
        
    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0
    
    def __gt__(self, other):
        return self.__cmp__(other) > 0
    
    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    def __str__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.key, )
        
    def __repr__(self):
        return self.__str__()
    
    def __hash__(self):
        return id(self.key)
        
    def __cmp__(self, other):
        s, o = len(self.key), len(other.key)
        if s == o:
            if self.key > other.key: return 1
            elif self.key < other.key: return -1
            else: return 0
        else:
            if s > o: return 1
            else: return -1
