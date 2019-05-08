import logging
from gym.envs.registration import register

logger = logging.getLogger(__name__)

# This is what registers the "Diplomacy-v0" environment to be used by agents
# For a successful registration, simply use "import gym_diplomacy" when initializing agents
register(
    id='Diplomacy-v0',
    entry_point='gym_diplomacy.envs:DiplomacyEnv'
)

register(
    id='Diplomacy_Strategy-v0',
    entry_point='gym_diplomacy.envs:DiplomacyStrategyEnv'
)

