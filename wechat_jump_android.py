# coding: utf-8
import os
import time
import random
from operator import itemgetter
from PIL import Image

import cv2
import numpy as np
from torchvision import transforms
from replay_memory import Transition


def pull_screenshot(file_name):
    # Get screenshot
    os.system('adb shell screencap -p /sdcard/%s' % file_name)
    os.system('adb pull /sdcard/%s .' % file_name)


def preprocess(image):
    # Crop and normalize image
    w, h = image.size
    top = (h - w) / 2

    image = image.crop((0, top, w, w + top))
    image = image.convert('RGB')
    image = image.resize((224, 224), resample=Image.LANCZOS)

    normalize = transforms.Normalize(
        mean=[0.92206, 0.92206, 0.92206], std=[0.08426, 0.08426, 0.08426])
    transform = transforms.Compose([transforms.ToTensor(), normalize])

    image = transform(image)

    return image


def jump(press_time, swipe_x1, swipe_y1, swipe_x2, swipe_y2):
    press_time = int(press_time)
    cmd = 'adb shell input swipe {x1} {y1} {x2} {y2} {duration}'.format(
        x1=swipe_x1,
        y1=swipe_y1,
        x2=swipe_x2,
        y2=swipe_y2,
        duration=press_time)
    os.system(cmd)


number_templet = [cv2.imread('templet/{}.jpg'.format(i)) for i in range(10)]
threshold = 0.98


def get_score(file_name):
    # Get score from image

    background = cv2.imread(file_name)

    match_result = []
    for i, number in enumerate(number_templet):
        res = cv2.matchTemplate(number, background, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res > threshold)
        for pt in zip(*loc):
            match_result.append((i, pt[0]))
    match_result.sort(key=itemgetter(1))

    score = 0
    for x in match_result:
        score = 10 * score + x[0]

    return score


restart_templet = cv2.imread('templet/again.jpg')


def restart(file_name):
    # Check game over and restart
    background = cv2.imread(file_name)

    res = cv2.matchTemplate(restart_templet, background, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    if max_val > threshold:
        top_left = max_loc
        left, top = (top_left[0] + restart_templet.shape[1] / 2,
                     top_left[1] + restart_templet.shape[0] / 2)
        left = int(random.uniform(left - 10, left + 10))
        top = int(random.uniform(top - 10, top + 10))
        jump(100, left, top, left, top)

        return True
    else:
        return False


def get_press_position():
    """Generate position randomly
    """

    left = int(1080 / 2)
    top = int(1920 / 2)
    left = int(random.uniform(left - 100, left + 100))
    top = int(random.uniform(top - 100, top + 100))
    return (left, top, left, top)


last_score = 0

def step(action):
    """Peform action and return state
       action = xx ms
    """
    global last_score
    state = preprocess(Image.open('autojump.png'))

    x1, y1, x2, y2 = get_press_position()
    jump(action, x1, y1, x2, y2)
    time.sleep(3)

    pull_screenshot('autojump.png')
    if restart('autojump.png'):
        last_score = 0
        return Transition(
            state=state, action=action, mask=0, next_state=None, reward=0)
    else:
        score = get_score('autojump.png')
        reward = score - last_score
        last_score = score

        next_state = preprocess(Image.open('autojump.png'))
        return Transition(
            state=state,
            action=action,
            mask=1,
            next_state=next_state,
            reward=reward)


if __name__ == "__main__":
    print(step(1000))
