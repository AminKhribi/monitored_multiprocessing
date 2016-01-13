import multiprocessing
import logging
import time

import support_monitored_mp

logger = logging.getLogger()

round_gb = lambda x: round(x / 1e9, 2)


def bound_mp(my_func=None, my_args=None, range_args=None, max_idx=None, sleep_time=None, security_mem=None, name=None, daemon=False, method='async', verbose=True):
    """
    multiprocessing with RAM monitoring.

    my_func: function to be computed in parallel

    my_args: dictionnary of arguments to be passed to my_func. This dictionnary must not contain parameters that parallelization will loop over
    
    range_args: dictionnary of arguments to loop over for parallelization. exple {'x1': [1, 2, 3, 4], 'x2': [5, 6, 7, 8, 9]}. all arguments must have exact number
                of values to loop over, as the loop will be in a zip form.

    max_idx: integer of number of steps requiered to check the memory

    sleep_time: integer of seconds to wait before checking the memory. This is useful for tasks using lots of RAM in order to give them time to reveal their needed RAM
    
    security_mem: at toal_memory - security_mem, the code will stop launching tasks and wait for launched ones. Should increase with computation needs.
    
    daemon: bool, whether or not to save memory usage using a daemon that checks memory use every one second, and returns a png.
    
    method: 'queue' or 'async'. if 'queue', use queue system with input and output tasks shared between multiple processes. If 'async', use pools of processes, launched asynchronously.

    This may not work for lambda functions.
    One should also not use huge arrays parallelized, as pool object can crash:
    http://stackoverflow.com/questions/24406937/scikit-learn-joblib-bug-multiprocessing-pool-self-value-out-of-range-for-i-fo
    """

    list_items = list(range_args.items())
    if len(set([len(i[1]) for i in list_items])) != 1:
        raise ValueError("range paramaters should be equal")

    l = len(list_items[0][1])  # same length (check)

    vars_list = [i[0] for i in list_items]  # variables names
    values = [i[1] for i in list_items]  # variables range

    vars_values = [[val[i] for val in values] for i in range(l)]

    if daemon:
        import matplotlib.pyplot as plt

        e = multiprocessing.Event()
        mgr = multiprocessing.Manager()

        mem_track = mgr.list()
        d = multiprocessing.Process(name='daemon', target=support_monitored_mp.worker_daemon, args=(mem_track, e))
        d.daemon = True

        d.start()

    if method == 'async':
        result_list = support_monitored_mp.async_mp(vars_values=vars_values, vars_list=vars_list, my_args=my_args, max_idx=max_idx, my_func=my_func,
                                                    sleep_time=sleep_time, security_mem=security_mem, verbose=verbose)
    else:
        result_list = support_monitored_mp.queue_mp(vars_values=vars_values, vars_list=vars_list, my_args=my_args, my_func=my_func)

    if daemon:
        time.sleep(sleep_time)

        e.set()

        mem_track = list(mem_track)

        time_list = [m[1] for m in mem_track]
        mem_list = [m[0] for m in mem_track]

        fig = plt.figure()
        plt.plot(time_list, mem_list)
        fig.savefig("memory_usage_" + str(name) + ".png")

    return result_list
