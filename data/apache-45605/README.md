## Apache ##
###Bug [#45605](http://issues.apache.org/bugzilla/show_bug.cgi?id=45605) ###

#### Bug type :  atomicity violation####

##### Functions involved : ######
 * ap_queue_info_set_idle in server/mpm/worker/fdqueue.c
 * listener_thread in server/mpm/worker/worker.c


###### Buggy interleaving : ######
|thread 1: listener_thread(...)|thread 2: ap_queue_info_set_idle(...)|
|---| ---|
||...|
||prev_idlers = queue_info->idlers;|
||queue_info->idlers++;|
||...|
|if (queue_info->idlers == 0) {}||
|...||
|queue_info->idlers--;||
|...||
|if (queue_info->idlers == 0) {<br>&nbsp;&nbsp;&nbsp;&nbsp;lock(idlers_mutex);<br>&nbsp;&nbsp;&nbsp;&nbsp;...<br>&nbsp;&nbsp;&nbsp;&nbsp;if (queue_info->idlers == 0) {<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;cond_wait(wait_for_idler);||
||if(prev_idlers == 0) {<br>&nbsp;&nbsp;&nbsp;&nbsp;apr_thread_mutex_lock(queue_info->idlers_mutex);<br>&nbsp;&nbsp;&nbsp;&nbsp;apr_thread_cond_signal(queue_info->wait_for_idler);<br>&nbsp;&nbsp;&nbsp;&nbsp;apr_thread_mutex_unlock(queue_info->idlers_mutex);<br>}|
|&nbsp;&nbsp;&nbsp;&nbsp;}<br>&nbsp;&nbsp;&nbsp;&nbsp;unlock(idlers_mutex);<br>}||
|queue_info->idlers--;||

##### Explanation : #####
If `idlers` is set to 0 before this execution, `ap_queue_info_set_idle` would put it to 1, which would then be decremented by `listener_thread`. Thus, `ap_queue_info_set_idle` would send the signal when computing `prev_idlers == 0`, even though this is outdated, leading `listener_thread` to put `idlers` to -1, causing an underflow.

##### Credits #####
Thanks to jieyu for having documented this bug in his [concurrency bugs repository](https://github.com/jieyu/concurrency-bugs)
More information are also available there.
