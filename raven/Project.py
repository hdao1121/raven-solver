from raven.Problem import Problem
from src.Agent import Agent
def solve():
    sets=[]
    with open("ProblemList.txt") as r:
        for line in r:
            line = line.rstrip()
            problem = Problem(line, '2x2')
            sets.append(problem)
    agent = Agent()
    for problem in sets:
        agent.Solve(problem)

def main():
    solve()

if __name__ == "__main__":
    main()