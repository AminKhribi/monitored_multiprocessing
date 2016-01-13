import multiprocessing
import logging
import time
import psutil


logger = logging.getLogger()

round_gb = lambda x: round(x / 1e9, 2)


def worker(d, my_func_w, my_args_w):
    """ Worker of parallel computation
    """
    try:
        results = my_func_w(**my_args_w)
        d.append(results)
    except Exception as e:
        print('ERROR:', e)
    # results = my_func_w(**my_args_w)


def worker_queue(task_queue, done_queue, lock):
    # global ready_list
    while True:
        lock.acquire()
        tmp = task_queue.get()
        if tmp == None:
            break
        else:
            # func, args = task_queue.get(block=False)
            func = tmp[0]
            args = tmp[1]
            try:
                result = func(**args)
                done_queue.put(result)
            except Exception as e:
                logger.info(e)
        lock.release()
    return


def worker_daemon(d, e):
    """ Daemon that records memory usage every second
    """
    start_time = time.time()
    while not e.is_set():
        if time.time() > (start_time + 1):
            _, mem = is_enough_memory(0)
            d.append([mem, time.time()])
            start_time = time.time()


def is_enough_memory(max_mem=None, verbose=False):
    """ Checks memory use
    """
    used_mem = psutil.virtual_memory().used
    # logger.info('used memory', used_mem, 'Gb')
    output = (max_mem > used_mem)
    if verbose:
        logger.info("available memory {} Gb and used memory {} Bytes".format(round_gb(max_mem - used_mem), used_mem, output))

    return output, used_mem


def async_mp(vars_values=None, vars_list=None, my_args=None, max_idx=None, my_func=None, sleep_time=None, security_mem=None, verbose=True):

    max_mem = psutil.virtual_memory().total - security_mem

    n_workers = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=n_workers)

    mgr = multiprocessing.Manager()  # manager so that all processes can acces the result list

    result_list = mgr.list()
    for step, params in enumerate(vars_values):

        my_args_loop = my_args.copy()
        step += 1
        for name_var, param in zip(vars_list, params):
            my_args_loop[name_var] = param

        if verbose:
            logger.info("launching {}".format(round(100 * step / len(vars_values), 2)))

        time_to_check = True if ((step > max_idx) and step % max_idx == 0) else False

        # pool.apply_async(worker, (result_list, my_func, my_args_loop), error_callback=handle_error)
        pool.apply_async(worker, (result_list, my_func, my_args_loop))
        if time_to_check:
            logger.info('')
            logger.info('time to check')
            time.sleep(sleep_time)
            ok, mem = is_enough_memory(max_mem, True)
            if not ok:
                logger.info('overload: waiting for pool')
                pool.close()
                pool.join()
                pool.terminate()
                logger.info('done shuting pool')
                time.sleep(sleep_time)
                ok, mem = is_enough_memory(max_mem, True)
                if not ok:
                    logger.info("WARNING: processes not clearing memory.. may need a bigger machine")
                logger.info('creating new pool')
                pool = multiprocessing.Pool(processes=n_workers)

            else:
                logger.info('all good!')

    logger.info("Start: waiting for last pool")
    pool.close()
    pool.join()
    pool.terminate()
    logger.info("End: waiting for last pool")

    return list(result_list)


def queue_mp(vars_values=None, vars_list=None, my_args=None, my_func=None, max_wait=5):

    manager = multiprocessing.Manager()

    task_queue = manager.Queue()
    done_queue = multiprocessing.Queue()
    lock = multiprocessing.Lock()

    tasks = []
    for step, params in enumerate(vars_values):

        my_args_loop = my_args.copy()
        step += 1
        for name_var, param in zip(vars_list, params):
            my_args_loop[name_var] = param

        tasks.append((my_func, my_args_loop))

    logger.info("Setting tasks in input queue")
    for i in tasks:
        task_queue.put(i)

    task_queue.put(None)

    n_workers = multiprocessing.cpu_count()
    processes = [multiprocessing.Process(target=worker_queue, args=(task_queue, done_queue, lock)) for i in range(n_workers)]

    # task_queue.put('STOP')
    logger.info('Start: Start processes')
    for proc in processes:
        proc.start()
    logger.info("End: start processes")

    logger.info('Start: finish processes')
    for proc in processes:
        proc.join(max_wait)
        proc.terminate()
    logger.info('End: finish processes')

    logger.info('Start: Gather results')
    results = []
    while done_queue.qsize():
        item = done_queue.get()
        results.append(item)
    logger.info('End: Gather results')
    # done_queue.join()

    # kill remaining processes
    for process in processes:
        if process.is_alive():
            logger.info("proc ", process, "is alive")
            process.terminate()

    return results
