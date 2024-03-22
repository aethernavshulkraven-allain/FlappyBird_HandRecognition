import pygame
import numpy as np
import cv2 as cv
import mediapipe as mp

# Initialize pygame
pygame.init()

# Define game constants
bird_speed = 1
gravity = 1  # Match jump force for equal falling speed
jump_force = -5  # Adjust as needed
bird_img = pygame.image.load("bird_sprite.png")
bird_img = pygame.transform.scale(bird_img, (bird_img.get_width() // 6, bird_img.get_height() // 6))
pipe_width = 50
pipe_gap = 300
pipe_interval = 200
pipes = []
score = 0
highest_score = 0

width, height = 500, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Flappy Bird (Gesture Control)")
clock = pygame.time.Clock()

# Initialize pygame font module
pygame.font.init()

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Initialize OpenCV webcam capture
cap = cv.VideoCapture(0)


class Bird:
    def __init__(self, y):
        self.y = y
        self.vel_y = 0
        self.bird_height = bird_img.get_height() // 6  # Adjust for scaled image

    def jump(self):
        self.vel_y = jump_force

    def update(self):
        # Update bird's vertical position
        self.y += self.vel_y
        self.vel_y += gravity

        # Ensure bird stays within screen boundaries
        if self.y < 0:  # Prevent bird from going above top boundary
            self.y = 0
            self.vel_y = 0
        elif self.y + self.bird_height > height:  # Prevent bird from going below bottom boundary
            self.y = height - self.bird_height
            self.vel_y = 0

 
def draw_game(screen, bird, pipes):
    # Display background, bird, and pipes
    screen.fill((0, 0, 0))  # Clear the screen
    screen.blit(background_img, (0, 0))  # Draw background image

    screen.blit(bird_img, (50, bird.y))  # Draw bird
    # Draw pipes
    for pipe in pipes:
        pygame.draw.rect(screen, (0, 255, 0), pipe)  # Green pipes

    # Display scores
    font = pygame.font.Font(None, 36)
    # score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    # screen.blit(score_text, (10, 10))

    highest_score_text = font.render(f"Highest Score: {highest_score}", True, (255, 255, 255))
    screen.blit(highest_score_text, (10, 40))


def update_game(bird, pipes):
    global score, highest_score
    bird.update()
    
    # Check if the bird passes a level (crosses a pipe)
    passed_level = False

    for pipe in pipes:
        pipe.x -= 1

        # Check if the bird crosses this pipe
        if pipe.x <= 50 and pipe.x + pipe_width >= 50:
            passed_level = True
            break  # Exit the loop after detecting a pipe crossing

    if pipes[-1].x < width - pipe_interval:
        top_pipe_height = np.random.randint(100, height - pipe_gap - 100)
        bottom_pipe_height = height - pipe_gap - top_pipe_height
        pipes.append(pygame.Rect(width, 0, pipe_width, top_pipe_height))
        pipes.append(pygame.Rect(width, height - bottom_pipe_height, pipe_width, bottom_pipe_height))

    pipes[:] = [pipe for pipe in pipes if pipe.x > -pipe_width]

    if check_collision(bird, pipes):
        print("Game Over")
        if score > highest_score:
            highest_score = score
        score = 0
        return True

    # Update score only once per pipe crossing event
    if passed_level:
        score += 1

    return False



def track_hand(frame):
    # Track hand landmarks and return the y-coordinate of the index finger
    results = hands.process(cv.cvtColor(frame, cv.COLOR_BGR2RGB))
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]

            if thumb_tip.y > index_tip.y:
                return 'up'
            else:
                return 'down'
    return None


def check_collision(bird, pipes):
    bird_rect = pygame.Rect(50, bird.y, bird_img.get_width(), bird_img.get_height())  # Bird rectangle
    for pipe in pipes:
        if bird_rect.colliderect(pipe):
            return True  # Collision detected
    return False


def draw_start_screen():
    global button_rect, background_img

    screen.fill((0, 0, 0))  # Clear the screen

    # Draw background image
    background_img = pygame.image.load("background_image.png")
    screen.blit(background_img, (0, 0))

    font = pygame.font.Font(None, 64)  # Use default font if None
    text = font.render("Flappy Bird", True, (255, 255, 255))
    text_rect = text.get_rect(center=(width // 2, height // 3))
    screen.blit(text, text_rect)

    button_img = pygame.image.load("button_image.png")
    button_rect = button_img.get_rect(center=(width // 2, 400))
    screen.blit(button_img, button_rect)

    pygame.display.flip()


def main():
    running = True
    start_screen = True

    while start_screen:
        draw_start_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                start_screen = False
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if button_rect.collidepoint(mouse_pos):
                    start_screen = False

   
    bird = Bird(height // 2)

    # Create initial pipes with random heights
    top_pipe_height = np.random.randint(100, height - pipe_gap - 100)
    bottom_pipe_height = height - pipe_gap - top_pipe_height
    pipes.append(pygame.Rect(width, 0, pipe_width, top_pipe_height))
    pipes.append(pygame.Rect(width, height - bottom_pipe_height, pipe_width, bottom_pipe_height))

    while running:
        ret, frame = cap.read()
        if not ret:
            break

        gesture = track_hand(frame)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if gesture == 'up':
            bird.jump()

        if update_game(bird, pipes):
            running = False

        draw_game(screen, bird, pipes)
        pygame.display.flip()
        clock.tick(60)  # Adjust frame rate as needed

        # Display hand landmarks on the webcam feed
        results = hands.process(cv.cvtColor(frame, cv.COLOR_BGR2RGB))
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # Show webcam feed
        cv.imshow("Hand Tracking", frame)
        if cv.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
            break

    cap.release()
    cv.destroyAllWindows()
    pygame.quit()


if __name__ == "__main__":
    main()
