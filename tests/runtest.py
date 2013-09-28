#!/usr/bin/env python

import unittest

def main():
    from testcase import test_sampling
    from testcase import test_compress
    
    suite1 = unittest.TestLoader().loadTestsFromModule(test_sampling)
    suite2 = unittest.TestLoader().loadTestsFromModule(test_compress)

    all_suite = unittest.TestSuite([suite1, suite2])
    unittest.TextTestRunner(verbosity=2).run(all_suite)
    
    
if __name__ == '__main__':
    main()