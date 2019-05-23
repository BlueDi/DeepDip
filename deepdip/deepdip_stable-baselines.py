import argparse
import os
import re
from datetime import datetime

import gym
import gym_diplomacy

import numpy as np
import matplotlib.pyplot as plt

from stable_baselines.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines.common import set_global_seeds

from stable_baselines.bench import Monitor
from stable_baselines.results_plotter import load_results, ts2xy

from ppo import PPO2

import logging


FORMAT = "%(levelname)-8s -- [%(filename)s:%(lineno)s - %(funcName)15s()] %(message)s"
logging.basicConfig(format=FORMAT)

logging_level = 'DEBUG'
level = getattr(logging, logging_level)
logger = logging.getLogger(__name__)
logger.setLevel(level)

gym_env_id = 'Diplomacy_Strategy-v0'
algorithm = 'ppo2'
total_timesteps = 1e6
saving_interval = 1e3
train_timesteps = 1e2
best_mean_reward, n_steps = -np.inf, 0

current_time_string = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
log_dir = "./deepdip-results/"
pickle_dir = log_dir + "pickles/"
os.makedirs(log_dir, exist_ok=True)
os.makedirs(pickle_dir, exist_ok=True)


def multiprocess_make_env(env_id, rank, seed=0):
    """
    Utility function for multiprocessed env.
    
    :param env_id: (str) the environment ID
    :param num_env: (int) the number of environment you wish to have in subprocesses
    :param seed: (int) the inital seed for RNG
    :param rank: (int) index of the subprocess
    """
    def _init():
        env = gym.make(env_id)
        env.seed(seed + rank)
        return env
    set_global_seeds(seed)
    return _init


def remove_files_with_pattern(dir, pattern):
    for f in os.listdir(dir):
        if re.search(pattern, f):
            os.remove(os.path.join(dir, f))


def rename_files(dir, pattern_to_search, old_pattern, new_pattern):
    for f in os.listdir(dir):
        if re.search(pattern_to_search, f):
            new_name = re.sub(old_pattern, new_pattern, f)
            os.rename(os.path.join(dir, f), os.path.join(dir, new_name))


def get_files_with_pattern(dir, pattern):
    files = []
    for f in os.listdir(dir):
        if re.search(pattern, f):
            files.append(os.path.join(dir,f))
    return files


def make_env(gym_env_id):
    env = None
    multiprocess = False
    num_cpu = 4
    if multiprocess:
        env = SubprocVecEnv([multiprocess_make_env(gym_env_id, i) for i in range(num_cpu)])
    else:
        gym_env = gym.make(gym_env_id)
        monitor_file_path = log_dir + current_time_string + "-monitor.csv"
        env = Monitor(gym_env, monitor_file_path, allow_early_resets=True)

        # vectorized environments allow to easily multiprocess training
        # we demonstrate its usefulness in the next examples
        env = DummyVecEnv([lambda: env]) # The algorithms require a vectorized environment to run
    return env


def load_model(env):
    model = None
    model_steps = 0

    existing_pickle_files = get_files_with_pattern(pickle_dir, algorithm + r'_' + gym_env_id + r'_(.*)_steps.pkl')
    
    for file_name in existing_pickle_files:
        search = re.search(algorithm + r'_' + gym_env_id + r'_(.*)_steps.pkl', file_name)
        if search:
            if algorithm == 'ppo2':
                model = PPO2.load(file_name, env=env, verbose=0)
            else:
                raise Exception("Algorithm not supported: {}".format(algorithm))

            model_steps = int(search.group(1))

            logger.info("Loading existing pickle file for environment {} with {} steps of training with algorithm {} and policy '{}'.".format(gym_env_id, model_steps, algorithm, model.policy))

            return model, model_steps
    
    logger.info("No pickle was found for environment {}. Creating new model with algorithm {} and policy 'MlpPolicy'...".format(gym_env_id, algorithm))
    model = PPO2(policy='MlpPolicy', env=env, verbose=0)

    return model, model_steps  


def train(env, total_timesteps=1e6):    
    model, model_steps = load_model(env)

    model.learn(int(total_timesteps), callback=callback)
    
    return model


def callback(_locals, _globals):
    """
    Callback called after n steps (see ACER or PPO2)
    :param _locals: (dict)
    :param _globals: (dict)
    """
    global n_steps, best_mean_reward
    # Print stats every X calls
    n_steps += 1
    if n_steps % saving_interval == 0:
        logger.info("Current Step: {}".format(n_steps))
        # Evaluate policy training performance
        x, y = ts2xy(load_results(log_dir), 'timesteps')
        if len(x) > 0:
            mean_reward = np.mean(y[-100:])
            logger.info("{} timesteps".format(x[-1]))
            logger.info("Best mean reward: {:.2f} - Last mean reward per episode: {:.2f}".format(best_mean_reward, mean_reward))

            # New best model, you could save the agent here
            if mean_reward > best_mean_reward:
                best_mean_reward = mean_reward
                # Example for saving best model
                logger.info("Saving new best model")
                _locals['self'].save(pickle_dir + 'ppo2_best_model.pkl')

    # Returning False will stop training early
    return True


def evaluate(env, num_steps=1e3):
    """
    Evaluate a RL agent
    :param model: (BaseRLModel object) the RL Agent
    :param num_steps: (int) number of timesteps to evaluate it
    :return: (float) Mean reward for the last 100 episodes
    """
    model, model_steps = load_model(env)
    episode_rewards = [0.0]
    obs = env.reset()
    for i in range(int(num_steps)):
        # _states are only useful when using LSTM policies
        action, _states = model.predict(obs)
        # here, action, rewards and dones are arrays
        # because we are using vectorized env
        obs, rewards, dones, info = env.step(action)
        
        # Stats
        episode_rewards[-1] += rewards[0]
        if dones[0]:
            obs = env.reset()
            episode_rewards.append(0.0)
    # Compute mean reward for the last 100 episodes
    mean_100ep_reward = round(np.mean(episode_rewards[-100:]), 1)
    print("Mean reward:", mean_100ep_reward, "Num episodes:", len(episode_rewards))
    
    return mean_100ep_reward


def moving_average(values, window):
    """
    Smooth values by doing a moving average
    :param values: (numpy array)
    :param window: (int)
    :return: (numpy array)
    """
    weights = np.repeat(1.0, window) / window
    return np.convolve(values, weights, 'valid')


def plot_results(log_folder, title='Learning Curve'):
    """
    plot the results

    :param log_folder: (str) the save location of the results to plot
    :param title: (str) the title of the task to plot
    """
    x, y = ts2xy(load_results(log_folder), 'timesteps')
    y = moving_average(y, window=1)
    # Truncate x
    x = x[len(x) - len(y):]

    fig = plt.figure(title)
    plt.plot(x, y)
    plt.xlabel('Number of Timesteps')
    plt.ylabel('Rewards')
    plt.title(title + " Smoothed")
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=None)
    parser.add_argument('env_id', nargs='?', default='Diplomacy_Strategy-v0', help='Select the environment to run')
    args = parser.parse_args()

    env = make_env(args.env_id)
    #train(env, total_timesteps)
    evaluate(env, train_timesteps)
    plot_results(log_dir)

