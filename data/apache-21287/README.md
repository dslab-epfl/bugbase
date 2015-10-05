## Apache ##
###Bug [#21287](http://issues.apache.org/bugzilla/show_bug.cgi?id=21287) ###

#### Bug type :  atomicity violation ####

##### Functions involved : ######
 * decrement_refcount in modules/experimental/mod_mem_cache.c


###### Buggy interleaving : ######
|thread 1: decrement_refcount(...)|thread 2: decrement_refcount(...)|
|---| ---|
|apr_atomic_dec(&obj->refcount);||
||apr_atomic_dec(&obj->refcount);|
||if (!obj->refcount) {<br>&nbsp;&nbsp;&nbsp;&nbsp;cleanup_cache_object(obj);<br>}|
|if (!obj->refcount) {<br>&nbsp;&nbsp;&nbsp;&nbsp;cleanup_cache_object(obj);<br>}|

##### Explanation : #####
the error is in `if(!apr_atomic_dec(&obj->refcount)`. This function should be atomic even though it isn't, leading to a double free.

##### Credits #####
Thanks to jieyu for having documented this bug in his [concurrency bugs repository](https://github.com/jieyu/concurrency-bugs)
More information are also available there.