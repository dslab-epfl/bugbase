## Transmission ##
###Bug [#1818](https://trac.transmissionbt.com/ticket/1818) in version 1.42 ###

#### Bug type : order violation ####

##### Functions involved : ######
 * tr_sessionInitFull in libtransmission/session.c
 * allocateBandwidth in libtransmission/bandwidth.c


###### Buggy interleaving : ######
|thread 1: tr_handle* tr_sessionInitFull(...)|thread 2: void allocateBandwidth(...)|
|---| ---|
|...|...|
|h->peerMgr = tr_peerMgrNew(h);||
||assert(tr_isBandwidth(b));|
|h->bandwidth = tr_bandwidthNew(h, NULL);||

##### Explanation : #####
the problematic variable is h->bandwidth.

It is created by `h->bandwidth = tr_bandwidthNew(h, NULL);` in session.c.

It is assumed to be always initialized while the program calls allocateBandwidth as allocateBandwidth is supposed to be called by a callback 500 msec after `t->peerMgr = tr_peerMgrNew(h);` is called.

However, this is not always true, as timing is not reliable, therefore `assert(tr_isBandwidth(b));` may be false.

##### Credits #####
Thanks to jieyu for having documented this bug in his [concurrency bugs repository](https://github.com/jieyu/concurrency-bugs)
More information are also available there.