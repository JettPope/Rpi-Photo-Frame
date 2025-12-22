import os
import random
import hashlib
import gc
import threading
from collections import OrderedDict
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

# Runtime caching / prefetch settings
PREFETCH_COUNT = 3        # how many upcoming images to cache in memory
SURFACE_CACHE_SIZE = 6    # max number of surfaces to keep in memory

# In-memory surface cache (path -> pygame.Surface), LRU
surface_cache = OrderedDict()
cache_lock = threading.Lock()


if platform.system() == "Windows": # for development only
    IMAGE_DIR = r"C:\PC\Documents\Rpi Photo Frame\Pictures"
    FULLSCREEN = False # make window resizable on Windows
else:
    IMAGE_DIR = "Pics"
    FULLSCREEN = True # run fullscreen on Pi


# ---------------------- CONFIGURATION ----------------------
DISPLAY_SECONDS = 45               # how long to show each image
SUPPORTED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".heic"]
# -----------------------------------------------------------


def load_image_paths(directory):
    # Return a sorted list of image file paths found recursively under `directory`.
    # Creates the directory if it doesn't exist so users cloning the repo see the folder.
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"Created image directory: {directory}")
        except Exception:
            print(f"Warning: could not create image directory: {directory}")
            return []

    paths = []
    for root, dirs, files in os.walk(directory):
        for fname in files:
            if any(fname.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                paths.append(os.path.join(root, fname))

    # Sort for deterministic order (folders then files alphabetically)
    paths.sort()

    # Remove duplicates while preserving order (defensive)
    seen = set()
    unique_paths = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            unique_paths.append(p)

    return unique_paths


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


def _load_surface_from_thumbnail(thumb_path):
    # Load a pygame surface from disk and return it. Caller should handle exceptions.
    return pygame.image.load(thumb_path).convert()


def _ensure_prefetch(images, start_index, screen_size):
    # Prefetch thumbnails + surfaces for the next PREFETCH_COUNT images starting at start_index.
    def _worker():
        n = len(images)
        if n == 0:
            return
        for i in range(start_index, start_index + PREFETCH_COUNT):
            idx = i % n
            path = images[idx]
            thumb = _thumbnail_path_for(path, screen_size)
            try:
                if not os.path.exists(thumb):
                    _create_thumbnail(path, thumb, screen_size)

                with cache_lock:
                    if path in surface_cache:
                        # move to end = mark as recently used
                        surface_cache.move_to_end(path)
                        continue

                surf = _load_surface_from_thumbnail(thumb)

                with cache_lock:
                    surface_cache[path] = surf
                    # trim cache
                    while len(surface_cache) > SURFACE_CACHE_SIZE:
                        surface_cache.popitem(last=False)
            except Exception:
                # ignore individual failures — they'll be skipped at display time
                continue

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def main():
    pygame.init()
    pygame.mouse.set_visible(False)
    pygame.font.init()

    # Open window / fullscreen
    if FULLSCREEN:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((800, 480))

    screen_width, screen_height = screen.get_size()

    # small font for status text (pause indicator)
    try:
        status_font = pygame.font.SysFont(None, 36)
    except Exception:
        status_font = None

    # Load images (recursive)
    images = load_image_paths(IMAGE_DIR)
    if not images:
        print("No images found!")
        return

    # Shuffle order to intersperse images from different folders
    random.shuffle(images)

    # Navigation tracking
    history = []              # images already shown
    future = []               # images we can go forward to after going back
    current_index = 0
    paused = False

    last_switch_time = time.time()

    def display_image(path):
        thumb_path = _thumbnail_path_for(path, (screen_width, screen_height))

        # Prefer in-memory cached surface
        with cache_lock:
            surface = surface_cache.get(path)

        if surface is not None:
            image = surface
        else:
            try:
                if not os.path.exists(thumb_path):
                    _create_thumbnail(path, thumb_path, (screen_width, screen_height))

                image = _load_surface_from_thumbnail(thumb_path)
                # store into cache
                with cache_lock:
                    surface_cache[path] = image
                    surface_cache.move_to_end(path)
                    while len(surface_cache) > SURFACE_CACHE_SIZE:
                        surface_cache.popitem(last=False)
            except MemoryError:
                print(f"MemoryError loading {path} — skipping image")
                return
            except Exception as e:
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

        # Draw paused indicator if paused
        if paused and status_font is not None:
            try:
                s = status_font.render("PAUSED", True, (255, 255, 255))
                bg = pygame.Surface((s.get_width() + 20, s.get_height() + 10), pygame.SRCALPHA)
                bg.fill((0, 0, 0, 160))
                bx = 10
                by = 10
                screen.blit(bg, (bx, by))
                screen.blit(s, (bx + 10, by + 5))
            except Exception:
                pass

        pygame.display.flip()


    # Display first image
    history.append(images[current_index])
    display_image(history[-1])
    # Prefetch next images
    _ensure_prefetch(images, current_index + 1, (screen_width, screen_height))

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

                        # reset auto-advance timer instead of pausing
                        last_switch_time = time.time()
                        _ensure_prefetch(images, current_index + 1, (screen_width, screen_height))

                # MIDDLE TOUCH → PAUSE / UNPAUSE
                elif x < screen_width * 0.66:
                    paused = not paused
                    # Immediately redraw the current image so the PAUSED indicator shows/hides
                    try:
                        if history:
                            display_image(history[-1])
                    except Exception:
                        pass

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

                    # reset auto-advance timer instead of pausing
                    last_switch_time = time.time()

                    # Prefetch upcoming images
                    _ensure_prefetch(images, current_index + 1, (screen_width, screen_height))

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
