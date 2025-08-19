# subset_check.py
import random
import unittest
from typing import List
from pedersen import Pedersen
from shuffle import shuffle_commitments, random_permutation

def product_commitments(commitments: List[int], indices: List[int], p: int) -> int:
    result = 1
    for i in indices:
        result = (result * commitments[i]) % p
    return result

def invert_permutation(perm: List[int]) -> List[int]:
    """
    Given perm where output[j] = input[perm[j]],
    returns inv_perm where inv_perm[i] = j such that perm[j] = i.
    """
    n = len(perm)
    inv = [0] * n
    for j, i in enumerate(perm):
        inv[i] = j
    return inv

def subset_check(
    ped: Pedersen,
    inputs: List[int],
    input_openings: List[int],
    outputs: List[int],
    output_openings: List[int],
    perm: List[int],
    subset: List[int],
) -> bool:
    """
    Check: ∏_{i∈I} [w_i]  ?=  h^{R} · ∏_{i∈I} [ŵ_{π(i)}]
    with R = Σ_{i∈I} (r_i - r'_i)  (mod p-1).
    """
    if not subset:
        raise ValueError("Subset must be non-empty")

    # LHS: product of original commitments over subset
    lhs = product_commitments(inputs, subset, ped.p)

    # Map each original index i -> shuffled position j
    inv_perm = invert_permutation(perm)

    # RHS base: product of shuffled commitments at those positions
    rhs = 1
    R = 0
    mod_order = ped.p - 1  # exponent group order for prime modulus p
    for i in subset:
        j = inv_perm[i]  # where original i ended up
        rhs = (rhs * outputs[j]) % ped.p
        # IMPORTANT: input minus output randomness (not the other way around)
        R = (R + (input_openings[i] - output_openings[j])) % mod_order

    rhs = (rhs * pow(ped.h, R, ped.p)) % ped.p
    return lhs == rhs

# -------------------- Tests --------------------

class TestSubsetCheck(unittest.TestCase):
    def setUp(self):
        self.p = 208351617316091241234326746312124448251235562226470491514186331217050270460481
        self.g = 2
        self.h = 3
        self.ped = Pedersen(self.p, self.g, self.h)

        # Messages and commitments
        self.messages = [10, 20, 30, 40]
        self.inputs = []
        self.input_openings = []
        for w in self.messages:
            c, r = self.ped.commit(w)
            self.inputs.append(c)
            self.input_openings.append(r)

        # Shuffle setup
        self.perm = random_permutation(len(self.messages))
        rerands = [random.randint(1, self.p - 2) for _ in self.messages]
        self.outputs, self.perm_msgs, self.output_openings = shuffle_commitments(
            self.ped, self.messages, self.input_openings, self.perm, rerands
        )

    def test_honest_shuffle_passes_subset_check(self):
        n = len(self.messages)
        # Try several random non-empty subsets, plus the full set
        for _ in range(10):
            k = random.randint(1, n)
            subset = random.sample(range(n), k=k)
            self.assertTrue(
                subset_check(self.ped, self.inputs, self.input_openings,
                             self.outputs, self.output_openings, self.perm, subset)
            )
        # Full set subset should also pass
        self.assertTrue(
            subset_check(self.ped, self.inputs, self.input_openings,
                         self.outputs, self.output_openings, self.perm, list(range(n)))
        )

    def test_cheating_shuffle_fails_subset_check(self):
        bad_outputs = self.outputs[:]
        bad_outputs[0] = (bad_outputs[0] * 5) % self.p  # corrupt one output
        subset = [0, 1]
        self.assertFalse(
            subset_check(self.ped, self.inputs, self.input_openings,
                         bad_outputs, self.output_openings, self.perm, subset)
        )

    def test_empty_subset_is_invalid(self):
        with self.assertRaises(ValueError):
            subset_check(self.ped, self.inputs, self.input_openings,
                         self.outputs, self.output_openings, self.perm, [])

if __name__ == "__main__":
    unittest.main()
# This code implements a subset check for shuffled Pedersen commitments and includes unit tests to verify its functionality.