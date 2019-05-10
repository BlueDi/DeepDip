import csv
from numpy import prod
import os
import pickle
import torch


class BaseAgent(object):
    def __init__(self, config, env, log_dir='./agent_logs'):
        self.model=None
        self.target_model=None
        self.optimizer = None

        self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        self.rewards = []

        self.action_log_frequency = config.ACTION_SELECTION_COUNT_FREQUENCY
        self.action_selections = [0 for _ in range(prod(env.observation_space.nvec))]


    def huber(self, x):
        cond = (x.abs() < 1.0).float().detach()
        return 0.5 * x.pow(2) * cond + (x.abs() - 0.5) * (1.0 - cond)


    def MSE(self, x):
        return 0.5 * x.pow(2)


    def save_w(self):
        fname_model = os.path.join(self.log_dir, 'model.pth')
        fname_optim = os.path.join(self.log_dir, 'optim.pth')

        if not os.path.isfile(fname_model):
            open(fname_model, 'w')
        if not os.path.isfile(fname_optim):
            open(fname_optim, 'w')

        torch.save(self.model.state_dict(), fname_model)
        torch.save(self.optimizer.state_dict(), fname_optim)


    def load_w(self):
        fname_model = os.path.join(self.log_dir, 'model.pth')
        fname_optim = os.path.join(self.log_dir, 'optim.pth')

        if os.path.isfile(fname_model):
            self.model.load_state_dict(torch.load(fname_model))
            self.target_model.load_state_dict(self.model.state_dict())

        if os.path.isfile(fname_optim):
            self.optimizer.load_state_dict(torch.load(fname_optim))


    def save_replay(self):
        fname_experiencereplay = os.path.join(self.log_dir, 'exp_replay_agent.pth')
        pickle.dump(self.memory, open(fname_experiencereplay, 'wb'))


    def load_replay(self):
        fname_experiencereplay = './saved_agents/exp_replay_agent.pth'
        if os.path.isfile(fname_experiencereplay):
            self.memory = pickle.load(open(fname_experiencereplay, 'rb'))


    def save_sigma_param_magnitudes(self, tstep):
        with torch.no_grad():
            sum_, count = 0.0, 0.0
            for name, param in self.model.named_parameters():
                if param.requires_grad and 'sigma' in name:
                    sum_+= torch.sum(param.abs()).item()
                    count += np.prod(param.shape)
            
            if count > 0:
                with open(os.path.join(self.log_dir, 'sig_param_mag.csv'), 'a') as f:
                    writer = csv.writer(f)
                    writer.writerow((tstep, sum_/count))


    def save_td(self, td, tstep):
        with open(os.path.join(self.log_dir, 'td.csv'), 'a') as f:
            writer = csv.writer(f)
            writer.writerow((tstep, td))


    def save_reward(self, reward):
        self.rewards.append(reward)


    def save_action(self, action, tstep):
        self.action_selections[int(action)] += 1.0/self.action_log_frequency
        if (tstep+1) % self.action_log_frequency == 0:
            with open(os.path.join(self.log_dir, 'action_log.csv'), 'a') as f:
                writer = csv.writer(f)
                writer.writerow(list([tstep]+self.action_selections))
            self.action_selections = [0 for _ in range(len(self.action_selections))]
