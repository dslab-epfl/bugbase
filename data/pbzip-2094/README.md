## Pbzip2 ##
###Bug in version 0.9.4, no bug report found ###

#### Bug type : order violation ####

##### Functions involved : ######
 * main in pbzip2.cpp
 * consumer in pbzip2.cpp


###### Buggy interleaving : ######
|thread 1: void main(...)|thread 2: void \*consumer(void \*q)|
|---| ---|
|...||
|ret = pthread_create(&con, NULL, consumer, fifo);||
|...|...|
|pthread_join(output, NULL);||
|...|if (allDone == 1) {|
|fifo->empty = 1;||
|//reclaim memory||
|queueDelete(fifo);||
|fifo = NULL;||
||&nbsp;&nbsp;&nbsp;&nbsp;pthread_mutex_unlock(fifo->mut);|
||}|

##### Explanation : #####
The main threads creates consumers to compress the data, but it only waits on the output thread.
If a consumer has not finished its task before the output thread has finished, the main thread will delete the fifo object.
Therefore, when unlocking the mutex, a consumer can access a null pointer and will segfault

##### Credits #####
Thanks to jieyu for having documented this bug in his [concurrency bugs repository](https://github.com/jieyu/concurrency-bugs)
More information are also available there.