import sys
import time
import random
import pygame
from collections import deque
import cv2 as cv
import mediapipe as mp

# Initialize Pygame
pygame.init()

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Initialize required elements/environment
VID_CAP = cv.VideoCapture(0)
window_size = (int(VID_CAP.get(cv.CAP_PROP_FRAME_WIDTH)), int(VID_CAP.get(cv.CAP_PROP_FRAME_HEIGHT)))  # width by height
screen = pygame.display.set_mode(window_size)

# Bird and pipe initialization
bird_img = pygame.image.load("bird_sprite.png")
bird_img = pygame.transform.scale(bird_img, (bird_img.get_width() // 6, bird_img.get_height() // 6))
bird_frame = bird_img.get_rect()
bird_frame.center = (window_size[0] // 6, window_size[1] // 2)
pipe_frames = deque()
pipe_img = pygame.image.load("pipe_sprite_single.png")

pipe_starting_template = pipe_img.get_rect()
space_between_pipes = 250

# Game parameters
game_clock = time.time()
stage = 1
pipeSpawnTimer = 0
time_between_pipe_spawn = 40
dist_between_pipes = 500
pipe_velocity = lambda: dist_between_pipes / time_between_pipe_spawn
score = 0
didUpdateScore = False
game_is_running = True

while True:
    # Check if game is running
    if not game_is_running:
        text = pygame.font.SysFont("Helvetica Bold.ttf", 64).render('Game over!', True, (99, 245, 255))
        tr = text.get_rect()
        tr.center = (window_size[0] // 2, window_size[1] // 2)
        screen.blit(text, tr)
        pygame.display.update()
        pygame.time.wait(2000)
        VID_CAP.release()
        cv.destroyAllWindows()
        pygame.quit()
        sys.exit()

    # Check if user quit window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            VID_CAP.release()
            cv.destroyAllWindows()
            pygame.quit()
            sys.exit()

    # Get frame
    ret, frame = VID_CAP.read()
    if not ret:
        print("Empty frame, continuing...")
        continue

    # Clear screen
    screen.fill((125, 220, 232))

    # Hand tracking
    frame.flags.writeable = False
    frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    frame.flags.writeable = True

    # Draw detected hands
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw landmarks if needed
            # mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Get landmark points for index finger and middle finger
            index_finger_landmark = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            middle_finger_landmark = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

            # Compare y-coordinates to control bird's movement
            if middle_finger_landmark.y < index_finger_landmark.y:
                # Move the bird upward
                bird_frame.centery -= 5  # Adjust the speed as needed
            else:
                # Move the bird downward
                bird_frame.centery += 5  # Adjust the speed as needed

    # Update pipe positions
    for pf in pipe_frames:
        pf[0].x -= pipe_velocity()
        pf[1].x -= pipe_velocity()

    if len(pipe_frames) > 0 and pipe_frames[0][0].right < 0:
        pipe_frames.popleft()

    # Update screen
    frame_surface = pygame.surfarray.make_surface(cv.flip(frame, 1).swapaxes(0, 1))
    screen.blit(frame_surface, (0, 0))
    screen.blit(bird_img, bird_frame)
    checker = True
    for pf in pipe_frames:
        # Check if bird went through to update score
        if pf[0].left <= bird_frame.x <= pf[0].right:
            checker = False
            if not didUpdateScore:
                score += 1
                didUpdateScore = True
        # Update screen
        screen.blit(pipe_img, pf[1])
        screen.blit(pygame.transform.flip(pipe_img, 0, 1), pf[0])
    if checker:
        didUpdateScore = False

    # Stage, score text
    text = pygame.font.SysFont("Helvetica Bold.ttf", 50).render(f'Stage {stage}', True, (99, 245, 255))
    tr = text.get_rect()
    tr.center = (100, 50)
    screen.blit(text, tr)
    text = pygame.font.SysFont("Helvetica Bold.ttf", 50).render(f'Score: {score}', True, (99, 245, 255))
    tr = text.get_rect()
    tr.center = (100, 100)
    screen.blit(text, tr)

    # Update screen
    pygame.display.flip()

    # Check if bird is touching a pipe
    if any([bird_frame.colliderect(pf[0]) or bird_frame.colliderect(pf[1]) for pf in pipe_frames]):
        game_is_running = False

    # Time to add new pipes
    if pipeSpawnTimer == 0:
        top = pipe_starting_template.copy()
        top.x, top.y = window_size[0], random.randint(120 - 1000, window_size[1] - 120 - space_between_pipes - 1000)
        bottom = pipe_starting_template.copy()
        bottom.x, bottom.y = window_size[0], top.y + 1000 + space_between_pipes
        pipe_frames.append([top, bottom])

    # Update pipe spawn timer - make it cyclical
    pipeSpawnTimer += 1
    if pipeSpawnTimer >= time_between_pipe_spawn:
        pipeSpawnTimer = 0

    # Update stage
    if time.time() - game_clock >= 10:
        time_between_pipe_spawn *= 5 / 6
        stage += 1
        game_clock = time.time()
