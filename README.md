## Benchmark Script

This benchmark script was designed to simulate reads and writes against a server. The script allows you to specify the number of simultaneous threads, loops per thread and for how long the script will wait for each loop.

#### Write Mode

The Key used to store each value is composed by two numbers - thread and loop. Eg: KEY "10-20" represents the thread 10 and loop 20

This combination allows easy reading of the entire cache at any time. In other words, if you create a cache using Threads 100 and Loops 100, use the same configuration with the read mode to check the cache created.

If a write-read simulation is necessary - use the options BENCH_AS_READER=False and BENCH_PRINT_GET=True.

#### Read Mode

The reading mode uses the same structure created by the write mode. For example. if the cache was created with 1000 threads and 10000 loops, just set the same parameters with the read mode on, and it will read the cache created until the end.
s
#### Parameters

Options: Environment variables or script arguments 

- `BENCH_SERVER` or `-h`
  - Hostname (required-string)
- `BENCH_THREADS` or `-t`
  - number of threads. (required-int)
- `BENCH_THREAD_LOOPS` or `-l`
  - loops inside each thread. (required-int)
- `BENCH_FILE` or `-f`
  - JSON payload (path) used to populate the cache. (string) - not required if reader mode is on
- `BENCH_PRINT_GET` or `-v`
  - print the value using GET - reader or writer mode - default False (True/False)
  - if enabled when BENCH_AS_READER is false, it will write and then read inside the same thread.
- `BENCH_PORT` or `-p`
  - server port - default 6379. (int)
- `BENCH_USE_SSL` or `-s`
  - use SSL connection - default True. (True/False)
- `BENCH_MODE` or `-m`
  - set the script to write or read (int) 0 Read mode / 1 Write mode
- `BENCH_THREAD_LOOP_DELAY` or `-d`
  - delay between between each lops inside the thread - default 0.0 (float)

## Examples

#### Read Mode
`export BENCH_SERVER=replica.iconic-10gb-m5-2xlarge.m82bcs.apse2.cache.amazonaws.com`
`export BENCH_THREADS=50`
`export BENCH_THREAD_LOOPS=50`
`export BENCH_MODE=0`
`python3 benchmark.py`

#### Write Mode
`export BENCH_SERVER=\<servername\>`
`export BENCH_THREADS=100`
`export BENCH_THREAD_LOOPS=100`
`export BENCH_MODE=1`
`export BENCH_FILE=payload.json`
`python3 benchmark.py`

To keep the script running, use  `while :; do sleep 5; python3 benchmark.py ; done`
