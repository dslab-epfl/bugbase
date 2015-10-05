## Apache ##
###Bug [#25520](http://issues.apache.org/bugzilla/show_bug.cgi?id=25520) ###

#### Bug type :  atomicity violation and data race####

##### Functions involved : ######
 * ap_buffered_log_writer in modules/loggers/mod_log_config.c


###### Buggy interleaving : ######
|thread 1: ap_buffered_log_writer(...)|thread 2: ap_buffered_log_writer(...)|
|---| ---|
|idx = buf->outcnt;||
|s = &buf->output[idx];||
||idx = buf->outcnt;|
||s = &buf->outcnt[idx];|
||buf->outcnt += len;|
|buf->outcnt += len;||

##### Explanation : #####
The error in `ap_buffered_log_writer()` is due to the access to `buf->outcnt`, which is the index of the end of the buffer. As an update to the buffer is not protected, two threads may write from the same point of the buffer (before the update of the end by `buf->outcnt += len;`) leading to a log corruption. 

##### Credits #####
Thanks to jieyu for having documented this bug in his [concurrency bugs repository](https://github.com/jieyu/concurrency-bugs)
More information are also available there.
