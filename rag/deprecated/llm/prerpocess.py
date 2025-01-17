import base64

def img_preprocessing(img_path):
    with open(img_path, "rb") as bimg:
        base64_img = base64.b64encode(bimg.read()).decode("utf-8")

    return base64_img