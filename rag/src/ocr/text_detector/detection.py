import cv2
import torch
import numpy as np

import image_processor
import model_utils

def detect(model, image, text_thres, link_thres, low_text, cuda, poly, refine_net=None):
    resized_img, target_ratio, heatmap_size = image_processor.resize_aspect_ratio(image, square_size=1280, interpolation=cv2.INTER_LINEAR, mag_ratio=1.5)
    ratio_h = ratio_w = 1 / target_ratio

    x = image_processor.normalize_mean_var(resized_img)
    x = torch.from_numpy(x).permute(2, 0, 1)
    x = torch.autograd.Variable(x.unsqueeze(0))

    if cuda:
        x = x.cuda()

    with torch.no_grad():
        y, feature = model(x)

    score_text = y[0,:,:,0].cpu().data.numpy()
    score_link = y[0,:,:,1].cpu().data.numpy()

    if refine_net is not None:
        with torch.no_grad():
            y_refiner = refine_net(y, feature)
        score_link = y_refiner[0,:,:,0].cpu().data.numpy()

    ## Post-processing
    boxes, polys = model_utils.getDetBoxes(score_text, score_link, text_thres, link_thres, low_text, poly)

    ## coordinate adjustment
    boxes = model_utils.adjustResultCoordinates(boxes, ratio_w, ratio_h)
    polys = model_utils.adjustResultCoordinates(polys, ratio_w, ratio_h)
    for k in range(len(polys)):
        if polys[k] is None: polys[k] = boxes[k]

    ## render results (optional)
    render_img = score_text.copy()
    render_img = np.hstack((render_img, score_link))
    ret_score_text = image_processor.cvt2HeatmapImg(render_img)

    return boxes, polys, ret_score_text