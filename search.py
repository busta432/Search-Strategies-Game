# Maze generation and search-strategy implementations, kept free of any
# pygame dependency so they can be imported headlessly by tests and the
# benchmark script (importing init.py directly would open a game window).

import random
import heapq
import itertools
from collections import deque


# Generate the Boolean Matrix that represents the maze

def generate_maze(cols, rows):
    # True = wall, False = open path. Carves a perfect maze (dead ends included)
    # via randomized depth-first backtracking, starting from cell (1, 1).
    maze = [[True] * cols for _ in range(rows)]

    start = (1, 1)
    maze[start[1]][start[0]] = False # 2D Array 1 = Wall 0 = Path
    stack = [start] # List containing the root node (1,1)

    while stack:
        x, y = stack[-1] #Last element in the stack
        neighbours = [] # Initalise Empty Frontier
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            nx, ny = x + dx, y + dy
            if 1 <= nx < cols - 1 and 1 <= ny < rows - 1 and maze[ny][nx]:
                neighbours.append((nx, ny, dx, dy))

        if neighbours:
            nx, ny, dx, dy = random.choice(neighbours) #Add wall choosen at random from the frontier list.
            maze[y + dy // 2][x + dx // 2] = False # knock down the wall between cells
            maze[ny][nx] = False
            stack.append((nx, ny))
        else:
            stack.pop() #Move onto the next time. Removing this item from the stack/queue.

    return maze


# Braid the perfect maze: a randomized-DFS carve leaves a spanning tree, so
# there's exactly one route between any two cells. Knock down a random
# subset of the remaining inner walls to add loops, so multiple different-
# length routes actually exist for a search strategy to choose between.

def add_loops(maze, cols, rows, loop_chance):
    for y in range(1, rows - 1, 2):
        for x in range(1, cols - 1, 2):
            for dx, dy in ((2, 0), (0, 2)): # only right/down - each wall considered once
                nx, ny = x + dx, y + dy
                if nx >= cols - 1 or ny >= rows - 1:
                    continue
                wx, wy = x + dx // 2, y + dy // 2
                if maze[wy][wx] and random.random() < loop_chance:
                    maze[wy][wx] = False # open the wall between the two rooms
    return maze


#ALGORITHMS:


class SearchStrategy:
    #Constructor
    def search(self, maze, start, goal):
        raise NotImplementedError


###################################
# UNINFORMED SEARCH STRATEGIES
#####################################

class BFS(SearchStrategy):
    def search(self, maze, start, goal):
        rows, cols = len(maze), len(maze[0])
        frontier = deque([start]) # init frontier set
        prev = {start: None} # Dict Defining where the previous step - could be a set
        depth = {start: 0} # tracks how many steps deep each discovered cell is
        explored = []
        max_depth = 0

        while frontier: #The recurrsive loop
            curr = frontier.popleft() #Take the First Item in the List (Leftmost)
            explored.append(curr)
            if curr == goal:
                return self.reconstruct_path(prev, start, goal), explored, max_depth #Return how we got to the goal

            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): #Expand all possible options for child node (move up/down ( +/- 1 dy) & move left/right (+// 1 dx))
                nx, ny = curr[0] + dx, curr[1] + dy
                child = (nx, ny)
                if 0 <= nx < cols and 0 <= ny < rows \
                    and not maze[ny][nx] and child not in prev:
                    prev[child] = curr
                    depth[child] = depth[curr] + 1
                    max_depth = max(max_depth, depth[child])
                    frontier.append(child)

        return [], explored, max_depth # No Path found

    def reconstruct_path(self, prev, start, goal):
        if goal not in prev:
            return []
        path = []
        node = goal
        while node != start:
            path.append(node)
            node = prev[node]
        path.reverse()
        return path

# Uniform Cost Search

class Node:
    def __init__(self, position, parent=None, cost=0):
        self.position = position
        self.parent = parent
        self.cost = cost


