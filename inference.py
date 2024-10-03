import os
import cv2
import utils
import numpy as np
import torch
from model import restormer_arch
from collections import OrderedDict

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def stride_integral(img, stride=32):
    h, w = img.shape[:2]

    if (h % stride) != 0:
        padding_h = stride - (h % stride)
        img = cv2.copyMakeBorder(img, padding_h, 0, 0, 0, borderType=cv2.BORDER_REPLICATE)
    else:
        padding_h = 0

    if (w % stride) != 0:
        padding_w = stride - (w % stride)
        img = cv2.copyMakeBorder(img, 0, 0, padding_w, 0, borderType=cv2.BORDER_REPLICATE)
    else:
        padding_w = 0

    return img, padding_h, padding_w

def convert_state_dict(state_dict):
    """Converts a state dict saved from a dataParallel module to normal
       module state_dict inplace
       :param state_dict is the loaded DataParallel model_state

    """
    new_state_dict = OrderedDict()
    for k, v in state_dict.items():
        name = k[7:]  # remove `module.`
        new_state_dict[name] = v
    return new_state_dict

#binarization
def binarization_promptv2(img):
    result,thresh = utils.SauvolaModBinarization(img)
    thresh = thresh.astype(np.uint8)
    result[result>155]=255
    result[result<=155]=0

    x = cv2.Sobel(img,cv2.CV_16S,1,0)
    y = cv2.Sobel(img,cv2.CV_16S,0,1)
    absX = cv2.convertScaleAbs(x)   # 转回uint8
    absY = cv2.convertScaleAbs(y)
    high_frequency = cv2.addWeighted(absX,0.5,absY,0.5,0)
    high_frequency = cv2.cvtColor(high_frequency,cv2.COLOR_BGR2GRAY)
    return np.concatenate((np.expand_dims(thresh,-1),np.expand_dims(high_frequency,-1),np.expand_dims(result,-1)),-1)


def binarization(model, im_path):
    im_org = cv2.imread(im_path)
    im, padding_h, padding_w = stride_integral(im_org, 8)
    prompt = binarization_promptv2(im)
    h, w = im.shape[:2]
    in_im = np.concatenate((im, prompt), -1)

    in_im = in_im / 255.0
    in_im = torch.from_numpy(in_im.transpose(2, 0, 1)).unsqueeze(0)
    in_im = in_im.to(DEVICE)
    model = model.float()
    in_im = in_im.float()
    with torch.no_grad():
        pred = model(in_im)
        pred = pred[:, :2, :, :]
        pred = torch.max(torch.softmax(pred, 1), 1)[1]
        pred = pred[0].cpu().numpy()
        pred = (pred * 255).astype(np.uint8)
        pred = cv2.resize(pred, (w, h))
        out_im = pred[padding_h:, padding_w:]

    return prompt[:, :, 0], prompt[:, :, 1], prompt[:, :, 2], out_im


def deshadow_prompt(img):
    h, w = img.shape[:2]
    #img = cv2.resize(img,(128,128))
    img = cv2.resize(img, (1024, 1024))
    rgb_planes = cv2.split(img)
    result_planes = []
    result_norm_planes = []
    bg_imgs = []
    for plane in rgb_planes:
        dilated_img = cv2.dilate(plane, np.ones((7, 7), np.uint8))
        bg_img = cv2.medianBlur(dilated_img, 21)
        bg_imgs.append(bg_img)
        diff_img = 255 - cv2.absdiff(plane, bg_img)
        norm_img = cv2.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        result_planes.append(diff_img)
        result_norm_planes.append(norm_img)
    bg_imgs = cv2.merge(bg_imgs)
    bg_imgs = cv2.resize(bg_imgs, (w, h))
    # result = cv2.merge(result_planes)
    result_norm = cv2.merge(result_norm_planes)
    result_norm[result_norm == 0] = 1
    shadow_map = np.clip(img.astype(float) / result_norm.astype(float) * 255, 0, 255).astype(np.uint8)
    shadow_map = cv2.resize(shadow_map, (w, h))
    shadow_map = cv2.cvtColor(shadow_map, cv2.COLOR_BGR2GRAY)
    shadow_map = cv2.cvtColor(shadow_map, cv2.COLOR_GRAY2BGR)
    # return shadow_map
    return bg_imgs



