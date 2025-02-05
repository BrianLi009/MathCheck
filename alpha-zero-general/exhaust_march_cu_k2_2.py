import operator
import re
import subprocess
import pickle
from pysat.formula import CNF
import time

start_time =  time.time()

order = 19
valid_literals = None
prob = None
march_pos_lit_score_dict = None
current_metric_val = None

org_filename = "constraints_19_c_100000_2_2_0_final.simp"
filename = "tmp.cnf"
edge_vars = order*(order-1)//2 

all_results = {}
all_results_nested = {}

cnf = CNF(from_file=org_filename)
max_metric_val = len(cnf.clauses) # maximum possible value of the metric (unweighted)

cnf.to_file(filename)

# ../PhysicsCheck/gen_cubes/march_cu/march_cu tmp.cnf -o tmp.cubes -d 1 -m 136
result = subprocess.run(['../PhysicsCheck/gen_cubes/march_cu/march_cu', 
                        filename,
                        '-o',
                        'tmp.cubes', 
                        '-d', '1'], capture_output=True, text=True)

output = result.stdout

# two groups enclosed in separate ( and ) bracket
re_out = re.findall(r"alphasat: variable: (\d+), w-left: (\d+.\d+), w-right: (\d+.\d+)", output)
march_pos_lit_score_dict = {int(k):(float(v)+float(w))/2.0 for k,v,w in re_out} # average of the two sides
# all_results.update(march_pos_lit_score_dict) # merge dict

res = None
if len(march_pos_lit_score_dict) == 0:
    unsat_check = re.findall(r"c number of cubes (\d+), including (\d+) refuted leaf", output)
    if len(unsat_check) > 0 and unsat_check[0][0] == unsat_check[0][1] in output:
        assert len(unsat_check) == 1
        res = 0
        print("Unsat!")
    elif "SATISFIABLE" in output:
        res = 1
        print("Sat!")
    else:
        print("Unknown result with empty dict!")
        print(output)
        print("-"*50)

pos_keys = list(march_pos_lit_score_dict.keys())
pos_keys = [ky for ky in pos_keys if ky <= edge_vars]
print("Pos keys: ", pos_keys)
neg_keys = [-k for k in pos_keys]
all_keys = pos_keys + neg_keys

f = open("x.txt", "w")
f.writelines(["a " + str(l) + " 0\n" for l in all_keys])
f.close()

for index, j in enumerate(all_keys):
    all_results_nested[j] = {}

    # ../PhysicsCheck/gen_cubes/march_cu/march_cu tmp.cnf -o tmp.cubes -d 1 -m 136
    myoutput = open(filename, "w")
    _ = subprocess.run(['../PhysicsCheck/gen_cubes/apply.sh', org_filename, "x.txt", str(index)], stdout=myoutput)
    myoutput.close()
    result = subprocess.run(['../PhysicsCheck/gen_cubes/march_cu/march_cu', 
                            filename,
                            '-o',
                            'tmp.cubes', 
                            '-d', '1'], capture_output=True, text=True)

    output = result.stdout

    if index > 3: 
        exit(0)

    continue

    march_pos_lit_score_dict2_out = re.findall(r"alphasat: variable: (\d+), w-left: (\d+.\d+), w-right: (\d+.\d+)", output)
    march_pos_lit_score_dict2 = {int(k):(float(v)+float(w))/2.0 for k,v,w in march_pos_lit_score_dict2_out} # average of the two sides

    res = None
    if len(march_pos_lit_score_dict2) == 0:
        unsat_check = re.findall(r"c number of cubes (\d+), including (\d+) refuted leaf", output)
        if len(unsat_check) > 0 and unsat_check[0][0] == unsat_check[0][1] in output:
            assert len(unsat_check) == 1
            res = 0
            print("Unsat!")
        elif "SATISFIABLE" in output:
            res = 1
            print("Sat!")
        else:
            print("Unknown result with empty dict!")
            print(output)
            print("-"*50)

    if len(march_pos_lit_score_dict2) == 0:
        march_pos_lit_score_dict2[0] = 0.0
    maxv_key2 = max(march_pos_lit_score_dict2.items(), key=operator.itemgetter(1))[0]
    print(j, maxv_key2)
    total_score = march_pos_lit_score_dict[abs(j)] + march_pos_lit_score_dict2[maxv_key2]
    all_results_nested[j][maxv_key2] = total_score

    if frozenset([j, maxv_key2]) in all_results:
        print("Duplicate!")
        print(j, maxv_key2)
        print("Existing val: ", all_results[frozenset([j, maxv_key2])])
        print("New val: ", total_score)
    else:
        all_results[frozenset([j, maxv_key2])] = total_score

print(f"Elapsed time: {int(time.time()-start_time)//60} min {int(time.time()-start_time)%60} sec")

# save dict to pickle file
with open("all_results.pickle", "wb") as f:
    pickle.dump(all_results, f)

with open("all_results_nested.pickle", "wb") as f:
    pickle.dump(all_results_nested, f)

# # load dict from pickle file
# with open("all_results.pickle", "rb") as f:
#     all_results = pickle.load(f)
#     print(all_results)
# 1/0

# print(all_results_nested)

# print(all_results)