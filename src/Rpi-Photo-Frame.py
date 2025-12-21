import os
import random
import hashlib
import gc
import pygame
import time
import platform
from PIL import Image
import pillow_heif
pillow_heif.register_heif_opener()

# Thumbnail cache directory (inside project .cache by default)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE_DIR = os.path.join(ROOT_DIR, ".cache", "thumbs")
os.makedirs(CACHE_DIR, exist_ok=True)


if platform.system() == "Windows": # for development only
    IMAGE_DIR = r"C:\PC\Documents\Rpi Photo Frame\Pictures"
    FULLSCREEN = False # make window resizable on Windows
else:
    IMAGE_DIR = "Pics"
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


def _thumbnail_path_for(image_path, screen_size):
    # Use path + mtime + screen size to generate a cache filename
    try:
        mtime = int(os.path.getmtime(image_path))
    except OSError:
        mtime = 0
    key = f"{image_path}-{mtime}-{screen_size[0]}x{screen_size[1]}"
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()
    # keep original extension as .jpg for cached thumbnails
    return os.path.join(CACHE_DIR, f"{h}.jpg")


def _create_thumbnail(src_path, dst_path, screen_size):
    # Create a small cached version of the image that fits screen_size.
    # Use Image.draft where possible to reduce memory when decoding large files.
    with Image.open(src_path) as im:
        try:
            im.draft("RGB", screen_size)
        except Exception:
            pass
        im = im.convert("RGB")
        im.thumbnail(screen_size, Image.Resampling.LANCZOS)
        # save with reasonable quality to reduce size
        im.save(dst_path, format="JPEG", quality=85, optimize=True)
    # encourage GC after heavy operations
    gc.collect()


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
        # Try to use a cached thumbnail (faster, lower memory). If missing,
        # create one and then load it with pygame to avoid expensive conversions.
        thumb_path = _thumbnail_path_for(path, (screen_width, screen_height))

        try:
            if not os.path.exists(thumb_path):
                _create_thumbnail(path, thumb_path, (screen_width, screen_height))

            # Load the cached JPEG thumbnail with pygame (fast, lower memory)
            image = pygame.image.load(thumb_path)
        except MemoryError:
            print(f"MemoryError loading {path} — skipping image")
            return
        except Exception as e:
            # Fallback: attempt an in-memory, conservative load; if that fails, skip
            try:
                with Image.open(path) as pil_img:
                    pil_img.draft("RGB", (screen_width, screen_height))
                    pil_img = pil_img.convert("RGB")
                    pil_img.thumbnail((screen_width, screen_height), Image.Resampling.LANCZOS)
                    data = pil_img.tobytes()
                    image = pygame.image.fromstring(data, pil_img.size, pil_img.mode)
            except Exception as e2:
                print(f"Failed to load image {path}: {e} / {e2}")
                return

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
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
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
