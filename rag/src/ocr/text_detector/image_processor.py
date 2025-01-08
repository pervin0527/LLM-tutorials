import cv2
import numpy as np

def load_image(img_file):
    image = cv2.imread(img_file, cv2.IMREAD_UNCHANGED)

    if len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    
    if image.shape[2] == 4:  # RGBA
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

    # Convert BGR to RGB
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    return image


def normalize_mean_var(in_img, mean=(0.485, 0.456, 0.406), variance=(0.229, 0.224, 0.225)):
    img = in_img.copy().astype(np.float32)
    mean = np.array(mean, dtype=np.float32) * 255.0
    variance = np.array(variance, dtype=np.float32) * 255.0

    img = (img - mean) / variance

    return img


def denormalize_mean_var(in_img, mean=(0.485, 0.456, 0.406), variance=(0.229, 0.224, 0.225)):
    img = in_img.copy()
    mean = np.array(mean, dtype=np.float32)
    variance = np.array(variance, dtype=np.float32)

    img = (img * variance + mean) * 255.0
    img = np.clip(img, 0, 255).astype(np.uint8)

    return img


def resize_aspect_ratio(img, square_size, interpolation, mag_ratio=1):
    height, width, channel = img.shape

    target_size = mag_ratio * max(height, width)

    if target_size > square_size:
        target_size = square_size

    ratio = target_size / max(height, width)

    target_h, target_w = int(height * ratio), int(width * ratio)
    proc = cv2.resize(img, (target_w, target_h), interpolation=interpolation)

    target_h32, target_w32 = target_h, target_w
    if target_h % 32 != 0:
        target_h32 = target_h + (32 - target_h % 32)
    if target_w % 32 != 0:
        target_w32 = target_w + (32 - target_w % 32)

    resized = np.zeros((target_h32, target_w32, channel), dtype=np.float32)
    resized[0:target_h, 0:target_w, :] = proc
    target_h, target_w = target_h32, target_w32

    size_heatmap = (int(target_w / 2), int(target_h / 2))

    return resized, ratio, size_heatmap


def cvt2HeatmapImg(img):
    img = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    img = cv2.applyColorMap(img, cv2.COLORMAP_JET)
    
    return img
