import redis
import uuid
import _thread
import time
import os
import sys
import getopt
import json
import signal
from distutils import util

## Globals - Arguments
argPrintGet = False
argTotalThread = None
argThreadTotalLoops = None
argThreadLoopDelay = 0.0
argJsonFile = None
argServer = None
argServerSSL = True
argServerPort = 6379
argAsReader = True

# Globals - Others
jsonObject = None
threadExitStatus = None
redisClient = None
threadErrorsLimit = 2
threadErrorsDelay = 0.2

# Sizes
# 2893973  = 19GB / (Threads 100 Loops 100000)
# 1523143  = 10GB / (Threads 100 Loops 15231)
# 761571   = 5GB  / (Threads 100 Loops 7615)
# 152314   = 1GB  / (Threads 100 Loops 1520)

## Command 
# WRITER - python3 generate-data.py -h master.elasticache-autoscaling-m5-xlarge.m82bcs.apse2.cache.amazonaws.com -t 10 -l 10 -f payload.json
# READER - python3 generate-data.py -h master.elasticache-autoscaling-m5-xlarge.m82bcs.apse2.cache.amazonaws.com -t 10 -l 10 -r True -v True

def readJsonObject():
  global jsonObject
  with open(argJsonFile) as jsonFileContent:
    jsonObject = json.load(jsonFileContent) 

def arguments():
    global argPrintGet
    global argTotalThread
    global argThreadTotalLoops
    global argServer
    global argJsonFile
    global argServerSSL    
    global argServerPort
    global argAsReader
    global argThreadLoopDelay

    try:
        opts, args = getopt.getopt(sys.argv[1:],"h:t:l:v:f:p:s:m:d:", ["-help"])
    except getopt.GetoptError:
        printHelp()
        sys.exit(2)

    optsDict = dict(opts)

    if "-help" in optsDict:
        printHelp()
        sys.exit(0)
    
    if "-h" not in optsDict:
        if "BENCH_SERVER" not in os.environ:
            raise Exception("Cannot find the host, use -h or BENCH_SERVER")

    if "-t" not in optsDict:
        if "BENCH_THREADS" not in os.environ:
            raise Exception("Cannot find the thread number, use -t or BENCH_THREADS")  

    if "-l" not in optsDict:
        if "BENCH_THREAD_LOOPS" not in os.environ:
            raise Exception("Cannot find the thread loop number, use -l or BENCH_THREAD_LOOPS")

    if "BENCH_MODE" not in os.environ:
        raise Exception("Are you trying to use read or write mode? use -m or BENCH_MODE")

    if "-r" not in optsDict:
        if "BENCH_MODE" in os.environ and os.environ["BENCH_MODE"] == 1:
            if "-f" not in optsDict:
                if "BENCH_FILE" not in os.environ:
                    raise Exception("Cannot find the json file, use -f")      

    for o, a in opts:
      if o == "-h":
          argServer = a
      elif o in ("-t"):
          argTotalThread = int(a) 
      elif o in ("-l"):
          argThreadTotalLoops = int(a)          
      elif o in ("-f"):
          argJsonFile = a   
      elif o in ("-v"):
          argPrintGet = bool(util.strtobool(a))
      elif o in ("-p"):
          argServerPort = int(a)  
      elif o in ("-s"):
          argServerSSL = bool(util.strtobool(a)) 
      elif o in ("-m"):
          argAsReader = True if int(a) == 0 else False   
      elif o in ("-d"):
          argThreadLoopDelay = float(a)  
                              
    if "BENCH_SERVER" in os.environ:
        argServer = os.environ["BENCH_SERVER"]
    if "BENCH_THREADS"in os.environ:
        argTotalThread = int(os.environ["BENCH_THREADS"])
    if "BENCH_THREAD_LOOPS" in os.environ:
        argThreadTotalLoops = int(os.environ["BENCH_THREAD_LOOPS"])
    if "BENCH_FILE"in os.environ:
        argJsonFile = os.environ["BENCH_FILE"]
    if "BENCH_PRINT_GET" in os.environ:
        argPrintGet = bool(util.strtobool(os.environ["BENCH_PRINT_GET"]))
    if "BENCH_PORT"in os.environ:
        argServerPort = int(os.environ["BENCH_PORT"])
    if "BENCH_USE_SSL" in os.environ:
        argServerSSL = bool(util.strtobool(os.environ["BENCH_USE_SSL"]))
    if "BENCH_MODE" in os.environ:
        argAsReader = True if int(os.environ["BENCH_MODE"]) == 0 else False 
    if "BENCH_THREAD_LOOP_DELAY" in os.environ:
        argThreadLoopDelay = float(os.environ["BENCH_THREAD_LOOP_DELAY"])
      
