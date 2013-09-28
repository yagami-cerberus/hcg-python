
import unittest

from hcg import compress
from hcg import _compress

class TestCompress(unittest.TestCase):
    def diff_data(self):
        data = b"".join(chr(i) for i in range(256))
        ref_data = (data*2)[100:356]
        diffed = "\x9c"*256
        return data, ref_data, diffed
    
    def testDiff(self):
        data, ref_data, diffed = self.diff_data()
        b_data, b_ref_data = bytearray(data), bytearray(ref_data)
        
        compress.diff_buffer(b_data, b_ref_data, len(data))
        self.assertEqual(b_data, diffed)
    
        data, ref_data, answer = self.diff_data()
        _compress.diff_buffer(data, ref_data, len(data))
        self.assertEqual(b_data, diffed)
    
    def testMerge(self):
        data, ref_data, diffed = self.diff_data()
        b_diffed, b_ref_data = bytearray(diffed), bytearray(ref_data)
        
        compress.merge_buffer(b_diffed, b_ref_data, len(diffed))
        self.assertEqual(b_diffed, data)

        data, ref_data, diffed = self.diff_data()
        _compress.merge_buffer(diffed, ref_data, len(diffed))
        self.assertEqual(diffed, data)
        
