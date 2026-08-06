# This will host the state space of the game as well as change state where required. Will also contain dependencies

# Dependencies:
import pygame
import random
from collections import deque
import heapq, itertools

# Game Set-up:
pygame.init()
screen = pygame.display.set_mode((1280,720)) # 1280 x 720 Screen
clock = pygame.time.Clock()
running = True
dt = 0 # delta time in seconds, set before the loop so first-frame key presses don't crash

##############
# Maze Set-up:
##############

MAZE_COLS = 60
MAZE_ROWS = 60
BLOCK_SIZE = 8 # each wall block is 5x5 pixels
MAZE_W = MAZE_COLS * BLOCK_SIZE
MAZE_H = MAZE_ROWS * BLOCK_SIZE

# Side-by-side panels: each agent gets its own maze render, so their
# trails/paths never share a pixel and never need to fight for visibility.
PANEL_GAP = 60
_panels_total_w = MAZE_W * 2 + PANEL_GAP
PANEL1_OFFSET_X = (screen.get_width() - _panels_total_w) // 2
PANEL1_OFFSET_Y = (screen.get_height() - MAZE_H) // 2
PANEL2_OFFSET_X = PANEL1_OFFSET_X + MAZE_W + PANEL_GAP
PANEL2_OFFSET_Y = PANEL1_OFFSET_Y



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
                neighbours.append((nx, ny, dx, dy)) # Nah I dont understand. 
                # We are creating the variables nx & ny, which are x & y values of the top of the stack
                # plus dy and dx respectively which are the possible options in the list we are looping through
                # SO essentially, we are either +/- 2 on x or y amd then appending those options to the frontier?

        if neighbours:
            nx, ny, dx, dy = random.choice(neighbours) #Add wall choosen at random from the frontier list. 
            maze[y + dy // 2][x + dx // 2] = False # knock down the wall between cells
            maze[ny][nx] = False 
            stack.append((nx, ny))
        else:
            stack.pop() #Move onto the next time. Removing this item from the stack/queue. In search we would then put in the closed set but not need for wall gen


    return maze



# Draw the maze to the screen

def draw_maze(screen, maze, block_size, offset_x, offset_y):
    for row_index, row in enumerate(maze):
        for col_index, is_wall in enumerate(row):
            if is_wall:
                rect = pygame.Rect(
                    offset_x + col_index * block_size,
                    offset_y + row_index * block_size,
                    block_size,
                    block_size,
                )
                pygame.draw.rect(screen, "brown", rect)
                pygame.draw.rect(screen, "black", rect, 1)


maze = generate_maze(MAZE_COLS, MAZE_ROWS)


# PICK GOAL STATE FOR PUZZLE

# TODO next: red finish square (x, y) + collision/interactivity with agents.  
goalSet=[]

for row_idx, row in enumerate(maze): # Go through list object
    for col, value in enumerate(row): #  Go through values in each list
        if value is False:
            goalSet.append((col, row_idx)) #Append the possible co-ordinates as a tuple to the list

goalState = random.choice(goalSet) # Pick a random Tuple representing the x, y location of the goal state

goal_x, goal_y = goalState
goal_rect_panel1 = pygame.Rect(
    PANEL1_OFFSET_X + goal_x * BLOCK_SIZE,
    PANEL1_OFFSET_Y + goal_y * BLOCK_SIZE,
    BLOCK_SIZE,
    BLOCK_SIZE
)
goal_rect_panel2 = pygame.Rect(
    PANEL2_OFFSET_X + goal_x * BLOCK_SIZE,
    PANEL2_OFFSET_Y + goal_y * BLOCK_SIZE,
    BLOCK_SIZE,
    BLOCK_SIZE
)



#ALGORITHMS: 


class SearchStrategy: 
    #Constructor
    def search(self,maze, start, goal):
        raise NotImplementedError


###################################
# UNINFORMED SEARCH STRATEGIES
#####################################

class BFS(SearchStrategy):
    def search(self, maze, start, goal):
        frontier = deque([start]) # init frontier set
        prev = {start : None} # Dict Defining where the previous step - could be a set
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
                if 0 <= nx < MAZE_COLS and 0 <= ny < MAZE_ROWS \
                    and not maze[ny][nx] and child not in prev:
                    prev[child] = curr
                    depth[child] = depth[curr] + 1
                    max_depth = max(max_depth, depth[child])
                    frontier.append(child)

        print("Shit Broke Boy") # No path found
        return [], explored, max_depth # No Path

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
    def __init__(self, position, parent = None, cost = 0):
        self.position = position
        self.parent = parent
        self.cost = cost


class UniformCostSearch(SearchStrategy):
    def search(self, maze, start, goal):
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
            if cost > best_cost.get(node.position, float("inf")): #Not sure I get the end of this line
                continue # stale, entry, a cheaper path already won

            for dx, dy in ((0,1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = node.position[0] + dx, node.position[1] + dy
                neighbour = (nx, ny)
                if not (0 <= nx < MAZE_COLS and 0 <= ny < MAZE_ROWS): # Make sure we are in bounds on the maze
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

    def search(self, maze, start, goal):
        depth = 1
        frontier = deque([start]) # Init Frontier Stack
        prev = {start: None}
        explored = []
        search_depth = {start: 0} # tracks true tree depth per cell, for stats only
        max_depth = 0

        while frontier:
            curr = frontier.popleft()
            explored.append(curr)
            if curr == goal:
                return self.reconstruct_DepthLimitedSearch(prev, start, goal), explored, max_depth
            if depth <= 5:
                print("Reached Your Limit Bud!")
                return [], explored, max_depth # Search Cap Reach Search - would be cool to show whole tree explored.

            for dx, dy in ((0,1), (0, -1), (1,0), (-1,0)):
                nx, ny = curr[0] + dx, curr[1] + dy #Expanding Node curr[0] is x value and curr[1] is y value
                child = (nx, ny) #Create Child Nodes
                if 0 <= nx < MAZE_COLS and 0 <= ny < MAZE_ROWS \
                and not maze[ny][nx] and child not in prev:
                    frontier.append(child) # Append to Frontier
                    search_depth[child] = search_depth[curr] + 1
                    max_depth = max(max_depth, search_depth[child])
                    depth += 1

        print("Shit Broke Boy")
        return [], explored, max_depth # Failed Search

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
        frontier = deque([start])
        prev = {start : None} # Could make this a set, if you do not want to re-create path
        depth = {start: 0}
        explored = []
        max_depth = 0

        while frontier:
            curr = frontier.pop() #Changing to pop() so pop happens from Right (end) not popleft (start) is the only structural difference between DFS and BFS
            explored.append(curr)
            if curr == goal:
                return self.reconstructDFS(prev, start, goal), explored, max_depth

            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = curr[0] + dx, curr[1] + dy # This is the line that need to change
                child = (nx, ny)
                if 0<= nx < MAZE_COLS and 0 <= ny < MAZE_ROWS \
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



# Iterative Deepening:


# Best First Search


# Greedy Best First Search


# A* Search

# A* Iterative Deepening


###################################
# ALGORITHM REGISTRY
###################################
# Every selectable strategy goes here as (display_name, class). The
# selection menu and Agent Set-up below read only from this list, so
# adding IDS/A*/Greedy/Best-First later is just adding a line here once
# the class is implemented above.
ALGORITHMS = [
    ("BFS", BFS),
    ("DFS", DFS),
    ("UCS", UniformCostSearch),
    ("DLS", DepthLimitedSearch),
]


##########################
# Agent Generation & Class
##########################

# I want to add a trail to the agent showing the search path explored.
class Agent:

    MOVE_INTERVAL = 0.1     # seconds per step along the final path (~10 cells/sec)
    EXPLORE_INTERVAL = 0.02 # seconds per trail-reveal tick
    EXPLORE_PER_TICK = 4    # explored cells revealed per tick

    def __init__(self, start, strategy, color=None):
        """
        Define the Agent Class - Position, x co-ord, Y co-ord
        """
        self.speed = 3
        self.color = color if color is not None else (
            random.randint(0,255),
            random.randint(0,255),
            random.randint(0,255)
        )

        self.velocity = pygame.Vector2() #Handles Movement

        self.position = start
        self.strategy = strategy
        self.path = [] # Path still to walk - consumed as the agent moves
        self.solution_path = [] # Full found route, kept intact for drawing/stats
        self.solution_depth = 0 # len(solution_path); 0 means no path was found
        self.start = start
        self.explored = [] # Init Empty List for search-order trail
        self.explore_index = 0 # how many explored cells have been revealed so far
        self.explore_timer = 0
        self.move_timer = 0
        self.max_depth = 0 # deepest cell reached during search

    #Planning
    def plan(self, maze, goal):
        self.start = self.position
        self.path, self.explored, self.max_depth = self.strategy.search(
            maze,
            self.position,
            goal
        )
        self.solution_path = list(self.path) # immutable copy - self.path gets popped as we walk
        self.solution_depth = len(self.solution_path)

    #Movement
    def update(self, dt):
        if self.explore_index < len(self.explored):
            # Phase 1: reveal the search trail before moving anywhere
            self.explore_timer += dt
            if self.explore_timer >= self.EXPLORE_INTERVAL:
                self.explore_timer = 0
                self.explore_index = min(
                    self.explore_index + self.EXPLORE_PER_TICK,
                    len(self.explored)
                )
        elif self.path:
            # Phase 2: walk the final reconstructed path
            self.move_timer += dt
            if self.move_timer >= self.MOVE_INTERVAL:
                self.move_timer = 0
                self.position = self.path.pop(0)

    # Drawing the explored-cell trail (search order, revealed progressively)

    def draw_trail(self, surface, offset_x, offset_y):
        # Each agent has its own panel now, so there's no cross-agent overlap
        # to worry about - a plain lighter tint of the agent's own colour is enough.
        trail_color = tuple(min(c + 70, 255) for c in self.color)

        for cx, cy in self.explored[:self.explore_index]:
            rect = pygame.Rect(
                offset_x + cx * BLOCK_SIZE,
                offset_y + cy * BLOCK_SIZE,
                BLOCK_SIZE,
                BLOCK_SIZE
            )
            pygame.draw.rect(surface, trail_color, rect)

    # Drawing the bold, fully-opaque solved route (distinct from the faint exploration trail)

    def draw_path(self, surface, offset_x, offset_y):
        if self.explore_index < len(self.explored):
            return # still revealing the trail - don't spoil the final route yet
        if not self.solution_path:
            return

        def center(cell):
            cx, cy = cell
            return (
                offset_x + cx * BLOCK_SIZE + BLOCK_SIZE // 2,
                offset_y + cy * BLOCK_SIZE + BLOCK_SIZE // 2,
            )

        points = [center(self.start)] + [center(cell) for cell in self.solution_path]
        pygame.draw.lines(surface, self.color, False, points, 4)

    # Drawing the Agent

    def draw(self, surface, offset_x, offset_y):

        x = offset_x + self.position[0] * BLOCK_SIZE
        y = offset_y + self.position[1] * BLOCK_SIZE

        pygame.draw.rect(
            surface,
            self.color,
            (x, y, BLOCK_SIZE, BLOCK_SIZE)
        )



####################
# Algorithm Selection Menu:
######################

def draw_button(surface, rect, text, font, selected):
    pygame.draw.rect(surface, "orange" if selected else "gray30", rect, border_radius=6)
    pygame.draw.rect(surface, "white", rect, 2, border_radius=6)
    label = font.render(text, True, "white")
    surface.blit(label, label.get_rect(center=rect.center))


def run_algorithm_menu(screen, clock, algorithms):
    """Pre-game screen: pick a strategy per agent from ALGORITHMS, click Start Race.
    Returns (agent1_strategy_cls, agent2_strategy_cls)."""
    font = pygame.font.SysFont(None, 28)
    title_font = pygame.font.SysFont(None, 44)

    button_w, button_h, gap = 90, 40, 10
    start_x = 220
    agent1_buttons = [pygame.Rect(start_x + i * (button_w + gap), 220, button_w, button_h)
                       for i in range(len(algorithms))]
    agent2_buttons = [pygame.Rect(start_x + i * (button_w + gap), 320, button_w, button_h)
                       for i in range(len(algorithms))]
    start_button = pygame.Rect(screen.get_width() // 2 - 80, 450, 160, 50)

    agent1_choice = 0
    agent2_choice = min(1, len(algorithms) - 1)

    selecting = True
    while selecting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, rect in enumerate(agent1_buttons):
                    if rect.collidepoint(event.pos):
                        agent1_choice = i
                for i, rect in enumerate(agent2_buttons):
                    if rect.collidepoint(event.pos):
                        agent2_choice = i
                if start_button.collidepoint(event.pos):
                    selecting = False

        screen.fill("purple")

        title = title_font.render("Select Algorithms", True, "white")
        screen.blit(title, title.get_rect(center=(screen.get_width() // 2, 120)))

        screen.blit(font.render("Agent 1:", True, "white"), (start_x - 110, 230))
        for i, (name, _) in enumerate(algorithms):
            draw_button(screen, agent1_buttons[i], name, font, i == agent1_choice)

        screen.blit(font.render("Agent 2:", True, "white"), (start_x - 110, 330))
        for i, (name, _) in enumerate(algorithms):
            draw_button(screen, agent2_buttons[i], name, font, i == agent2_choice)

        draw_button(screen, start_button, "Start Race", font, True)

        pygame.display.flip()
        clock.tick(60)

    return algorithms[agent1_choice][1], algorithms[agent2_choice][1]


def draw_panel_title(surface, agent, offset_x, font, is_winner):
    """Algorithm name centred above an agent's own panel, in that agent's colour."""
    text = type(agent.strategy).__name__
    if is_winner:
        text += "  ★ WINNER"
    label = font.render(text, True, agent.color)
    rect = label.get_rect(midbottom=(offset_x + MAZE_W // 2, PANEL1_OFFSET_Y - 10))
    surface.blit(label, rect)

    if is_winner:
        border = pygame.Rect(offset_x - 4, PANEL1_OFFSET_Y - 4, MAZE_W + 8, MAZE_H + 8)
        pygame.draw.rect(surface, agent.color, border, 3)


def print_results(winner, loser):
    """Console stats dump for both agents once one of them reaches the goal."""
    def stats(agent, label):
        print(f"  {label} - {type(agent.strategy).__name__}")
        print(f"    Nodes explored:      {len(agent.explored)}")
        print(f"    Max search depth:    {agent.max_depth}")
        depth_text = agent.solution_depth if agent.solution_depth else "no path found"
        print(f"    Solution path depth: {depth_text}")

    print("=" * 44)
    print("RACE OVER")
    stats(winner, "WINNER")
    stats(loser, "LOSER")
    print("=" * 44)


def draw_finish_screen(surface, winner, loser, title_font, font):
    """Dimmed overlay shown once the race ends: winner banner + both agents' stats."""
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    surface.blit(overlay, (0, 0))

    cx = surface.get_width() // 2
    y = 130

    title = title_font.render("RACE OVER", True, "white")
    surface.blit(title, title.get_rect(center=(cx, y)))
    y += 60

    winner_label = title_font.render(f"WINNER: {type(winner.strategy).__name__}", True, winner.color)
    surface.blit(winner_label, winner_label.get_rect(center=(cx, y)))
    y += 70

    def stats_block(agent, label, x):
        line_y = y
        header = font.render(f"{label} - {type(agent.strategy).__name__}", True, agent.color)
        surface.blit(header, (x, line_y))
        line_y += 34
        depth_text = agent.solution_depth if agent.solution_depth else "no path found"
        for line in (
            f"Nodes explored:      {len(agent.explored)}",
            f"Max search depth:    {agent.max_depth}",
            f"Solution path depth: {depth_text}",
        ):
            surface.blit(font.render(line, True, "white"), (x, line_y))
            line_y += 28

    stats_block(winner, "WINNER", cx - 420)
    stats_block(loser, "LOSER", cx + 60)


####################
# Agent Set-up:
######################

Agent1Strategy, Agent2Strategy = run_algorithm_menu(screen, clock, ALGORITHMS)
hud_font = pygame.font.SysFont(None, 28)
finish_title_font = pygame.font.SysFont(None, 48)

AGENT1_COLOR = (40, 110, 255) # blue
AGENT2_COLOR = (255, 215, 0)  # yellow

start_cell = random.choice([c for c in goalSet if c != goalState])
agent1 = Agent(start_cell, Agent1Strategy(), color=AGENT1_COLOR)
agent1.plan(maze, goalState)

agent2 = Agent(start_cell, Agent2Strategy(), color=AGENT2_COLOR)
agent2.plan(maze, goalState)

winner = None
loser = None
race_over = False


####################
# Game Loop:
######################


panels = (
    (agent1, PANEL1_OFFSET_X, PANEL1_OFFSET_Y, goal_rect_panel1),
    (agent2, PANEL2_OFFSET_X, PANEL2_OFFSET_Y, goal_rect_panel2),
)

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close the window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Fill the Screen with a Colour to wipe away anything from the last frame
    screen.fill ("purple")

    # Render Game Here -----!!!!

    for agent, offset_x, offset_y, goal_rect in panels:
        draw_maze(screen, maze, BLOCK_SIZE, offset_x, offset_y)
        agent.draw_trail(screen, offset_x, offset_y)
        agent.draw_path(screen, offset_x, offset_y)
        pygame.draw.rect(screen, "red", goal_rect)
        draw_panel_title(screen, agent, offset_x, hud_font, race_over and agent is winner)

    # Update Agents (frozen once the race has been won)
    if not race_over:
        agent1.update(dt)
        agent2.update(dt)

        if agent1.position == goalState:
            winner, loser = agent1, agent2
            race_over = True
        elif agent2.position == goalState:
            winner, loser = agent2, agent1
            race_over = True

        if race_over:
            print_results(winner, loser)

    for agent, offset_x, offset_y, goal_rect in panels:
        agent.draw(screen, offset_x, offset_y)

    if race_over:
        draw_finish_screen(screen, winner, loser, finish_title_font, hud_font)

    # flip() the displat to put your work on screen
    pygame.display.flip()

    # dt is delta time in seconds since last frame, used for framerate independent physics.

    dt = clock.tick(60) / 1000 # 60 FPS

pygame.quit()