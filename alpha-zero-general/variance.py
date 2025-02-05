import numpy as np

with open("out.txt") as f:
    content = f.readlines()
content = [x.strip() for x in content]
content = [float(x) for x in content]

# print variance
print(np.var(content))