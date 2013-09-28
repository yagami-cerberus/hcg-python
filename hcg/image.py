
import os
from threading import Event, Lock

from PIL import Image

from hcg import _sampling
from hcg import _compress
from hcg.compress import diff_buffer, merge_buffer
from hcg.sampling import sampling_bbox, split_rect
from hcg.threading_pool import ThreadPool
from hcg.utils import BytesIO

__all__ = ["HCGImage"]

class HCGImage(object):
    _ref = None
    _size = None
    _crc32 = None
    _sample = None
    _sample_ttl = None
    _sample_event = None
    _sample_lock = None
    
    
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
        if not self._sample:
            self.make_sample()
        
        while self._sample_event.wait(0.5) == False:
            pass
        
        return self._sample
    
    def make_sample(self):
        # This method create features for image, if two image has same group
        # ths sample must contains same dimension samples.
        
        img = self.get_origin_image()
        
        if img.mode == "RGB":
            bands = 3
        elif img.mode == "RGBA":
            bands = 4
        elif img.mode == "L":
            bands = 1
        else:
            raise RuntimeError("Sampling only work for 8-bits depth image")
        
        if self._sample_event and self._sample_event.is_set() == False:
            # Another sampling task is running
            return
        else:
            self._sample_event = Event()
            self._sample_lock = Lock()
        
        w, h = img.size
        
        regions = []
        self._sample = []
        self._sample_ttl = 0
        
        for bbox in split_rect(w, h):
            self._sample.append(None)
            regions.append((self._sample_ttl, bbox))
            self._sample_ttl += 1
        
        pool = ThreadPool.default_pool()
        
        # @CYTHON
        data = img.tobytes()
        
        for index, bbox in regions:
            pool.assign_task((_sampling.sampling_bbox, (data, w, h, bands, bbox, self._make_sample_cb, index), {}))
        # @NATIVE
        # data = bytearray(img.tobytes())
        # 
        # for index, bbox in regions:
        #     pool.assign_task((sampling_bbox, (data, w, h, bands, bbox, self._make_sample_cb, index), {}))
        # @END
    
    def _make_sample_cb(self, index, result):
        self._sample[index] = result
        
        with self._sample_lock:
            self._sample_ttl -= 1
            if self._sample_ttl == 0:
                self._sample_event.set()
    
    def get_image(self):
        # return PIL Image object, if image is compressed
        raise RuntimeError("Override this method.")
    
    def get_image_data(self):
        return self.get_image().tobytes()
    
    def get_origin_image(self):
        if self.has_diff:
            ref_img = self._ref.get_image()
            diff_img = self.get_image()
            
            # @CYTHON
            ref_data = ref_img.tobytes()
            data = diff_img.tobytes()
            _compress.merge_buffer(data, ref_data, len(data))
            return Image.frombytes(ref_img.mode, ref_img.size, data)
            
            # @NATIVE
            # ref_data = bytearray(ref_img.tobytes())
            # data = bytearray(diff_img.tobytes())
            # 
            # merge_buffer(data, ref_data, len(data))
            # 
            # return Image.frombytes(ref_img.mode, ref_img.size, bytes(data))
            # @END
        else:
            return self.get_image()

    def get_data(self):
        # return bytes data
        raise RuntimeError("Override this method.")
    
    def create_diff_image(self, ref_image):
        img = self.get_image()

        # @CYTHON
        data = img.tobytes()
        ref_data = ref_image.get_image_data()
        _compress.diff_buffer(data, ref_data, len(data))
        
        img = Image.frombytes(img.mode, img.size, data)
        # @NATIVE
        # data = bytearray(img.tobytes())
        # ref_data = bytearray(ref_image.get_image_data())
        # 
        # diff_buffer(data, ref_data, len(data))
        # 
        # img = Image.frombytes(img.mode, img.size, bytes(data))
        # @END
        
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

