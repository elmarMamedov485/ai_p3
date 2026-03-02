from agent import agent

a = agent(3, 3, 1)

a.current_state = {(1, 1): 0, (2, 1) : 1, (3, 1):1, (2,2) : 0, (3, 2) : 1, (1,3): 0}

print(a.alpha_beta())