def deshadowing(model, im_path):
    MAX_SIZE = 1000
    # obtain im and prompt
    im_org = cv2.imread(im_path)
    h, w = im_org.shape[:2]
    prompt = deshadow_prompt(im_org)
    in_im = np.concatenate((im_org, prompt), -1)

    # constrain the max resolution
    if max(w, h) < MAX_SIZE:
        in_im, padding_h, padding_w = stride_integral(in_im, 8)
    else:
        in_im = cv2.resize(in_im, (MAX_SIZE, MAX_SIZE))

    # normalize
    in_im = in_im / 255.0
    in_im = torch.from_numpy(in_im.transpose(2, 0, 1)).unsqueeze(0)

    # inference
    # in_im = in_im.half().to(DEVICE)
    # model = model.half()
    in_im = in_im.float().to(DEVICE)
    model = model.float()
    with torch.no_grad():
        pred = model(in_im)
        pred = torch.clamp(pred, 0, 1)
        pred = pred[0].permute(1, 2, 0).cpu().numpy()
        pred = (pred * 255).astype(np.uint8)

        if max(w, h) < MAX_SIZE:
            out_im = pred[padding_h:, padding_w:]
        else:
            pred[pred == 0] = 1
            shadow_map = cv2.resize(im_org, (MAX_SIZE, MAX_SIZE)).astype(float) / pred.astype(float)
            shadow_map = cv2.resize(shadow_map, (w, h))
            shadow_map[shadow_map == 0] = 0.00001
            out_im = np.clip(im_org.astype(float) / shadow_map, 0, 255).astype(np.uint8)
            out_im = cv2.cvtColor(out_im, cv2.COLOR_BGR2RGB)
    return prompt[:, :, 0], prompt[:, :, 1], prompt[:, :, 2], out_im


def model_init(model_path):
    # prepare model
    model = restormer_arch.Restormer(
        inp_channels=6,
        out_channels=3,
        dim=48,
        num_blocks=[2, 3, 3, 4],
        num_refinement_blocks=4,
        heads=[1, 2, 4, 8],
        ffn_expansion_factor=2.66,
        bias=False,
        LayerNorm_type='WithBias',
        dual_pixel_task=True
    )

    map_location = 'cpu' if DEVICE.type == 'cpu' else 'cuda:0'
    state_dict = torch.load(model_path, map_location=map_location)['model_state']
    state = convert_state_dict(state_dict)

    # 将状态字典加载到模型中
    model.load_state_dict(state)

    model.eval()
    model = model.to(DEVICE)
    return model


def inference_one_im(im_path,task = 'deshadow',model_path = "./pth/docres.pkl",):
    model = model_init(model_path)
    if task == 'deshadow':
        prompt1, prompt2, prompt3, restorted = deshadowing(model, im_path)
    elif task == 'binarization':
        prompt1, prompt2, prompt3, restorted = binarization(model, im_path)
    return prompt1, prompt2,prompt3,restorted

if __name__ == '__main__':
    ## model init
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model_path = "./pth/docres.pkl"
    im_path = './test_pic/0002.JPG'
    task = ''

    # inference
    prompt1, prompt2, prompt3, restorted = inference_one_im(im_path)

    # results saving
    # im_name = os.path.split(args.im_path)[-1]
    # im_format = '.'+im_name.split('.')[-1]
    # save_path = os.path.join(args.out_folder,im_name.replace(im_format,'_'+args.task+im_format))
    save_path = "./test_pic/0002_refined.JPG"
    cv2.imwrite(save_path,restorted)
    # if args.save_dtsprompt:
    #     cv2.imwrite(save_path.replace(im_format,'_prompt1'+im_format),prompt1)
    #     cv2.imwrite(save_path.replace(im_format,'_prompt2'+im_format),prompt2)
    #     cv2.imwrite(save_path.replace(im_format,'_prompt3'+im_format),prompt3)
