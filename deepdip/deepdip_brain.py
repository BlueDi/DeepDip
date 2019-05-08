#!/bin/env python

import argparse

import gym
import gym_diplomacy
from gym import wrappers, logger
from baselines.bench import monitor

import glob
import math
import numpy as np
import os
import torch
from time import time
from timeit import default_timer as timer
from datetime import timedelta

from agent import Model
from agent_config import Config
from plot import plot_all_data


start = timer()

config = Config()

config.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

#epsilon variables
config.epsilon_start    = 1.0
config.epsilon_final    = 0.01
config.epsilon_decay    = 30000
config.epsilon_by_frame = lambda frame_idx: config.epsilon_final + (config.epsilon_start - config.epsilon_final) * math.exp(-1. * frame_idx / config.epsilon_decay)

#misc agent variables
config.GAMMA = 0.99
config.LR    = 1e-4

#memory
config.TARGET_NET_UPDATE_FREQ = 2
config.EXP_REPLAY_SIZE        = 10000
config.BATCH_SIZE             = 32

#Learning control variables
config.LEARN_START = 1000
config.MAX_FRAMES  = 10000
config.UPDATE_FREQ = 1


parser = argparse.ArgumentParser(description=None)
parser.add_argument('env_id', nargs='?', default='Diplomacy_Strategy-v0', help='Select the environment to run')
args = parser.parse_args()

logger.set_level(logger.INFO)

log_dir = os.path.join(os.getcwd(), 'deepdip-results')
try:
    os.makedirs(log_dir)
except OSError:
    files = glob.glob(os.path.join(log_dir, '*.monitor.csv')) \
        + glob.glob(os.path.join(log_dir, '*td.csv')) \
        + glob.glob(os.path.join(log_dir, '*sig_param_mag.csv')) \
        + glob.glob(os.path.join(log_dir, '*action_log.csv'))
    for f in files:
        os.remove(f)

env_id = args.env_id
env = gym.make(env_id)
env = monitor.Monitor(env, os.path.join(log_dir, env_id))
model = Model(env=env, config=config, log_dir=log_dir)
model.load_w()
model.load_replay()
print(model.model)

frame_idx = 0
episode_reward = 0
reward = 0
done = False


def get_player_units(state):
    player = state[-1]
    index = state[::4]
    units = state[3::4]
    player_units = [i for i, unit in zip(index, units) if unit == player]
    return player_units


observation = env.reset()
for frame_idx in range(1, config.MAX_FRAMES + 1):
    epsilon = config.epsilon_by_frame(frame_idx)

    action = model.get_action(observation, epsilon)

    prev_observation = observation
    observation, reward, done, _ = env.step(action)
    #observation = None if done else observation
    episode_reward += reward
    
    model.update(prev_observation, action, reward, observation, frame_idx)
    
    if done:
        logger.info('Finished episode at frame {} with a reward of {}.'.format(frame_idx, episode_reward))
        model.finish_nstep()
        model.reset_hx()
        observation = env.reset()
        model.save_reward(episode_reward)
        episode_reward = 0

    if frame_idx % 10 == 0:
        print('')
        print('')
        print('FRAME_IDX: {}'.format(frame_idx))
        print('')
        print('')
        model.save_w()
        plot_all_data(log_dir, env_id, 'DeepDip', config.MAX_FRAMES, bin_size=(10, 100, 100, 1), smooth=1, time=timedelta(seconds=int(timer()-start)), save_filename='./results.png', ipynb=False)

model.save_w()
model.save_replay()
env.close()
plot_all_data(log_dir, env_id, 'DeepDip', config.MAX_FRAMES, bin_size=(10, 100, 100, 1), smooth=1, time=timedelta(seconds=int(timer()-start)), save_filename='./results.png', ipynb=False)
logger.info('Training completed.')