def connectRedis():
    global redisClient    
    redisClient = redis.StrictRedis(host=argServer, port=argServerPort, db=0, ssl=argServerSSL)
    redis.BlockingConnectionPool(timeout=5)

def elasticache(number, loops):
    count = 0
    errors = 0

    while True:
        if errors == threadErrorsLimit:
            print("Thread number %s couldn't connect after %s errors/" % (str(number),str(errors)))
            break

        try:
            uid = str(number) + "-" + str(count)
            
            if not argAsReader:
                redisClient.set(uid, str(jsonObject))
            
            if argPrintGet or argAsReader:
                getResult = redisClient.get(uid)

            if argPrintGet:
                print("UID %s" % uid)
                print(getResult)

            elif not argPrintGet and argAsReader:
                if getResult is not None:
                    lenString = str(len(getResult))
                else:
                    lenString = "0"

                print("UID %s - String size loaded - %s" % (uid, lenString))

            else:
                print("UID %s" % uid)

            count = count + 1

            time.sleep(argThreadLoopDelay)
            if count == loops:
                threadExitStatus[number] = True
                break

        except ConnectionError as e:
            print("Connection Error detected - waiting to re connect")
            with open("logs/conn_" + uid + ".txt", "a") as file_object:
                # Append 'hello' at the end of file
                file_object.write(repr(e))

            
            time.sleep(threadErrorsDelay)
            errors = errors + 1
            
        except Exception as e:
            print("A non connection exception happened.")
            with open("logs/all_" + uid + ".txt", "a") as file_object:
                # Append 'hello' at the end of file
                file_object.write(repr(e))   

            time.sleep(threadErrorsDelay)
            errors = errors + 1
        

def threadManager():
  global threadExitStatus
  threadsCount = 0
  threadExitStatus = [False] * argTotalThread
  
  while True:
    _thread.start_new_thread(elasticache, (threadsCount,argThreadTotalLoops))
    threadsCount = threadsCount + 1

    if threadsCount == argTotalThread:
        break

def printHelp():
    print('Required -h host to connect. (string)')
    print('Required -t number of threads. (int)')
    print('Required -l loops inside each thread. (int)')
    print('Required -f json file payload used to set the cache. (string) - not required if reader mode is on')
    print('Required -m set the script to write or read (int) 0 Read / 1 Write')
    print('Optional -v for printing the object - reader or writer mode - default False (True/False)')
    print('Optional -p server port - default 6379. (int)')
    print('Optional -s connect using SSL - default True. (True/False)')
    print('Optional -d set the delay between lops within threads - default 0.0 (float)')

def signal_handler(signum, frame):
    signal.signal(signum, signal.SIG_IGN) # ignore additional signals
    print("Forcing the program to stop - killing all threads")
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    arguments()

    if argJsonFile is not None:
        readJsonObject()

    print("Working as Reader? %s" % str(argAsReader))

    connectRedis()
    threadManager()

    while False in threadExitStatus: pass

    totalExecutions = argTotalThread * argThreadTotalLoops
    print('Program exited successfully as all %s threads has been executed. Total of %s executons.' % (argTotalThread, totalExecutions))