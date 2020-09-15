from tqdm import tqdm
with tqdm(total=10) as pbar:
    for i in range(100000000):
    	if i % 10000000 == 0:
        	pbar.update()