from functools import partial
from typing import Any, List, Callable, Tuple

from numpy import select

from VectorGym.process_worker import ProcessGym
from concurrent.futures import Future
import gym


class VectorGym:
    """
    Run multiple gym environments using multiprocessing.
    """
    def __init__(self,
                 env_name,
                 num_envs=1,
                 block=True,
                 return_attr_on_call=True,
                 **kwargs) -> None:
        """
        Create Vecortized gym environments. All arguments excep num_envs, block,
        and return_attr_on_call are passed to the gym environment. All calls will
        be processed concurrently on all environments. Select which environments
        to call with the select attribute. E.g. envs.step(action, select=[True, False])
        will only step the first environment. Wait for result and before returning if
        block is enabled. Block properties (e.g. env.action_space) if
        return_attr_on_call is enabled. If not blocked, concurrent.futures.Future
        is returned.

        Args:
            env_name (str): gym environment id
            num_envs (int, optional): Number of concurrent environment to create. Defaults to 1.
            block (bool, optional): If block before returning. Defaults to True.
            return_attr_on_call (bool, optional): If block calls to attributes
                Behaved weidly if disabled,
                e.g. envs.action_space() instead of envs.action_space. Defaults to True.
        """
        self.envs = [ProcessGym(env_name, **kwargs) for _ in range(num_envs)]
        self.num_envs = num_envs
        self.block = block
        self.return_attr_on_call = return_attr_on_call

        self._env_attr_callable = self.envs[0].gym_callable

        # spaces for multi-env
        incarnate = lambda x: x.result() if isinstance(x, Future) else x

        # action_space
        single_action_space = incarnate(self.action_space)
        self.action_space = gym.spaces.Tuple(
            [single_action_space for _ in range(num_envs)])

        # observation_space
        single_obs_space = incarnate(self.observation_space)
        self.observation_space = gym.spaces.Tuple(
            [single_obs_space for _ in range(num_envs)])

    def _deal_gym_methods(self,
                          name: str) -> Callable[[List[Any]], List[Future]]:
        """
        Generate function for the call to remote environments.
        """
        def method(self,
                   *args,
                   name=name,
                   select=None,
                   **kwargs) -> List[Future]:
            if select is None:
                select = [True] * self.num_envs
            assert len(select) == self.num_envs

            # check args are arrays
            for arg in args:
                assert '__iter__' in dir(arg), "Need list arg for vector env"
            for _, v in kwargs:
                assert '__iter__' in dir(v), "Need list arg for vector env"

            # make payload
            payload = []
            for i in range(self.num_envs):
                t_arg = [arg[i] for arg in args]
                t_kwarg = {k: v[i] for k, v in kwargs.items()}

                payload.append((t_arg, t_kwarg))

            # dispatch and wait
            res_futures = [
                getattr(env, name)(*t_args, **t_kwargs) if t_select else None
                for env, (
                    t_args,
                    t_kwargs), t_select in zip(self.envs, payload, select)
            ]

            return res_futures

        return partial(method, self, name=name)

    def close(self) -> None:
        [env.close() for env in self.envs]

    def __getattr__(
            self, name: str
    ) -> Tuple[Callable[[List[Any]], List[Future]], Any, Future]:
        """
        Forward calls to the environments. Deal with block and return_attr_on_call.
        """
        if name not in self._env_attr_callable:
            raise AttributeError

        attr = self._deal_gym_methods(name)

        if self._env_attr_callable[name] and self.block:
            res = lambda *args, **kwargs: list(
                map(lambda f: None
                    if f is None else f.result(), attr(*args, **kwargs)))
            # res = lambda *args, **kwargs: attr(*args, **kwargs)
        elif not self._env_attr_callable[name] and (self.return_attr_on_call
                                                    or self.block):
            futures = attr(select=[True, *([False] * (self.num_envs - 1))])
            res = futures[0].result()
        return res


if __name__ == '__main__':
    envs = VectorGym('CartPole-v1', 2)

    envs.reset()

    for _ in range(500):
        envs.render()
        actions = envs.action_space.sample()
        res = envs.step(actions)
        dones = [r[-2] for r in res]

        envs.reset(select=dones)

    envs.close()
