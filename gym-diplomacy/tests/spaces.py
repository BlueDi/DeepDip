import gym.spaces
import numpy as np

NUMBER_OF_OPPONENTS = 7
NUMBER_OF_PROVINCES = 75

# observation_space = gym.spaces.Tuple((gym.spaces.Discrete(NUMBER_OF_PROVINCES),
#                                      gym.spaces.MultiDiscrete([NUMBER_OF_OPPONENTS, 2])))

observation_space_description = []

for i in range(NUMBER_OF_PROVINCES):
    observation_space_description.extend([NUMBER_OF_OPPONENTS, 2])

observation_space = gym.spaces.MultiDiscrete(observation_space_description)

print(len(observation_space.sample()))

observation = np.zeros(NUMBER_OF_PROVINCES * 2)
print(len(observation))

