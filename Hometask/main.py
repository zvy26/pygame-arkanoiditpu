import pygame
import sys
import random
import math
from game_objects import Paddle, Ball, Brick, PowerUp, Laser, Particle, Firework

# --- Level Setup ---
LEVELS = [
    [
        "XXXXXXXXXX",
        "X        X",
        "X XXXXX  X",
        "X        X",
        "XXXXXXXXXX",
    ],
    [
        "XXXXXXXXXX",
        "X        X",
        "X XXXX   X",
        "X   XX   X",
        "XXXXXXXXXX",
    ],
    [
        "X  X  X  X",
        " XX XX XX ",
        "XXXXXXXXXX",
        " XX XX XX ",
        "X  X  X  X",
    ],
    [
        "XXXXXXXXXX",
        "X        X",
        "X X  X X X",
        "X  XX  XX ",
        "XXXXXXXXXX",
    ],
]
current_level = 0

def load_level(idx):
    bricks = []
    pattern = LEVELS[idx]
    brick_width = screen_width // len(pattern[0])
    brick_height = 20
    for row, line in enumerate(pattern):
        for col, ch in enumerate(line):
            if ch == "X":
                x = col * brick_width
                y = row * (brick_height + 5) + 50
                color = BRICK_COLORS[row % len(BRICK_COLORS)]
                bricks.append(Brick(x, y, brick_width - 5, brick_height, color))
    return bricks

# -- General Setup --
pygame.init()
pygame.mixer.init()
clock = pygame.time.Clock()

# -- Screen Setup --
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("PyGame Arkanoid")

# -- Colors --
BG_COLOR = pygame.Color('grey12')
BRICK_COLORS = [(178, 34, 34), (255, 165, 0), (255, 215, 0), (50, 205, 50)]

# -- Font Setup --
# !!! PHASE: TITLE SCREEN !!!
title_font = pygame.font.Font(None, 70)
# !!! END PHASE: TITLE SCREEN !!!
game_font = pygame.font.Font(None, 40)
message_font = pygame.font.Font(None, 30)

# -- Sound Setup --
try:
    bounce_sound = pygame.mixer.Sound('bounce.wav')
    brick_break_sound = pygame.mixer.Sound('brick_break.wav')
    game_over_sound = pygame.mixer.Sound('game_over.wav')
    laser_sound = pygame.mixer.Sound('laser.wav')
except pygame.error as e:
    print(f"Warning: Sound file not found. {e}")
    class DummySound:
        def play(self): pass
    bounce_sound, brick_break_sound, game_over_sound, laser_sound = DummySound(), DummySound(), DummySound(), DummySound()

# -- Game Objects --
paddle = Paddle(screen_width, screen_height)
ball = Ball(screen_width, screen_height)
balls = [ball]

# Apply base speed from difficulty
# --- Pause flag ---
paused = False

# --- Difficulty settings ---
DIFFICULTIES = {
    'Easy':   {'Attempts': 5, 'speed': 4, 'powerup_rate': 0.5},
    'Normal': {'Attempts': 3, 'speed': 6, 'powerup_rate': 0.3},
    'Hard':   {'Attempts': 1, 'speed': 12, 'powerup_rate': 0.1},
}
difficulty = 'Normal'
powerup_rate = DIFFICULTIES[difficulty]['powerup_rate']

for b in balls:
    b.base_speed = DIFFICULTIES[difficulty]['speed']
    b.reset()

bricks = load_level(current_level)
power_ups = []
lasers = []
laser_cooldown = 0
particles = []
fireworks = []

# --- Game Variables ---
# !!! PHASE: TITLE SCREEN !!!
# The game now starts on the title screen
game_state = 'title_screen' 
# !!! END PHASE: TITLE SCREEN !!!
points = 0
Attempts = DIFFICULTIES[difficulty]['Attempts']
display_message = ""
message_timer = 0
firework_timer = 0


