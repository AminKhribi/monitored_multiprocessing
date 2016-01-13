# monitored_multoprocessing
custom python multiprocessing that checks the RAM state while launching tasks to prevent from crashing dur to memory errors

How to use:

call bound_mp with args:

my_func: function to be computed in parallel

my_args: dictionnary of arguments to be passed to my_func. This dictionnary must not contain parameters that                        parallelization will loop over
    
range_args: dictionnary of arguments to loop over for parallelization. exple {'x1': [1, 2, 3, 4], 'x2': [5, 6, 7, 8, 9]}.              all arguments must have exact number of values to loop over, as the loop will be in a zip form.

max_idx: integer of number of steps requiered to check the memory

sleep_time: integer of seconds to wait before checking the memory. This is useful for tasks using lots of RAM in order to              give them time to reveal their needed RAM
    
security_mem: at toal_memory - security_mem, the code will stop launching tasks and wait for launched ones. Should increase               with computation needs.
    
daemon: bool, whether or not to save memory usage using a daemon that checks memory use every one second, and returns a            png.
    
method: 'queue' or 'async'. if 'queue', use queue system with input and output tasks shared between multiple processes. If          'async', use pools of processes, launched asynchronously.

