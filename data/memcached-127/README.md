## Memcached ##
###Bug [#127](http://code.google.com/p/memcached/issues/detail?id=127) ###

#### Bug type :  atomicity violation (data race free) ####

##### Functions involved : ######
 * process_arithmetic_command in memcached.c
 * item_get in thread.c
 * add_delta in thread.c
 * do_add_delta in memcached.c
 * item_replace in thread.c

###### Buggy interleaving : ######
|thread 1: process_arithmetic_command(...)|thread 2: process_arithmetic_command(...)|
|---| ---|
|...|...|
|it = item_get(key, nkey);||
||it = item_get(key, nkey);|
|...|...|
||add_delta(...) { <br>&nbsp;&nbsp;&nbsp;&nbsp;...<br>&nbsp;&nbsp;&nbsp;&nbsp;//operate on new item<br>&nbsp;&nbsp;&nbsp;&nbsp;item_replace(it, new_it)<br>&nbsp;&nbsp;&nbsp;&nbsp;...<br>}|
|add_delta(...) { <br>&nbsp;&nbsp;&nbsp;&nbsp;...<br>&nbsp;&nbsp;&nbsp;&nbsp;// operate on old item<br>&nbsp;&nbsp;&nbsp;&nbsp;memcpy(...,it, res);<br>&nbsp;&nbsp;&nbsp;&nbsp;...<br>}||

##### Explanation : #####
When two clients are incrementing/decrementing the same variable, the action might not be atomic.
If the place allocated for the variable is not enough, the action will have to first reallocate a new place in memory for it.
then it will have to copy it, and then increment it.
However, if, in the meantime, someone else modify the variable, it might be operating on the older
place in memory, which will cause the change to be lost.

##### Credits #####
Thanks to jieyu for having documented this bug in his [concurrency bugs repository](https://github.com/jieyu/concurrency-bugs)
More information are also available there.
