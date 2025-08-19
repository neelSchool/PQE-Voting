# pedersen.py
import random
import unittest

class Pedersen:
    def __init__(self, p, g, h):
        """
        Setup for Pedersen commitments.
        :param p: large prime modulus
        :param g: group generator
        :param h: independent generator
        """
        self.p = p
        self.g = g
        self.h = h

    def commit(self, w, r=None):
        """
        Commit to message w with randomness r.
        C = g^w * h^r mod p
        """
        if r is None:
            r = random.randint(1, self.p - 1)
        c = (pow(self.g, w, self.p) * pow(self.h, r, self.p)) % self.p
        return c, r

    def verify(self, c, w, r):
        """Check if c is a valid commitment to w with randomness r."""
        expected = (pow(self.g, w, self.p) * pow(self.h, r, self.p)) % self.p
        return c == expected


# ---------- Tests ----------
class TestPedersen(unittest.TestCase):
    def setUp(self):
        # A small safe prime for testing (in real life this should be 2048+ bits)
        self.p = 208351617316091241234326746312124448251235562226470491514186331217050270460481
        self.g = 2
        self.h = 3
        self.ped = Pedersen(self.p, self.g, self.h)

    def test_commit_and_verify(self):
        w = 42
        c, r = self.ped.commit(w)
        self.assertTrue(self.ped.verify(c, w, r))

    def test_different_randomness(self):
        w = 99
        c1, r1 = self.ped.commit(w)
        c2, r2 = self.ped.commit(w)
        self.assertNotEqual(c1, c2)  # same message, different commitments

    def test_wrong_opening(self):
        w = 50
        c, r = self.ped.commit(w)
        self.assertFalse(self.ped.verify(c, w + 1, r))  # wrong message
        self.assertFalse(self.ped.verify(c, w, r + 1))  # wrong randomness


if __name__ == "__main__":
    unittest.main()
# This code implements a simple Pedersen commitment scheme and includes unit tests to verify its functionality.