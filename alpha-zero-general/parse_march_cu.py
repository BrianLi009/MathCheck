import re
import subprocess

def march_metrics(board=None):
    # board cnf -> file
    # use that file name
    # TODO: file saving might cause issue with code parallelization
    filename = "constraints_17_c_100000_2_2_0_final.simp"   
    edge_vars = 136 # self.order*(self.order-1)//2 

    result = subprocess.run(['../PhysicsCheck/gen_cubes/march_cu/march_cu', 
                            filename,
                            '-o',
                            'mcts_logs/tmp.cubes', 
                            '-d', '1', '-m', str(edge_vars)], capture_output=True, text=True)
    output = result.stdout

    # print(output)

    # two groups enclosed in separate ( and ) bracket
    march_var_score_dict = dict(re.findall(r"alphasat: variable (\d+) with score (\d+)", output))
    march_var_score_dict = {int(k):int(v) for k,v in march_var_score_dict.items()}

    # [best literal with sign, node, diff of the selected literal]
    march_var_node_score_list = list(map(int, re.findall(r"selected (\d+) at (\d+) with diff (\d+)", output)[0]))

    # print(march_var_score_dict)
    # print(march_var_node_score_list)

    valid_literals = list(march_var_score_dict.keys())
    prob = [0 for _ in range(edge_vars*2+1)]
    for l in valid_literals:
        prob[l] = march_var_score_dict[l]
    
    prob = [p/sum(prob) for p in prob]
    
    # print(prob)
    # print(valid_literals)

march_metrics()

# from pysat.formula import CNF

# cnf = CNF(from_file="test.cnf")
# cnf.append([-1, 2, 3, 4])
# cnf.append([-2, 3, 4])

# cnf.to_file("test2.cnf")
