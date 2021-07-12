import os
from multiprocessing import Process, Pipe, Queue
from multiprocessing.connection import Connection
from functools import partial
from concurrent.futures.thread import ThreadPoolExecutor
from concurrent.futures import Future
import dill

import gym


def strip_hidden_func(ls):
    """
    Take out all str stating with "__".
    """
    return list(filter(lambda n: not n.startswith('__'), ls))


class QueueExit:
    pass


class DAO:
    def __init__(self, dic):
        for k, v in dic.items():
            setattr(self, str(k), v)


def process_rec(con: Connection):
    res = con.recv()
    return res


class GymWorker(Process):
    def __init__(
        self,
        *args,
        request_queue: Queue,
        ans_con: Connection,
        **kwargs,
    ):
        super().__init__()

        self.request_queue = request_queue
        self.ans_con = ans_con
        self.env = gym.make(*args, **kwargs)

        self._callable_dic = self._get_attr_callable_dict()

    def __dir__(self):
        orig_ls = super().__dir__()

        gym_ls = []
        cur_env = self.env
        while True:
            gym_ls.extend(strip_hidden_func(dir(cur_env)))
            if 'env' in dir(cur_env):
                cur_env = cur_env.env
            else:
                break
        return set(orig_ls + gym_ls)

    def get_attr_callable_dict(self):
        return self._callable_dic

    def _get_attr_callable_dict(self):
        attr_dic = {}
        cur_env = self.env
        while True:
            #             gym_ls += strip_hidden_func(dir(cur_env))
            attr_dic.update({
                k: callable(getattr(cur_env, k))
                for k in strip_hidden_func(dir(cur_env))
            })
            if 'env' in dir(cur_env):
                cur_env = cur_env.env
            else:
                break

        return attr_dic

    def __getattr__(self, name):
        """
        Forward any call to env.
        """
        def method(self, name, *args, **kwargs):
            # support gettign attribute
            attr = getattr(self.env, name)

            if callable(attr):
                return attr(*args, **kwargs)
            else:
                # check picklable

                if dill.pickles(attr):
                    return attr
                else:
                    pickable_attrs = {
                        k: getattr(attr, k)
                        for k in dir(attr)
                        if dill.pickles(getattr(attr, k)) and '__' not in k
                    }

                    dao = DAO(pickable_attrs)
                    return dao

        return partial(method, self, name)

    def run(self):
        print(f'{os.getpid()}: Worker started')

        for ret in iter(self.request_queue.get, None):
            if isinstance(ret, QueueExit):
                break

            method_name, args, kwargs = ret

            res = getattr(self, method_name)(*args, **kwargs)
            self.ans_con.send(res)

        print(f'{os.getpid()}: Worker exited')


class ProcessGym:
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        # should be very small
        self.request_queue = Queue(5)
        self.con, self.worker_con = Pipe()
        self.gym_worker = GymWorker(*args,
                                    request_queue=self.request_queue,
                                    ans_con=self.worker_con,
                                    **kwargs)

        # make getting result async
        self.future_executor = ThreadPoolExecutor(max_workers=1)
        self.gym_worker.start()

        self.gym_callable = self.get_attr_callable_dict().result()

    def close(self):
        self.request_queue.put(QueueExit())
        self.request_queue.close()
        self.con.close()
        self.worker_con.close()
        self.gym_worker.join()
        self.gym_worker.close()
        self.future_executor.shutdown()

    def __getattr__(self, name):
        # forward to gym worker and
        def method(que, con, future_executor, method_name, *args,
                   **kwargs) -> Future:
            que.put((method_name, args, kwargs))

            # make getting result async
            # use a thread to avoid copying data over process
            # TODO: speed up data passing
            async_res = future_executor.submit(process_rec, con)

            return async_res

        return partial(method, self.request_queue, self.con,
                       self.future_executor, name)


if __name__ == '__main__':
    env = ProcessGym('CartPole-v1')

    env.reset()

    for _ in range(500):
        env.render().result()
        done = env.step(env.action_space().result().sample()).result()[-2]

        if done:
            env.reset().result()

    env.close()
