# This will host the state space of the game as well as change state where required. Will also contain dependencies

# Dependencies:
import pygame
import random

# Game Set-up:
pygame.init()
screen = pygame.display.set_mode((1280,720)) # 1280 x 720 Screen
clock = pygame.time.Clock()
running = True
dt = 0 # delta time in seconds, set before the loop so first-frame key presses don't crash


# Maze Set-up:
MAZE_COLS = 60
MAZE_ROWS = 60
BLOCK_SIZE = 8 # each wall block is 5x5 pixels
MAZE_OFFSET_X = (screen.get_width() - MAZE_COLS * BLOCK_SIZE) // 2
MAZE_OFFSET_Y = (screen.get_height() - MAZE_ROWS * BLOCK_SIZE) // 2


def generate_maze(cols, rows):
    # True = wall, False = open path. Carves a perfect maze (dead ends included)
    # via randomized depth-first backtracking, starting from cell (1, 1).
    maze = [[True] * cols for _ in range(rows)]

    # WTF IS the _ ? 

    start = (1, 1)
    maze[start[1]][start[0]] = False # List of Lists - 2D Array 1 = Wall 0 = Path
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
        if maze[row][col] is False:
            goalSet.append([row][col]) #Append the possible co-ordinates as a tuple to the list

goalState = random.choice(goalSet) # Pick a random Tuple representing the x, y location of the goal state

# Agent Generation & Class
# I want to add a trail to the agent showing the search path explored. 
class Agent:

    def __init__(self, start, strategy):
        """
        Define the Agent Class - Position, x co-ord, Y co-ord
        """
        self.speed = 3
        self.color = (
            random.randint(0,255),
            random.randint(0,255),
            random.randint(0,255)
        )

        self.velocity = pygame.Vector2() #Handles Movement

        self.position = start
        self.strategy = strategy
        self.path = [] # Init Empty List for path

    #Planning
    def plan(self, maze, goal):
        self.path = self.strategy(
            maze, 
            self.position, 
            goal
        )

    #Movement 
    def update(self):
        if self.path:
            self.position = self.path.pop(0)

    # Drawing the Agent

    def draw(self, surface):

        x = self.position[0] * BLOCK_SIZE
        y = self.position[1] * BLOCK_SIZE

        pygame.draw.rect(
            surface, 
            self.colour, 
            (x, y, BLOCK_SIZE, BLOCK_SIZE)
        )

# Game Loop:

while running: 
    # poll for events
    # pygame.QUIT event means the user clicked X to close the window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Fill the Screen with a Colout to wipe away anything from the last frame
    screen.fill ("purple")

    # Render Game Here -----!!!!

    draw_maze(screen, maze, BLOCK_SIZE, MAZE_OFFSET_X, MAZE_OFFSET_Y)
    print(type(maze))
    print(maze)

    # Print Goal State on Maze
    redSquare = pygame.rect(goalState[0], goalState[1], BLOCK_SIZE, BLOCK_SIZE) 
        



    # TODO next: race logic - first agent to reach it wins, print stats (nodes expanded, max depth, etc).
    if agent1.pos == redSquare:
        winner = True
        #print_results() - TBC
    if agent2.pos == redSquare:
        winner = True
        #print_results()
    
    
    
    # Draw Agents
    #agent1 = Agent() #Need to provide start and strategy 
    #agent2 = Agent()
    
    
    
    #pygame.draw.circle(screen, "yellow", agent1_pos, 3) #Init Agent1

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        agent1_pos.y -= 300 * dt # Move Agent 1 up on W Press at rate of 300 delta time
    if keys[pygame.K_s]:
        agent1_pos.y += 300 * dt
    if keys[pygame.K_a]: 
        agent1_pos.x -= 300 * dt  
    if keys[pygame.K_d]: 
        agent1_pos.x += 300 * dt 

    # flip() the displat to put your work on screen 
    pygame.display.flip()

    # dt is delta time in seconds since last frame, used for framerate independent physics. 

    dt = clock.tick(60) / 1000 # 60 FPS

pygame.quit()




#ALGORITHMS: 

# Create the Graph Class that will be used for each algo

class SearchStrategy: 
    #Constructor
    def search(self,maze, start, goal):
        raise NotImplementedError


# For each algo implement as follows

# class BFS(SearchStrategy):


###################################
# UNINFORMED SEARCH STRATEGIES
#####################################


# Bredth-First Search
    """
    Still need to implement Goal State Test and test
    Need to re-write the function so it take in an inital position,
    Goal Test
    """
    def BredthFirstSearch(self, s, goal):
        #Initalise Visited List with Lenght of all node of the graph and set all to False (not visited)
        visited = [False] * (max(self.graph) + 1)

        # Initalise Queue
        queue = [] 

        # Maek the root as visited and put it in the queue for expansion
        queue.append(s) # s = source/root
        visited[s] = True

        # Create recursive call to expand the queue and add nodes to visted untill finished/goal test
        while queue: 
            s = queue.pop(0) # Remove a node from the queue and print it
            print(s, end= " ")

            # Get all children of the node s (which is being expanded).
            # If a child node has not been visited, then mark it visited and put it in the queue

            for i in self.graph[s]:
                if not visited[i]:
                    queue.append(i)
                    visited[i] = True


# Uniform Cost Search
    def UniformCostSearch(): 
        """
        UCS expands the node n with the lowest path cost g(n)
        This is done by storing the frontier as a priority queue order by g.
        Two other difference between BFS and UCS
        1. Goal Test is applied to a node when it is selected for expansion rather than when it is selected for expansion 
        2. A test is added in case a better path is found to a node currently in the frontier. 
        """

        