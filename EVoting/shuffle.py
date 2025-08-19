# shuffle.py
import random
import unittest
from typing import List, Tuple

# Import Pedersen from your Step 1 file
# Make sure pedersen.py is in the same folder.
from pedersen import Pedersen

def apply_permutation(vec: List[int], perm: List[int]) -> List[int]:
    """
    Apply a permutation perm to vec.
    perm is a list of indices (0..n-1) describing where each input goes in the output.
    Example: perm = [2,0,1] means output[0]=input[2], output[1]=input[0], output[2]=input[1].
    """
    assert len(vec) == len(perm)
    n = len(vec)
    out = [None] * n
    for i in range(n):
        out[i] = vec[perm[i]]
    return out

def random_permutation(n: int) -> List[int]:
    perm = list(range(n))
    random.shuffle(perm)
    return perm

def shuffle_commitments(
    ped: Pedersen,
    messages: List[int],
    openings: List[int],
    perm: List[int],
    rerands: List[int],
) -> Tuple[List[int], List[int], List[int]]:
    """
    Given:
      - messages: w_i
      - openings: r_i (randomness for each commitment)
      - perm: a permutation over indices (length n)
      - rerands: additional randomness Δr_i to add to each commitment after permutation
    Output:
      - shuffled commitments C'_j
      - permuted messages w'_j = w_{perm[j]}
      - new openings r'_j = r_{perm[j]} + rerands_{perm[j]} (mod p-1)  [mod exponent group]
    """
    assert len(messages) == len(openings) == len(perm) == len(rerands)
    n = len(messages)

    # Permute messages and openings
    perm_messages = apply_permutation(messages, perm)
    perm_openings = apply_permutation(openings, perm)

    # Re-randomize commitments with additional randomness
    new_openings = []
    shuffled_commitments = []
    for j in range(n):
        r_prime = (perm_openings[j] + rerands[perm[j]]) % (ped.p - 1)  # exponent group modulo φ(p) ≈ p-1 for prime p
        new_openings.append(r_prime)
        c_prime = (pow(ped.g, perm_messages[j], ped.p) * pow(ped.h, r_prime, ped.p)) % ped.p
        shuffled_commitments.append(c_prime)

    return shuffled_commitments, perm_messages, new_openings


# -------------------- Tests --------------------

class TestShuffle(unittest.TestCase):
    def setUp(self):
        # Same safe-ish prime and generators as Step 1 (toy values for research prototype)
        self.p = 208351617316091241234326746312124448251235562226470491514186331217050270460481
        self.g = 2
        self.h = 3
        self.ped = Pedersen(self.p, self.g, self.h)

        # Create a small dataset of commitments
        self.messages = [10, 20, 30, 40, 50]
        self.commitments = []
        self.openings = []
        for w in self.messages:
            c, r = self.ped.commit(w)
            self.commitments.append(c)
            self.openings.append(r)

    def test_apply_permutation(self):
        perm = [2, 0, 4, 1, 3]  # length 5 permutation
        expected = [self.messages[2], self.messages[0], self.messages[4], self.messages[1], self.messages[3]]
        self.assertEqual(apply_permutation(self.messages, perm), expected)

    def test_shuffle_produces_valid_openings(self):
        n = len(self.messages)
        perm = random_permutation(n)
        # Extra randomness for each original position (index by original index)
        rerands = [random.randint(1, self.p - 2) for _ in range(n)]

        shuffled_C, perm_msgs, new_openings = shuffle_commitments(
            self.ped, self.messages, self.openings, perm, rerands
        )

        # Verify: each shuffled commitment opens to the permuted message with its new opening
        for c_prime, w_prime, r_prime in zip(shuffled_C, perm_msgs, new_openings):
            self.assertTrue(self.ped.verify(c_prime, w_prime, r_prime))

    def test_shuffle_breaks_if_wrong_openings(self):
        n = len(self.messages)
        perm = random_permutation(n)
        rerands = [random.randint(1, self.p - 2) for _ in range(n)]

        shuffled_C, perm_msgs, new_openings = shuffle_commitments(
            self.ped, self.messages, self.openings, perm, rerands
        )

        # Tamper with an opening: should fail verification for at least one
        tampered = new_openings[:]
        tampered[0] = (tampered[0] + 1) % (self.p - 1)

        ok_all = True
        for c_prime, w_prime, r_prime in zip(shuffled_C, perm_msgs, tampered):
            ok_all &= self.ped.verify(c_prime, w_prime, r_prime)
        self.assertFalse(ok_all)

    def test_shuffle_breaks_if_wrong_messages(self):
        n = len(self.messages)
        perm = random_permutation(n)
        rerands = [random.randint(1, self.p - 2) for _ in range(n)]

        shuffled_C, perm_msgs, new_openings = shuffle_commitments(
            self.ped, self.messages, self.openings, perm, rerands
        )

        # Tamper with a message: should fail
        bad_msgs = perm_msgs[:]
        bad_msgs[0] += 1

        ok_all = True
        for c_prime, w_prime, r_prime in zip(shuffled_C, bad_msgs, new_openings):
            ok_all &= self.ped.verify(c_prime, w_prime, r_prime)
        self.assertFalse(ok_all)

    def test_shuffle_with_identity_perm_is_just_rerandomization(self):
        n = len(self.messages)
        perm = list(range(n))  # identity
        rerands = [random.randint(1, self.p - 2) for _ in range(n)]

        shuffled_C, perm_msgs, new_openings = shuffle_commitments(
            self.ped, self.messages, self.openings, perm, rerands
        )

        # Messages should be identical order
        self.assertEqual(perm_msgs, self.messages)

        # Each new commitment should verify as the same message with new randomness
        self.assertTrue(all(
            self.ped.verify(c_prime, w, r_prime)
            for c_prime, w, r_prime in zip(shuffled_C, self.messages, new_openings)
        ))

    def test_roundtrip_vs_naive_formula(self):
        """
        Cross-check one position against the algebra:
        C'_j ?= g^{w_{perm[j]}} * h^{r_{perm[j]} + rerands[perm[j]]}
        """
        n = len(self.messages)
        perm = random_permutation(n)
        rerands = [random.randint(1, self.p - 2) for _ in range(n)]

        shuffled_C, perm_msgs, new_openings = shuffle_commitments(
            self.ped, self.messages, self.openings, perm, rerands
        )

        j = 0
        i = perm[j]  # original index that moved to position j
        lhs = shuffled_C[j]
        rhs = (pow(self.g, self.messages[i], self.p) *
               pow(self.h, (self.openings[i] + rerands[i]) % (self.p - 1), self.p)) % self.p
        self.assertEqual(lhs, rhs)


if __name__ == "__main__":
    unittest.main()
# This code implements a shuffle function for Pedersen commitments and includes unit tests to verify its functionality.