class UniformCostSearch(SearchStrategy):
    def search(self, maze, start, goal):
        rows, cols = len(maze), len(maze[0])
        counter = itertools.count()
        frontier = [(0, next(counter), Node(start, None, 0))]
        best_cost = {start: 0}
        explored = []
        max_depth = 0

        while frontier:
            cost, _, node = heapq.heappop(frontier)
            explored.append(node.position)
            max_depth = max(max_depth, node.cost) # uniform step cost -> cost doubles as depth
            if node.position == goal:
                return self.reconstruct_UCS(node), explored, max_depth
            if cost > best_cost.get(node.position, float("inf")):
                continue # stale entry, a cheaper path already won

            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = node.position[0] + dx, node.position[1] + dy
                neighbour = (nx, ny)
                if not (0 <= nx < cols and 0 <= ny < rows): # Make sure we are in bounds on the maze
                    continue
                if maze[ny][nx]:
                    continue
                new_cost = node.cost + 1
                if new_cost < best_cost.get(neighbour, float("inf")):
                    best_cost[neighbour] = new_cost
                    heapq.heappush(frontier, (new_cost, next(counter), Node(neighbour, node, new_cost)))

        return [], explored, max_depth # No Path found

    def reconstruct_UCS(self, node):
        path = []
        while node.parent is not None:
            path.append(node.position)
            node = node.parent
        path.reverse()
        return path


# Depth-Limited Search

class DepthLimitedSearch(SearchStrategy):
    def __init__(self, limit=100):
        self.limit = limit # deepest a branch may go before it's cut off

    def search(self, maze, start, goal):
        rows, cols = len(maze), len(maze[0])
        frontier = deque([start]) # Init Frontier Stack
        prev = {start: None}
        explored = []
        search_depth = {start: 0} # tracks true tree depth per cell
        max_depth = 0

        while frontier:
            curr = frontier.popleft()
            explored.append(curr)
            if curr == goal:
                return self.reconstruct_DepthLimitedSearch(prev, start, goal), explored, max_depth
            if search_depth[curr] >= self.limit:
                continue # at the depth cap - don't expand this node's children

            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = curr[0] + dx, curr[1] + dy #Expanding Node curr[0] is x value and curr[1] is y value
                child = (nx, ny) #Create Child Nodes
                if 0 <= nx < cols and 0 <= ny < rows \
                and not maze[ny][nx] and child not in prev:
                    prev[child] = curr
                    search_depth[child] = search_depth[curr] + 1
                    max_depth = max(max_depth, search_depth[child])
                    frontier.append(child) # Append to Frontier

        return [], explored, max_depth # Failed Search - goal unreachable within the depth limit

    def reconstruct_DepthLimitedSearch(self, prev, start, goal):
        if goal not in prev:
            return []
        path = []
        node = goal
        while node != start:
            path.append(node)
            node = prev[node]
        path.reverse()
        return path


# Depth First Search:

class DFS(SearchStrategy):
    def search(self, maze, start, goal):
        rows, cols = len(maze), len(maze[0])
        frontier = deque([start])
        prev = {start: None} # Could make this a set, if you do not want to re-create path
        depth = {start: 0}
        explored = []
        max_depth = 0

        while frontier:
            curr = frontier.pop() #Changing to pop() so pop happens from Right (end) not popleft (start) is the only structural difference between DFS and BFS
            explored.append(curr)
            if curr == goal:
                return self.reconstructDFS(prev, start, goal), explored, max_depth

            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = curr[0] + dx, curr[1] + dy
                child = (nx, ny)
                if 0 <= nx < cols and 0 <= ny < rows \
                and not maze[ny][nx] and child not in prev:
                    prev[child] = curr
                    depth[child] = depth[curr] + 1
                    max_depth = max(max_depth, depth[child])
                    frontier.append(child)

        return [], explored, max_depth # Failed to find path

    def reconstructDFS(self, prev, start, goal):
        if goal not in prev:
            return [] #Fail?
        path = []
        node = goal
        while node != start:
            path.append(node)
            node = prev[node]
        path.reverse()
        return path


# Iterative Deepening

class IterativeDeepening(SearchStrategy):
    def search(self, maze, start, goal):
        rows, cols = len(maze), len(maze[0])
        explored = []   # accumulated across every depth-limit pass, for stats/trail
        max_depth = 0

        for limit in itertools.count():
            # Fresh DFS state each pass - a bigger limit can re-open branches
            # that got cut off last time, so nothing carries over.
            frontier = deque([start])
            prev = {start: None}
            depth = {start: 0}
            cutoff_hit = False # did we stop expanding anything purely due to the limit?

            while frontier:
                curr = frontier.pop() # DFS: pop from the right (stack behaviour)
                explored.append(curr)
                max_depth = max(max_depth, depth[curr])

                if curr == goal:
                    return self.reconstuct_ID(prev, start, goal), explored, max_depth

                if depth[curr] == limit:
                    cutoff_hit = True
                    continue # at the limit - don't expand this node's children

                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nx, ny = curr[0] + dx, curr[1] + dy
                    child = (nx, ny)
                    if 0 <= nx < cols and 0 <= ny < rows and not maze[ny][nx]:
                        # Once the maze has loops, DFS can reach the same cell
                        # by a longer route before a shorter one - a plain
                        # "child not in prev" guard would lock that in
                        # permanently and break depth-optimality. Only skip
                        # the child if we already have an equal-or-shorter
                        # route to it (mirrors the best_cost pattern in
                        # UniformCostSearch/AStar).
                        new_depth = depth[curr] + 1
                        if new_depth < depth.get(child, float("inf")):
                            prev[child] = curr
                            depth[child] = new_depth
                            frontier.append(child)

            if not cutoff_hit:
                # This pass explored everything reachable and never hit the
                # limit - a deeper limit won't find anything new either.
                return [], explored, max_depth # Failed Search

    def reconstuct_ID(self, prev, start, goal):
        if goal not in prev:
            return []
        path = []
        node = goal
        while node != start:
            path.append(node)
            node = prev[node]
        path.reverse()
        return path


