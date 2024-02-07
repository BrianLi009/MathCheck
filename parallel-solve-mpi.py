import argparse
import time
import random
import math

parser = argparse.ArgumentParser(description="Approximate digits of Pi using Monte Carlo simulation.")
parser.add_argument("--num-samples", type=int, default=1000000)
parser.add_argument("--parallel", default=False, action="store_true")
parser.add_argument("--distributed", default=False, action="store_true")

SAMPLE_BATCH_SIZE = 100000

def sample(num_samples):
    num_inside = 0
    for _ in range(num_samples):
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        if math.hypot(x, y) <= 1:
            num_inside += 1

    return num_inside

def approximate_pi(num_samples):
    start = time.time()
    num_inside = sample(num_samples)
    print("pi ~= {}".format((4*num_inside)/num_samples))
    print("Finished in: {:.2f}s".format(time.time()-start))

def approximate_pi_parallel(num_samples):
    from multiprocessing import Pool
    pool = Pool()

    start = time.time()
    num_inside = 0
    for result in pool.map(sample, [SAMPLE_BATCH_SIZE for _ in range(num_samples//SAMPLE_BATCH_SIZE)]):
        num_inside += result

    print("pi ~= {}".format((4*num_inside)/num_samples))
    print("Finished in: {:.2f}s".format(time.time()-start))

def approximate_pi_distributed(num_samples):
    from ray.util.multiprocessing import Pool
    pool = Pool()

    start = time.time()
    num_inside = 0
    for result in pool.map(sample, [SAMPLE_BATCH_SIZE for _ in range(num_samples//SAMPLE_BATCH_SIZE)]):
        num_inside += result

    print("pi ~= {}".format((4*num_inside)/num_samples))
    print("Finished in: {:.2f}s".format(time.time()-start))

if __name__ == "__main__":
    args = parser.parse_args()
    if args.parallel:
        print("Estimating Pi using multiprocessing with {} samples...".format(args.num_samples))
        approximate_pi_parallel(args.num_samples)
    elif args.distributed:
        print("Estimating Pi using ray.util.multiprocessing with {} samples...".format(args.num_samples))
        approximate_pi_distributed(args.num_samples)
    else:
        print("Estimating Pi in one process with {} samples...".format(args.num_samples))
        approximate_pi(args.num_samples)