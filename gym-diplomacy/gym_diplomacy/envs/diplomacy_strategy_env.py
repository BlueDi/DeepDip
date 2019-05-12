import gym
from gym import spaces

import subprocess
import os
import signal
import atexit
import threading
import numpy as np

from gym_diplomacy.envs import proto_message_pb2
from gym_diplomacy.envs import comm

import logging

logging_level = 'DEBUG'
level = getattr(logging, logging_level)
logger = logging.getLogger(__name__)
logger.setLevel(level)

### LEVELS OF LOGGING (in increasing order of severity)
# DEBUG	    Detailed information, typically of interest only when diagnosing problems.
# INFO	    Confirmation that things are working as expected.
# WARNING	An indication that something unexpected happened, or indicative of some problem in the near future
# (e.g. ‘disk space low’). The software is still working as expected.
# ERROR	    Due to a more serious problem, the software has not been able to perform some function.
# CRITICAL	A serious error, indicating that the program itself may be unable to continue running.

### CONSTANTS
NUMBER_OF_ACTIONS = 3
NUMBER_OF_PLAYERS = 2#7
NUMBER_OF_PROVINCES = 8#75


def observation_data_to_observation(observation_data: proto_message_pb2.ObservationData) -> np.array:
    """
    This function takes a Protobuf ObservationData and generates the necessary information for the agent to act.

    :param observation_data: A Protobug ObservationData object.
    :return: A list with the structure [observation, reward, done, info]. Observation is an np array, reward is a float,
    done is a boolean and info is a string.
    """
    number_of_provinces = len(observation_data.provinces)

    if number_of_provinces != NUMBER_OF_PROVINCES:
        raise ValueError("Number of provinces is not consistent. Constant variable is '{}' while received number of "
                         "provinces is '{}'.".format(NUMBER_OF_PROVINCES, number_of_provinces))

    observation = np.zeros(number_of_provinces * 3)

    for province in observation_data.provinces:
        # simply for type hint and auto-completion
        province: proto_message_pb2.ProvinceData = province

        # id - 1 because the ids begin at 1
        observation[(province.id - 1) * 3] = province.owner
        observation[(province.id - 1) * 3 + 1] = province.sc
        observation[(province.id - 1) * 3 + 2] = province.unit

    reward = observation_data.previousActionReward
    done = observation_data.done
    info = {}

    return observation, reward, done, info


def action_to_orders_data(action, state) -> proto_message_pb2.OrdersData:
    """
    Transforms the action list generated by the model into a OrdersData object that will be sent to Bandana.
    :param action: The list of the agent action.
    :return: OrdersData object with the representation of the set of orders.
    """
    player_units = get_player_units(state)
    orders_data: proto_message_pb2.OrdersData = proto_message_pb2.OrdersData()
    for unit in player_units:
        order = action[unit]
        if order == 0:
            clean_order = [0, 0]
        else:
            order = order - 1
            order_type, destination = divmod(order, NUMBER_OF_PROVINCES)
            clean_order = [order_type + 1, destination]

        new_order = orders_data.orders.add()
        new_order.start = unit
        new_order.action = int(clean_order[0])
        new_order.destination = int(clean_order[1])
    return orders_data


def get_player_units(state):
    player = 1
    units = state[2::3]
    player_units = [i for i, unit in enumerate(units) if unit == player]
    return player_units


