import re
import unittest

def is_arm64(instance_type):
    # Matches both numeric Graviton families and the a1 family
    return len(re.findall(r"^(a1|[a-z]+[0-9]g[a-z]*)\.", instance_type)) > 0

class TestIsArm64(unittest.TestCase):
    def test_graviton_detection(self):
        self.assertTrue(is_arm64("t4g.micro"))
        self.assertTrue(is_arm64("m6gd.large"))
        self.assertTrue(is_arm64("c7gn.xlarge"))
        self.assertTrue(is_arm64("a1.large"))
        self.assertFalse(is_arm64("t3.micro"))
        self.assertFalse(is_arm64("m5.large"))

if __name__ == '__main__':
    unittest.main()
