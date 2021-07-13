# VectorGym
Multi-process any(most) gym environment. Automatically parallel the given gym environment using [multiprocessing](https://docs.python.org/3/library/multiprocessing.html); VectorGym forwards all properties and function \(not starting with __\) of the underlying gym to you.

# Quick Start

Run gym environment in parallel.
```
from VectorGym import VectorGym

if __name__ == '__main__':
    envs = VectorGym('CartPole-v1', 2)

    print(envs.action_space)
    print(envs.observation_space)

    envs.reset()

    for _ in range(500):
        envs.render()
        actions = envs.action_space.sample()
        res = envs.step(actions)
        dones = [r[-2] for r in res]

        envs.reset(select=dones)

    envs.close()
```

# Install
```
git clone git@github.com:MRzNone/VectorGym.git
cd VectorGym
pip install -e .
```
