import math
import random
import time

def sample(num_samples):
    num_inside = 0
    for _ in range(num_samples):
        x, y = random.uniform(-1, 1), random.uniform(-1, 1)
        if math.hypot(x, y) <= 1:
            num_inside += 1
    return num_inside

def approximate_pi_parallel(num_samples):
    from multiprocessing.pool import Pool
    pool = Pool()
    
    start = time.time()
    num_inside = 0
    sample_batch_size = 100000
    for result in pool.map(sample, [sample_batch_size for _ in range(num_samples//sample_batch_size)]):
        num_inside += result
        
    print("pi ~= {}".format((4*num_inside)/num_samples))
    print("Finished in: {:.2f}s".format(time.time()-start))