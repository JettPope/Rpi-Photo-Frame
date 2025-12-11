import os
import random
import pygame
import time
import platform
from PIL import Image
import pillow_heif
pillow_heif.register_heif_opener()


if platform.system() == "Windows": # for development only
    IMAGE_DIR = r"C:\PC\Documents\Rpi Photo Frame\Pictures"
    FULLSCREEN = False # make window resizable on Windows
else:
    IMAGE_DIR = "/home/Castleberry-Photo-Frame-Pics"
    FULLSCREEN = True # run fullscreen on Pi


# ---------------------- CONFIGURATION ----------------------
DISPLAY_SECONDS = 8               # how long to show each image
SUPPORTED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".heic"]
# -----------------------------------------------------------


def load_image_paths(directory):
    files = []
    for f in os.listdir(directory):
        if any(f.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            files.append(os.path.join(directory, f))
    return files


def scale_to_screen(img, screen_size):
    img_w, img_h = img.get_size()
    scr_w, scr_h = screen_size
    scale = min(scr_w / img_w, scr_h / img_h)
    new_size = (int(img_w * scale), int(img_h * scale))
    return pygame.transform.scale(img, new_size)


def main():
    pygame.init()
    pygame.mouse.set_visible(False)

    # Open window / fullscreen
    if FULLSCREEN:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((800, 480))

    screen_width, screen_height = screen.get_size()

    # Load images
    images = load_image_paths(IMAGE_DIR)
    if not images:
        print("No images found!")
        return

    # Shuffle order
    random.shuffle(images)

    # Navigation tracking
    history = []              # images already shown
    future = []               # images we can go forward to after going back
    current_index = 0
    paused = False

    last_switch_time = time.time()

    def display_image(path):
        # Load with Pillow (handles HEIC)
        pil_img = Image.open(path).convert("RGB")

        # Scale with Pillow to reduce RAM + speed conversion
        pil_img.thumbnail((screen_width, screen_height), Image.Resampling.LANCZOS)

        # Convert Pillow image → Pygame Surface
        mode = pil_img.mode
        size = pil_img.size
        data = pil_img.tobytes()

        image = pygame.image.fromstring(data, size, mode)

        # Center on screen
        rect = image.get_rect(center=(screen_width // 2, screen_height // 2))

        screen.fill((0, 0, 0))
        screen.blit(image, rect)
        pygame.display.flip()


    # Display first image
    history.append(images[current_index])
    display_image(history[-1])

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos

                # LEFT TOUCH → BACK
                if x < screen_width * 0.33:
                    if len(history) > 1:
                        # Move current into future history
                        future.append(history.pop())
                        display_image(history[-1])
                        paused = True

                # MIDDLE TOUCH → PAUSE / UNPAUSE
                elif x < screen_width * 0.66:
                    paused = not paused

                # RIGHT TOUCH → FORWARD
                else:
                    if future:
                        # Continue along previous path
                        next_img = future.pop()
                        history.append(next_img)
                        display_image(next_img)
                    else:
                        # Regular forward navigation
                        current_index = (current_index + 1) % len(images)
                        next_img = images[current_index]
                        history.append(next_img)
                        display_image(next_img)

                    paused = True

                last_switch_time = time.time()

        # Automatic switching (if not paused)
        if not paused and (time.time() - last_switch_time > DISPLAY_SECONDS):
            current_index = (current_index + 1) % len(images)
            next_img = images[current_index]
            history.append(next_img)
            future.clear()     # once you move forward naturally, future is invalidated
            display_image(next_img)
            last_switch_time = time.time()

        time.sleep(0.01)


if __name__ == "__main__":
    main()
