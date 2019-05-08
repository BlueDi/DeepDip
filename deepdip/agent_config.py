import torch


class Config(object):
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        #PPO controls
        self.ppo_epoch = 3
        self.num_mini_batch = 32
        self.ppo_clip_param = 0.1

        #a2c controls
        self.num_agents = 8
        self.rollout = 16
        self.value_loss_weight = 0.5
        self.entropy_loss_weight = 0.001
        self.grad_norm_max = 0.5
        self.USE_GAE=True
        self.gae_tau = 0.95

        #algorithm control
        self.USE_NOISY_NETS=False
        self.USE_PRIORITY_REPLAY=False
        
        #Multi-step returns
        self.N_STEPS = 1

        #epsilon variables
        self.epsilon_start = 1.0
        self.epsilon_final = 0.01
        self.epsilon_decay = 30000
        self.epsilon_by_frame = lambda frame_idx: self.epsilon_final + (self.epsilon_start - self.epsilon_final) * math.exp(-1. * frame_idx / self.epsilon_decay)

        #misc agent variables
        self.GAMMA=0.99
        self.LR=1e-4

        #memory
        self.TARGET_NET_UPDATE_FREQ = 1000
        self.EXP_REPLAY_SIZE = 100000
        self.BATCH_SIZE = 32
        self.PRIORITY_ALPHA=0.6
        self.PRIORITY_BETA_START=0.4
        self.PRIORITY_BETA_FRAMES = 100000

        #Noisy Nets
        self.SIGMA_INIT=0.5

        #Learning control variables
        self.LEARN_START = 10000
        self.MAX_FRAMES  = 100000
        self.UPDATE_FREQ = 1

        #Categorical Params
        self.ATOMS = 51
        self.V_MAX = 10
        self.V_MIN = -10

        #Quantile Regression Parameters
        self.QUANTILES=51

        #DRQN Parameters
        self.SEQUENCE_LENGTH=8

        #data logging parameters
        self.ACTION_SELECTION_COUNT_FREQUENCY = 1000

