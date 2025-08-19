# fullprotocol.py
import random
import unittest
from pedersen import Pedersen
from shuffle import shuffle_commitments, random_permutation
from subset_check import subset_check, invert_permutation

class ProtocolProver:
    def __init__(self, ped: Pedersen, messages, openings):
        self.ped = ped
        self.messages = messages
        self.openings = openings

    def shuffle_and_prove(self):
        n = len(self.messages)
        perm = random_permutation(n)
        rerands = [random.randint(1, self.ped.p - 2) for _ in range(n)]
        outputs, perm_msgs, output_openings = shuffle_commitments(
            self.ped, self.messages, self.openings, perm, rerands
        )
        return outputs, perm_msgs, output_openings, perm

class ProtocolVerifier:
    def __init__(self, ped: Pedersen):
        self.ped = ped

    def check(self, subset, inputs, input_openings, outputs, output_openings, perm):
        return subset_check(self.ped, inputs, input_openings, outputs, output_openings, perm, subset)

# -------------------- Tests --------------------
class TestProtocol(unittest.TestCase):
    def setUp(self):
        self.p = 208351617316091241234326746312124448251235562226470491514186331217050270460481
        self.g = 2
        self.h = 3
        self.ped = Pedersen(self.p, self.g, self.h)

        self.messages = [5, 15, 25, 35, 45]
        self.inputs = []
        self.input_openings = []
        for w in self.messages:
            c, r = self.ped.commit(w)
            self.inputs.append(c)
            self.input_openings.append(r)

        self.prover = ProtocolProver(self.ped, self.messages, self.input_openings)
        self.verifier = ProtocolVerifier(self.ped)

        self.outputs, self.perm_msgs, self.output_openings, self.perm = self.prover.shuffle_and_prove()

    def test_nizk_always_passes(self):
        subset = list(range(len(self.messages)))
        self.assertTrue(
            self.verifier.check(subset, self.inputs, self.input_openings, self.outputs, self.output_openings, self.perm)
        )

    def test_subset_check_random_subsets(self):
        n = len(self.messages)
        for _ in range(5):
            k = random.randint(1, n)
            subset = random.sample(range(n), k)
            self.assertTrue(
                self.verifier.check(subset, self.inputs, self.input_openings, self.outputs, self.output_openings, self.perm)
            )

    def test_zk_respond_produces_valid_check(self):
        subset = [0, 2, 4]
        self.assertTrue(
            self.verifier.check(subset, self.inputs, self.input_openings, self.outputs, self.output_openings, self.perm)
        )

    def test_zkprover_always_passes(self):
        outputs, perm_msgs, output_openings, perm = self.prover.shuffle_and_prove()
        subset = list(range(len(self.messages)))
        ok = self.verifier.check(subset, self.inputs, self.input_openings, outputs, output_openings, perm)
        self.assertTrue(ok)

    def test_cheating_shuffle_fails(self):
        bad_outputs = self.outputs[:]
        inv_perm = invert_permutation(self.perm)
        # pick original index 0 -> find where it ended up
        j = inv_perm[0]
        bad_outputs[j] = (bad_outputs[j] * 5) % self.p
        subset = [0,1]
        self.assertFalse(
            self.verifier.check(subset, self.inputs, self.input_openings, bad_outputs, self.output_openings, self.perm)
        )

if __name__ == "__main__":
    unittest.main()