# -- Main Game Loop --
while True:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            # !!! PHASE: TITLE SCREEN !!!
            if event.key == pygame.K_SPACE:
                # If on title screen, start the game
                if game_state == 'title_screen':
                    game_state = 'playing'
                # If game is over, go back to title screen
                elif game_state in ['game_over', 'you_win']:
                    paddle.reset()
                    for b in balls:
                        b.reset()
                    # Reset balls
                    new_ball = Ball(screen_width, screen_height)
                    balls = [new_ball]
                    # Reset level
                    bricks = load_level(current_level)
                    points = 0
                    Attempts = DIFFICULTIES[difficulty]['Attempts']
                    powerup_rate = DIFFICULTIES[difficulty]['powerup_rate']
                    for b in balls:
                        b.base_speed = DIFFICULTIES[difficulty]['speed']
                        b.reset()
                    power_ups.clear()
                    lasers.clear()
                    particles.clear()
                    fireworks.clear()
                    game_state = 'title_screen'
                # Launch glued ball
                else:
                    for b in balls:
                        if b.is_glued:
                            b.is_glued = False
            elif event.key == pygame.K_ESCAPE and game_state == 'playing':
                paused = not paused
            elif event.key == pygame.K_UP and paddle.has_laser and laser_cooldown <= 0:
                # Fire lasers on key press
                left_x = paddle.rect.left + 10
                right_x = paddle.rect.right - 10
                lasers.append(Laser(left_x, paddle.rect.top))
                lasers.append(Laser(right_x, paddle.rect.top))
                laser_sound.play()
                laser_cooldown = 10
            # Start next level from transition screen
            if game_state == 'level_transition' and event.key == pygame.K_SPACE:
                # Load next level
                bricks = load_level(current_level)
                # Reset paddle and balls
                paddle.reset()
                new_ball = Ball(screen_width, screen_height)
                new_ball.base_speed = DIFFICULTIES[difficulty]['speed']
                balls = [new_ball]
                # Back to playing
                game_state = 'playing'
            # Difficulty selection on title screen
            if game_state == 'title_screen':
                if event.key == pygame.K_1:
                    difficulty = 'Easy'
                elif event.key == pygame.K_2:
                    difficulty = 'Normal'
                elif event.key == pygame.K_3:
                    difficulty = 'Hard'
                # Update Attempts, powerup_rate, and ball speed when changed
                Attempts = DIFFICULTIES[difficulty]['Attempts']
                powerup_rate = DIFFICULTIES[difficulty]['powerup_rate']
                for b in balls:
                    b.base_speed = DIFFICULTIES[difficulty]['speed']
            # !!! END PHASE: TITLE SCREEN !!!

    # --- Drawing and Updating based on Game State ---
    screen.fill(BG_COLOR)

    # !!! PHASE: TITLE SCREEN !!!
    if game_state == 'title_screen':
        # Draw the title
        title_surface = title_font.render("ARKANOID", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(screen_width / 2, screen_height / 2 - 50))
        screen.blit(title_surface, title_rect)
        
        # Draw the start message
        start_surface = game_font.render("Press SPACE to Start", True, (255, 255, 255))
        start_rect = start_surface.get_rect(center=(screen_width / 2, screen_height / 2 + 20))
        screen.blit(start_surface, start_rect)

        diff_surface = game_font.render(f"1-Easy  2-Normal  3-Hard (Current: {difficulty})", True, (255, 255, 255))
        diff_rect = diff_surface.get_rect(center=(screen_width/2, screen_height/2 + 60))
        screen.blit(diff_surface, diff_rect)

    elif game_state == 'level_transition':
        screen.fill(BG_COLOR)
        level_surf = game_font.render(f"Уровень {current_level+1}", True, (255, 255, 255))
        level_rect = level_surf.get_rect(center=(screen_width/2, screen_height/2 - 20))
        screen.blit(level_surf, level_rect)

        cont_surf = game_font.render("Нажмите SPACE для начала", True, (255, 255, 255))
        cont_rect = cont_surf.get_rect(center=(screen_width/2, screen_height/2 + 20))
        screen.blit(cont_surf, cont_rect)

        pygame.display.flip()
        clock.tick(60)
        continue

    elif game_state == 'playing':
        # Pause handling: if paused, display pause screen
        if paused:
            screen.fill(BG_COLOR)
            pause_surf = game_font.render("PAUSED - Press ESC to resume", True, (255, 255, 255))
            pause_rect = pause_surf.get_rect(center=(screen_width/2, screen_height/2))
            screen.blit(pause_surf, pause_rect)
            pygame.display.flip()
            clock.tick(60)
            continue
        # --- Update all game objects ---
        paddle.update()
        keys = pygame.key.get_pressed()

        # Laser firing while Up Arrow is held
        if paddle.has_laser and keys[pygame.K_UP] and laser_cooldown <= 0:
            # Fire from paddle edges
            left_x = paddle.rect.left + 10
            right_x = paddle.rect.right - 10
            lasers.append(Laser(left_x, paddle.rect.top))
            lasers.append(Laser(right_x, paddle.rect.top))
            laser_sound.play()
            laser_cooldown = 10  # cooldown in frames

        if laser_cooldown > 0:
            laser_cooldown -= 1

        for ball in balls[:]:
            ball_status, collision_object = ball.update(paddle, keys[pygame.K_SPACE])

            if ball_status == 'lost':
                balls.remove(ball)
                if not balls:
                    Attempts -= 1
                    if Attempts <= 0:
                        # On game over, reset all and go to title screen
                        game_over_sound.play()
                        # Reset paddle and balls
                        paddle.reset()
                        # Reset balls
                        new_ball = Ball(screen_width, screen_height)
                        balls = [new_ball]
                        # Reset level, bricks, points, Attempts
                        current_level = 0
                        bricks = load_level(current_level)
                        points = 0
                        Attempts = DIFFICULTIES[difficulty]['Attempts']
                        powerup_rate = DIFFICULTIES[difficulty]['powerup_rate']
                        # Clear effects
                        power_ups.clear()
                        lasers.clear()
                        particles.clear()
                        fireworks.clear()
                        # Back to title screen
                        game_state = 'title_screen'
                        continue
                    else:
                        new_ball = Ball(screen_width, screen_height)
                        # Apply difficulty speed
                        new_ball.base_speed = DIFFICULTIES[difficulty]['speed']
                        balls = [new_ball]
                        new_ball.reset()
                        paddle.reset()
            elif collision_object in ['wall', 'paddle']:
                bounce_sound.play()
                for _ in range(5):
                    particles.append(Particle(ball.rect.centerx, ball.rect.centery, (255, 255, 0), 1, 3, 1, 3, 0))

        for brick in bricks[:]:
            for ball in balls:
                if ball.rect.colliderect(brick.rect):
                    ball.speed_y *= -1
                    for _ in range(15):
                        particles.append(Particle(brick.rect.centerx, brick.rect.centery, brick.color, 1, 4, 1, 4, 0.05))
                    bricks.remove(brick)
                    points += 10
                    brick_break_sound.play()
                    if random.random() < powerup_rate:
                        power_up_type = random.choice(['laser', 'glue', 'slow', 'expand', 'multiball', 'speed'])
                        power_up = PowerUp(brick.rect.centerx, brick.rect.centery, power_up_type)
                        power_ups.append(power_up)
                    break
        
        for power_up in power_ups[:]:
            power_up.update()
            if power_up.rect.top > screen_height:
                power_ups.remove(power_up)
            elif paddle.rect.colliderect(power_up.rect):
                display_message = power_up.PROPERTIES[power_up.type]['message']
                message_timer = 120
                if power_up.type in ['laser', 'glue', 'expand', 'speed']:
                    paddle.activate_power_up(power_up.type)
                elif power_up.type == 'slow':
                    for ball in balls:
                        ball.activate_power_up(power_up.type)
                elif power_up.type == 'multiball':
                    # Spawn an extra ball at current position
                    new_ball = Ball(screen_width, screen_height)
                    # Apply difficulty speed
                    new_ball.base_speed = DIFFICULTIES[difficulty]['speed']
                    # Position and give opposite horizontal speed
                    new_ball.rect.center = balls[0].rect.center
                    new_ball.speed_x = -balls[0].speed_x
                    new_ball.speed_y = balls[0].speed_y
                    balls.append(new_ball)
                power_ups.remove(power_up)
        
        for laser in lasers[:]:
            laser.update()
            if laser.rect.bottom < 0:
                lasers.remove(laser)
            else:
                for brick in bricks[:]:
                    if laser.rect.colliderect(brick.rect):
                        for _ in range(10):
                            particles.append(Particle(brick.rect.centerx, brick.rect.centery, brick.color, 1, 3, 1, 3, 0.05))
                        bricks.remove(brick)
                        lasers.remove(laser)
                        points += 10
                        brick_break_sound.play()
                        break
        
        if not bricks:
            current_level += 1
            if current_level < len(LEVELS):
                # Transition to next level screen
                game_state = 'level_transition'
            else:
                # All levels completed: reset to title screen
                game_over_sound.play()
                # Reset paddle
                paddle.reset()
                # Reset balls
                new_ball = Ball(screen_width, screen_height)
                balls = [new_ball]
                # Reset level and bricks
                current_level = 0
                bricks = load_level(current_level)
                # Reset points and Attempts
                points = 0
                Attempts = DIFFICULTIES[difficulty]['Attempts']
                powerup_rate = DIFFICULTIES[difficulty]['powerup_rate']
                # Clear active effects
                power_ups.clear()
                lasers.clear()
                particles.clear()
                fireworks.clear()
                # Return to title screen
                game_state = 'title_screen'
                continue

        # --- Draw all game objects ---
        paddle.draw(screen)
        for ball in balls:
            ball.draw(screen)
        for brick in bricks:
            brick.draw(screen)
        for power_up in power_ups:
            power_up.draw(screen)
        for laser in lasers:
            laser.draw(screen)
        
        # --- Draw UI ---
        points_text = game_font.render(f"points: {points}", True, (255, 255, 255))
        screen.blit(points_text, (10, 10))
        Attempts_text = game_font.render(f"Attempts: {Attempts}", True, (255, 255, 255))
        screen.blit(Attempts_text, (screen_width - Attempts_text.get_width() - 10, 10))

    elif game_state in ['game_over', 'you_win']:
        if game_state == 'you_win':
            firework_timer -= 1
            if firework_timer <= 0:
                fireworks.append(Firework(screen_width, screen_height))
                firework_timer = random.randint(20, 50)
            
            for firework in fireworks[:]:
                firework.update()
                if firework.is_dead():
                    fireworks.remove(firework)
            
            for firework in fireworks:
                firework.draw(screen)

        message = "GAME OVER" if game_state == 'game_over' else "YOU WIN!"
        text_surface = game_font.render(message, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(screen_width / 2, screen_height / 2 - 20))
        screen.blit(text_surface, text_rect)
        
        # !!! PHASE: TITLE SCREEN !!!
        # The restart message is now consistent
        restart_surface = game_font.render("Press SPACE to return to Title", True, (255, 255, 255))
        # !!! END PHASE: TITLE SCREEN !!!
        restart_rect = restart_surface.get_rect(center=(screen_width / 2, screen_height / 2 + 30))
        screen.blit(restart_surface, restart_rect)

    # --- Update effects and messages (these run in all states) ---
    if message_timer > 0:
        message_timer -= 1
        message_surface = message_font.render(display_message, True, (255, 255, 255))
        message_rect = message_surface.get_rect(center=(screen_width / 2, screen_height - 60))
        screen.blit(message_surface, message_rect)
        
    for particle in particles[:]:
        particle.update()
        if particle.size <= 0:
            particles.remove(particle)
    for particle in particles:
        particle.draw(screen)
    # !!! END PHASE: TITLE SCREEN !!!

    # --- Final Display Update ---
    pygame.display.flip()
    clock.tick(60)