###################
# INFORMED SEARCH
###################

# Greedy Best First Search
# h(n) - L1 (Manhattan) distance to goal, path cost ignored entirely

class BestFirst(SearchStrategy):
    def search(self, maze, start, goal):
        rows, cols = len(maze), len(maze[0])
        counter = itertools.count()
        frontier = [(self.manhattan(start, goal), next(counter), Node(start, None, 0))]
        visited = {start}
        explored = []
        max_depth = 0

        while frontier:
            _, _, node = heapq.heappop(frontier) #Pop the smallest item off the heap.
            explored.append(node.position)
            max_depth = max(max_depth, node.cost) # node.cost tracks depth here, not path cost - not used in priority
            if node.position == goal:
                return self.reconstruct_BestFirst(node), explored, max_depth

            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = node.position[0] + dx, node.position[1] + dy
                neighbour = (nx, ny)
                if not (0 <= nx < cols and 0 <= ny < rows):
                    continue
                if maze[ny][nx] or neighbour in visited:
                    continue
                visited.add(neighbour)
                priority = self.manhattan(neighbour, goal) # greedy: rank purely on h(n), ignore path cost so far
                heapq.heappush(frontier, (priority, next(counter), Node(neighbour, node, node.cost + 1)))

        return [], explored, max_depth # Failed Search

    def manhattan(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def reconstruct_BestFirst(self, node):
        path = []
        while node.parent is not None:
            path.append(node.position)
            node = node.parent
        path.reverse()
        return path


# A* Search
# f(n) = g(n) + h(n) - path cost so far plus Manhattan distance to goal.
# Uses the same best_cost/stale-entry pattern as UniformCostSearch (rather
# than BestFirst's simple visited set) so a cheaper path discovered later
# can still replace a costlier one already on the frontier.

class AStar(SearchStrategy):
    def search(self, maze, start, goal):
        rows, cols = len(maze), len(maze[0])
        counter = itertools.count()
        frontier = [(self.manhattan(start, goal), next(counter), Node(start, None, 0))]
        best_cost = {start: 0}
        explored = []
        max_depth = 0

        while frontier:
            _, _, node = heapq.heappop(frontier)
            explored.append(node.position)
            max_depth = max(max_depth, node.cost)
            if node.position == goal:
                return self.reconstruct_AStar(node), explored, max_depth
            if node.cost > best_cost.get(node.position, float("inf")):
                continue # stale entry, a cheaper path already won

            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = node.position[0] + dx, node.position[1] + dy
                child = (nx, ny)
                if not (0 <= nx < cols and 0 <= ny < rows):
                    continue
                if maze[ny][nx]:
                    continue
                new_cost = node.cost + 1
                if new_cost < best_cost.get(child, float("inf")):
                    best_cost[child] = new_cost
                    priority = new_cost + self.manhattan(child, goal)
                    heapq.heappush(frontier, (priority, next(counter), Node(child, node, new_cost)))

        return [], explored, max_depth

    def manhattan(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def reconstruct_AStar(self, node):
        path = []
        while node.parent is not None:
            path.append(node.position)
            node = node.parent
        path.reverse()
        return path


###################################
# ALGORITHM REGISTRY
###################################
# Every selectable strategy goes here as (display_name, class). The
# selection menu and Agent Set-up in init.py read only from this list, so
# adding a new strategy later is just adding a line here once the class is
# implemented above.
ALGORITHMS = [
    ("BFS", BFS),
    ("DFS", DFS),
    ("UCS", UniformCostSearch),
    ("DLS", DepthLimitedSearch),
    ("ID", IterativeDeepening),
    ("Greedy", BestFirst),
    ("A*", AStar),
]
