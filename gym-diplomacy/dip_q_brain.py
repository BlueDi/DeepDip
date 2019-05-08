import argparse

import gym
# This import is needed to register the environment, even if it gives an "unused" warning
import gym_diplomacy
from gym import wrappers, logger


class RandomAgent(object):
    """The world's simplest agent!"""

    def __init__(self, action_space):
        self.action_space = action_space

    def act(self, observation, reward, done):
        return self.action_space.sample()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=None)
    parser.add_argument('env_id', nargs='?', default='Diplomacy-v0', help='Select the environment to run')
    args = parser.parse_args()

    # You can set the level to logger.DEBUG or logger.WARN if you
    # want to change the amount of output.
    logger.set_level(logger.DEBUG)

    env = gym.make(args.env_id)

    # You provide the directory to write to (can be an existing
    # directory, including one with existing data -- all monitor files
    # will be namespaced). You can also dump to a tempdir if you'd
    # like: tempfile.mkdtemp().
    outdir = '/tmp/random-agent-results'
    env = wrappers.Monitor(env, directory=outdir, force=True)
    env.seed(0)
    agent = RandomAgent(env.action_space)

    # episode_count = 10
    num_of_steps = 30
    reward = 0
    done = False

    ob = env.reset()

    steps_executed = 0
    episode = 0

    # TODO: Instead of having a loop with episode count, try to get num_of_steps working.
    # TODO: Probably the step function needs to be in a separate thread. It would make it easier to shutdown/stop.

    for i in range(num_of_steps):
        action = agent.act(ob, reward, done)

        ob, reward, done, info = env.step(action)
        steps_executed += 1

        logger.debug("Step number: {}".format(steps_executed))
        if done:
            logger.info("Game/episode {} has ended.".format(episode))
            episode += 1
            ob = env.reset()
            logger.info("Reset environment.")

        # Note there's no env.render() here. But the environment still can open window and
        # render if asked by env.monitor: it calls env.render('rgb_array') to record video.
        # Video is not recorded every episode, see capped_cubic_video_schedule for details.

    # Close the monitor and write monitor result info to disk
    env.close()

    # Explicitly close env, because Monitor does not call env close.
    # Issues has been fixed (https://github.com/openai/gym/pull/1023) but I still don't have the new version.
    # env.env.close()

