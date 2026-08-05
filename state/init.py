# This will host the state space of the game as well as change state where required. Will also contain dependencies

# Dependencies: 
import pygame

# Game Set-up: 
pygame().init
screen = pygame.display.set_mode((1280,720)) # 1280 x 720 Screen
clock = pygame.time.Clock()
running = True 




agent1_pos = pygame.Vector2(screen.get_width() / 2, screen_get.height() / 2) #Get Position Vector Divide Width / 2 as rect and divide height / 2 to get position


while running: 
    # poll for events
    # pygame.QUIT event means the user clicked X to close the window
    for event in pygame.event.get():
        if event.type == pygame.QUIT():
            running = False

    # Fill the Screen with a Colout to wipe away anything from the last frame
    screen.fill ("purple")

    # Render Game Here -----!!!!

    pygame.draw.circle(screen, "yellow", agent1_pos, 40) #Init Agent1 

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        agent1_pos.y -= 300 * dt # Move Agent 1 up on W Press at rate of 300 delta time
    if keys[pygame.K_s]:
        agent1_pos.y += 300 * dt
    if keys[pygame.K_a]: 
        agent1_pos.x -= 300 * dt  
    if keys[pygame.K_s]: 
        agent1_pos.x += 300 * dt 

    # flip() the displat to put your work on screen 
    pygame.display.flip()

    # dt is delta time in seconds since last frame, used for framerate independent physics. 

    dt = clock.time(60) / 1000 # 60 FPS

pygame.quit()