class DiplomacyStrategyEnv(gym.Env):
    """
    The main OpenAI Gym class. It encapsulates an environment with
    arbitrary behind-the-scenes dynamics. An environment can be
    partially or fully observed.
    The main API methods that users of this class need to know are:
        step
        reset
        render
        close
        seed
    And set the following attributes:
        action_space: The Space object corresponding to valid actions
        observation_space: The Space object corresponding to valid observations
        reward_range: A tuple corresponding to the min and max possible rewards
    Note: a default reward range set to [-inf,+inf] already exists. Set it if you want a narrower range.
    The methods are accessed publicly as "step", "reset", etc.. The
    non-underscored versions are wrapper methods to which we may add
    functionality over time.
    """

    # Set this in SOME subclasses
    metadata = {'render.modes': []}
    reward_range = (-float('inf'), float('inf'))
    spec = None

    # Set these in ALL subclasses
    action_space = None
    observation_space = None

    metadata = {'render.modes': ['human']}

    ### CUSTOM ATTRIBUTES

    # BANDANA
    bandana_root_path: str = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                          "../../../bandana"))
    bandana_init_command: str = "./run-tournament.sh"
    bandana_subprocess = None

    # Communication
    server: 'DiplomacyThreadedTCPServer' = None

    # Env
    received_first_observation: bool = False
    waiting_for_action: bool = False
    response_available = threading.Event()
    limit_action_time: int = 0
    observation: np.ndarray = None
    action: np.ndarray = None
    info: dict = {}
    done: bool = False
    reward: float = 0
    current_agent = None

    terminate = False
    termination_complete = False


    def __init__(self):
        atexit.register(self.clean_up)

        self._init_observation_space()
        self._init_action_space()
        self._init_socket_server()


    def step(self, action):
        """Run one timestep of the environment's dynamics. When end of
        episode is reached, you are responsible for calling `reset()`
        to reset this environment's state.
        Accepts an action and returns a tuple (observation, reward, done, info).
        Args:
            action (object): an action provided by the environment
        Returns:
            observation (object): agent's observation of the current environment
            reward (float) : amount of reward returned after previous action
            done (boolean): whether the episode has ended, in which case further step() calls will return undefined results
            info (dict): contains auxiliary diagnostic information (helpful for debugging, and sometimes learning)
        """
        # When the agent calls step, make sure it does nothing until the agent can act
        while not self.waiting_for_action:
            pass

        self.action = action
        self.waiting_for_action = False

        # After setting 'waiting_for_action' to false, the 'handle' function should send the chosen action
        self.response_available.wait()

        return self.observation, self.reward, self.done, self.info


    def reset(self):
        """Resets the state of the environment and returns an initial observation.
        Returns: observation (object): the initial observation of the space.
        """
        # Set or reset current observation to None
        self.observation = None

        # In this case we simply restart Bandana
        if self.bandana_subprocess is not None:
            self._kill_bandana()
            self._init_bandana()
        else:
            self._init_bandana()

        # Wait until the observation field has been set, by receiving the observation from Bandana
        while self.observation is None:
            pass

        return self.observation


    def render(self, mode='human'):
        raise NotImplementedError


    def close(self):
        """Override _close in your subclass to perform any necessary cleanup.
        Environments will automatically close() themselves when
        garbage collected or when the program exits.
        """
        logger.debug("CLOSING ENV")

        self.terminate = True

        self.server.shutdown()

        if self.bandana_subprocess is not None:
            self._kill_bandana()

        self.termination_complete = True


    def clean_up(self):
        logger.debug("CLEANING UP ENV")

        if not self.termination_complete:
            self.close()


    def seed(self, seed=None):
        return


    def _init_bandana(self):
        logger.info("Starting BANDANA tournament...")
        logger.debug("Running '{}' command on directory '{}'."
                     .format(self.bandana_init_command, self.bandana_root_path))

        self.bandana_subprocess = subprocess.Popen(self.bandana_init_command, cwd=self.bandana_root_path, shell=True, preexec_fn=os.setsid)
        logger.info("Initialized BANDANA tournament.")


    def _kill_bandana(self):
        if self.bandana_subprocess is None:
            logger.info("No BANDANA process to terminate.")
        else:
            logger.info("Terminating BANDANA process...")

            # Killing the process group (pg) also kills the children, whereas killing the process would leave the
            # children as orphan processes
            os.killpg(os.getpgid(self.bandana_subprocess.pid), signal.SIGTERM)
            self.bandana_subprocess.wait()

            logger.info("BANDANA process terminated.")

            # Set current process to None
            self.bandana_subprocess = None


    def _init_observation_space(self):
        '''
        Observation space: [[province_id, owner, is_supply_center, has_unit] * number of provinces]
        The last 2 values represent the player id and the province to pick the order.
        Eg: If observation_space[2] is [5, 0, 0], then the second province belongs to player 5, is NOT a SC, and does NOT have a unit.
        '''
        observation_space_description = []
        for i in range(NUMBER_OF_PROVINCES):
            observation_space_description.extend([NUMBER_OF_PLAYERS, 2, NUMBER_OF_PLAYERS])

        self.observation_space = spaces.MultiDiscrete(observation_space_description)


    def _init_action_space(self):
        '''
        An action represents an order for a unit.
        Action space: [Order type for the unit, Destination province]
        Eg: Action [2, 5] proposes an order of type 2 related to the province with id 5.
        '''
        action_space_description = []
        action_space_row = [1 + (NUMBER_OF_ACTIONS - 1) * NUMBER_OF_PROVINCES]
        for _ in range(NUMBER_OF_PROVINCES):
            action_space_description.extend(action_space_row)
        self.action_space = spaces.MultiDiscrete(action_space_description)


    def _init_socket_server(self):
        self.server = comm.DiplomacyThreadedTCPServer(5000)
        self.server.handler = self.handle_request

        self.server_thread = threading.Thread(target=self.server.serve_forever)

        # Exit the server thread when the main thread terminates
        self.server_thread.daemon = True
        self.server_thread.start()
        logger.info("Started ThreadedTCPServer daemon thread.")


    def _terminate_socket_server(self):
        with self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("Shut down ThreadedTCPServer.")


    def handle_request(self, request: bytearray) -> None:
        request_data: proto_message_pb2.BandanaRequest = proto_message_pb2.BandanaRequest()
        request_data.ParseFromString(request)

        if request_data.type is proto_message_pb2.BandanaRequest.INVALID:
            raise ValueError("Type of BandanaRequest is INVALID.", request_data)

        observation_data: proto_message_pb2.ObservationData = request_data.observation
        self.observation, self.reward, self.done, self.info = observation_data_to_observation(observation_data)

        response_data: proto_message_pb2.DiplomacyGymOrdersResponse = proto_message_pb2.DiplomacyGymOrdersResponse()
        response_data.type = proto_message_pb2.DiplomacyGymOrdersResponse.VALID

        self.waiting_for_action = True
        while self.waiting_for_action:
            if self.done or self.terminate:
                # Return empty deal just to finalize program
                logger.debug("Sending empty deal to finalize program.")
                return response_data.SerializeToString()

        self.received_first_observation = True
        self.response_available.set()

        orders_data: proto_message_pb2.OrdersData = action_to_orders_data(self.action, self.observation)
        response_data.orders.CopyFrom(orders_data)

        return response_data.SerializeToString()


def main():
    gym = DiplomacyStrategyEnv()


if __name__ == "__main__":
    main()
