#timing_fullprotocol.py
import random
import time
import csv
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

def run_protocol_once():
    p = 208351617316091241234326746312124448251235562226470491514186331217050270460481
    g = 2
    h = 3
    ped = Pedersen(p, g, h)

    messages = [5, 15, 25, 35, 45]
    inputs = []
    input_openings = []

    start = time.perf_counter()
    for w in messages:
        c, r = ped.commit(w)
        inputs.append(c)
        input_openings.append(r)
    pedersen_time = time.perf_counter() - start

    prover = ProtocolProver(ped, messages, input_openings)
    verifier = ProtocolVerifier(ped)

    start = time.perf_counter()
    outputs, perm_msgs, output_openings, perm = prover.shuffle_and_prove()
    shuffle_time = time.perf_counter() - start

    subset = list(range(len(messages)))
    start = time.perf_counter()
    result = verifier.check(subset, inputs, input_openings, outputs, output_openings, perm)
    check_time = time.perf_counter() - start

    return pedersen_time, shuffle_time, check_time, result

def main():
    NUM_RUNS = 100
    timings = []
    all_passed = True

    for _ in range(NUM_RUNS):
        ped_t, shuf_t, chk_t, result = run_protocol_once()
        timings.append((
            ped_t * 1e3,   # convert to milliseconds
            shuf_t * 1e3,
            chk_t * 1e3
        ))
        all_passed &= result

    # Write all timings to CSV
    with open("timing_results.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["PedersenCommit(ms)", "ShuffleAndProve(ms)", "SubsetCheck(ms)"])
        writer.writerows(timings)

    # Compute and print averages
    avg_ped = sum(t[0] for t in timings) / NUM_RUNS
    avg_shuf = sum(t[1] for t in timings) / NUM_RUNS
    avg_chk = sum(t[2] for t in timings) / NUM_RUNS

    print(f"[Average Timing over {NUM_RUNS} runs]")
    print(f"  Pedersen Commitments: {avg_ped:.3f} ms")
    print(f"  Shuffle and Prove:    {avg_shuf:.3f} ms")
    print(f"  Subset Check:         {avg_chk:.3f} ms")
    print(f"[Result] All subset checks passed: {all_passed}")

if __name__ == "__main__":
    main()
