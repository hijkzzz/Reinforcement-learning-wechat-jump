#coding: utf-8

import os
import random
import torch
import numpy as np

from ddpg import DDPG
from ounoise import OUNoise
from replay_memory import ReplayMemory, Transition
import wechat_jump_android as env

SEED = 2
NOISE_SCALE = 1
BATCH_SIZE = 16
REPLAY_SIZE = 50000
NUM_EPISODES = 100000
GAMMA = 0.99
TAU = 0.001
EXPLORATION_END = 100
UPDATES_PER_STEP = 1

torch.manual_seed(SEED)
np.random.seed(SEED)
random.seed(SEED)


def main():
    ddpg = DDPG(GAMMA, TAU, torch.cuda.is_available())
    memory0 = ReplayMemory(REPLAY_SIZE // 2)
    memory1 = ReplayMemory(REPLAY_SIZE // 2)
    ounoise = OUNoise(1, scale=NOISE_SCALE)
    env.init_state()

    if os.path.exists('models/ddpg_actor_'):
        ddpg.load_model()

    updates = 0
    for i_episode in range(NUM_EPISODES):
        ounoise.reset()

        while True:
            action = ddpg.select_action(env.state, ounoise) \
                    if i_episode < EXPLORATION_END else ddpg.select_action(env.state)
            transition = env.step(action)

            if transition.reward < 1:
                memory0.push(transition)
            else:
                memory1.push(transition)

            if len(memory0) > BATCH_SIZE // 2 and len(
                    memory1) > BATCH_SIZE // 2:
                for _ in range(UPDATES_PER_STEP):
                    transitions = memory0.sample(
                        BATCH_SIZE // 2) + memory1.sample(BATCH_SIZE // 2)
                    random.shuffle(transitions)

                    batch = Transition(*zip(*transitions))
                    value_loss, policy_loss = ddpg.update_parameters(batch)

                    print(
                        "Episode: {}, Updates: {}, Value Loss: {}, Policy Loss: {}".
                        format(i_episode, updates, value_loss, policy_loss))
                    updates += 1

                break

        if (i_episode + 1) % 1000 == 0:
            ddpg.save_model()


if __name__ == "__main__":
    main()
