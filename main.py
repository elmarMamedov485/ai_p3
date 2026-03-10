from agent import agent

a = agent(10, 4, 1)

a.current_state = {(1,1): 1, (2,2): 1, (4,4): 1, (5,5):1, (2,1): 1, (4,1): 1, (5,1): 1, (6, 1): 1}
print(a.find_longest_diag(a.current_state, a.side))