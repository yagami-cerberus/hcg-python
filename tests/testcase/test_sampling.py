
import unittest

from hcg import sampling
from hcg import _sampling

class TestLineSegement(unittest.TestCase):
    def test50(self):
        result = [i for i in sampling.split_line(50)]
        self.assertEqual([(0, 50)], result)

    def test100(self):
        result = [i for i in sampling.split_line(100)]
        self.assertEqual([(0, 100)], result)

    def test149(self):
        result = [i for i in sampling.split_line(149)]
        self.assertEqual([(0, 149)], result)

    def test150(self):
        result = [i for i in sampling.split_line(150)]
        self.assertEqual([(0, 75), (75, 150)], result)
        
    def test305(self):
        result = [i for i in sampling.split_line(305)]
        self.assertEqual([(0, 101), (101, 202), (202, 305)], result)

class TestRectChunk(unittest.TestCase):
    def test50_50(self):
        result = [i for i in sampling.split_rect(50, 50)]
        self.assertEqual([(0, 0, 50, 50)], result)

    def test100_50(self):
        result = [i for i in sampling.split_rect(100, 50)]
        self.assertEqual([(0, 0, 100, 50)], result)
    
    def test149_150(self):
        result = [i for i in sampling.split_rect(149, 150)]
        self.assertEqual(result, [(0, 0, 149, 75), (0, 75, 149, 150)])
    
    def test150_249(self):
        result = [i for i in sampling.split_rect(150, 249)]
        self.assertEqual(result, [(0, 0, 75, 124), (75, 0, 150, 124),
                                    (0, 124, 75, 249), (75, 124, 150, 249)])
        
    def test150_305(self):
        result = [i for i in sampling.split_rect(150, 305)]
        self.assertEqual(result, [(0, 0, 75, 101),
                                    (75, 0, 150, 101),
                                    (0, 101, 75, 202),
                                    (75, 101, 150, 202),
                                    (0, 202, 75, 305),
                                    (75, 202, 150, 305)])

class TestSamplingBbox(unittest.TestCase):
    B1 = []
    for y in range(60):
        for x in range(y, 80 + y):
            B1.append(chr(x))
    
    B3 = []
    for y in range(60):
        for x in range(y, 80 + y):
            B3.append(chr(x))
            B3.append(chr(x + 1))
            B3.append(chr(x + 2))
    
    ANSWER = {
        0: [(0, 0, 80, 60), [331200]],
        1: [(0, 0, 40, 30), [40800]],
        2: [(40, 0, 80, 30), [88800]],
        3: [(0, 30, 40, 60), [76800]],
        4: [(40, 30, 80, 60), [124800]],
        5: [(0, 0, 80, 30), [129600]],
        6: [(40, 0, 80, 60), [213600]],
        7: [(20, 15, 60, 45), [82800]]
    }
    
    def validateCb(self, index, result):
        self.assertEqual((index, self.ANSWER[index][1]), (index, result))
    
    def testNativeSampling(self):
        data = bytearray(b"".join(self.B1))
        
        for index, item in self.ANSWER.items():
            sampling.sampling_bbox(data, 80, 60, 1, item[0],
                self.validateCb, index)
    
    def testCythonSampling(self):
        data = b"".join(self.B1)
        
        for index, item in self.ANSWER.items():
            _sampling.sampling_bbox(data, 80, 60, 1, item[0],
                self.validateCb, index)
        
