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
