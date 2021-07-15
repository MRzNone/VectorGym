import numpy as np
from VectorGym import VectorGym

MAX_PATH_LEN = 100
NUM_TRAJECTORIES_BATCH = 10


# Dummy agent
class Agent:
    def __init__(self, in_shape, out_shape, discrete=True) -> None:
        self.out_shape = out_shape
        self.discrete = discrete

    def train(self, data):
        del data
        pass

    def select_action(self, obs):
        num_obs = len(obs)

        if self.discrete:
            actions = np.random.randn(num_obs, self.out_shape)
            actions = np.argmax(actions, 1)
        else:
            actions = np.random.randn(num_obs, self.out_shape)

        return actions


# append  items to arr only if the corresponding check is True
def _safe_append(arr, itms, checks, preproc=None):
    for a, it, c in zip(arr, itms, checks):
        if c:
            if preproc is not None:
                it = preproc(it)
            a.append(it)


if __name__ == '__main__':
    envs = VectorGym('CartPole-v1', 2)

    print(envs.action_space)
    print(envs.observation_space)

    # since action_space and observation_space
    # will be Tuple[orig_space, orig_space ...]
    agent = Agent(envs.observation_space.spaces[0].shape,
                  envs.action_space.spaces[0].n)

    paths = []
    for _ in range(NUM_TRAJECTORIES_BATCH):
        # initialize arrays to record path
        obs, acs, rewards, next_obs, terminals, image_obs = [
            [[] for _ in range(envs.num_envs)] for _ in range(6)
        ]

        # keep track of done for only running unfinished env
        done = np.array([False] * envs.num_envs)

        ob = envs.reset()
        step = 0
        while True:
            num_alive = sum(~done)

            # render and store images
            rendered_im = envs.render(select=~done)
            _safe_append(image_obs, rendered_im, ~done)

            # get observations from running envs
            t_ob = [o for o in ob if o is not None]
            # get actions
            actions_pred = agent.select_action(t_ob)
            # add 'None' paddings back for the API
            actions = [None] * envs.num_envs
            val_idx = np.where(~done)[0]
            for idx, t_ac in zip(val_idx, actions_pred):
                actions[idx] = t_ac
            # store actions
            _safe_append(acs, actions, ~done)

            #[(observation, reward, done, info), (observation, reward, done, info)]
            ret = envs.step(actions, select=~done)

            _safe_append(obs, ob, ~done)

            # process the transition (return from step) to avoid the None(s)
            ob = []
            for i, ret in enumerate(envs.step(actions, select=~done)):
                if ret is None:
                    ob.append(None)
                    continue
                t_ob, t_rew, t_done, _ = ret

                if t_done:
                    done[i] = True
                ob.append(t_ob)
                next_obs[i].append(t_ob)
                rewards[i].append(t_rew)

            step += 1
            # end the rollout if the rollout ended
            # HINT: rollout can end due to done, or due to max_path_length
            rollout_done = np.logical_or(step >= MAX_PATH_LEN, done)
            terminals.extend(rollout_done)

            if np.all(rollout_done):
                break
        t_paths = [
            path
            for path in zip(obs, image_obs, acs, rewards, next_obs, terminals)
        ]
        paths.extend(t_paths)

    agent.train(paths)

    envs.close()
