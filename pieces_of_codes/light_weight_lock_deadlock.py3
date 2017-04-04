#!/usr/bin/python3

#=================================================  generate requriing-holding lockid information area =====================================================



#=================================================  deadlock checking area =====================================================

def debug_holding_requiring_dict (d):
    # print holding_requiring_dict for debug
    for th, (holding_lockid, required_lockid) in d.items():
        print("%s holds lock %s, and requires lock %d" % (th, str(holding_lockid), required_lockid))

def debug_lockid2holder(d):
    # print lockid2holder for debug
    for lockid, thread in d.items():
        print("lock %d is held by %s" % (lockid, thread))

def pre_handle( holding_requiring_dict ):
    # first we will remove all the unused threads which don't cause deadlock.
    # 1): either holding-locks set or required-lock id is None.
    # 2): required-lock id is not in any holding-locks set, including itself
    unused_threads = []
    for thread_name , (holding_lockid,  required_lockid) in holding_requiring_dict.items():
        if holding_lockid[0] is None or required_lockid is None:
            unused_threads.append(thread_name)
    # the first time to remove
    for thread_name in unused_threads:
        del holding_requiring_dict[thread_name]

    # we collect all the required lockid
    required_lockid_list = []
    required_thread_list = []
    for required_thread , (holding_lockid,  required_lockid) in holding_requiring_dict.items():
        required_lockid_list.append(required_lockid)
        required_thread_list.append(required_thread)

    # if required-lock id is not in any holding-locks set,
    # remove it from holding_requiring_dict.
    # and by the way we build the map from lockid to its holder
    lockid2holder = {}
    total_size = len(required_lockid_list)
    idx_lockid = 0
    while idx_lockid < total_size:
        lockid = required_lockid_list[idx_lockid]
        required_thread = required_thread_list[idx_lockid]
        idx_lockid = idx_lockid + 1
        found = False
        for thread_name , (holding_lockid,  required_lockid) in holding_requiring_dict.items() :
            if lockid in holding_lockid:
                found = True
                # build map from required-lock id to thread list
                if lockid not in lockid2holder:
                    lockid2holder[lockid] = thread_name
                else:
                    print("WARNING: lockid(%d/%s) ocuurs in lockid2holder(%s) more than one time." % 
                        (lockid, thread_name, lockid2holder[lockid]))
                break
        if not found:
            del holding_requiring_dict[required_thread]
    # debug_lockid2holder(lockid2holder)
    return lockid2holder

def deadlock_itself (holding_requiring_dict):
    # if required-lock id is in its thead's holding-lock set,
    # deadlock happens and its thread name is returned.
    for thread_name, (holding_lockid,  required_lockid) in holding_requiring_dict.items():
        if required_lockid in holding_lockid:
            # print("\t %s require lock %d, and itself holds this lock." % (thread_name, required_lockid))
            return thread_name
    return None

def deadlock_ring (requiring_thread, holding_requiring_dict, lockid2holder):
    # holding relation:  holding thread <-->  lockid
    # requiring relation:  requiring thread <--> lockid
    requiring_list = []
    holding_list = []
    direct_ring_found = False
    requiring_lockid = holding_requiring_dict[requiring_thread][1]
    while True:
        # build requiring_list
        if (requiring_thread, requiring_lockid) in requiring_list:
            direct_ring_found = True
            break
        requiring_list.append( (requiring_thread, requiring_lockid) )
        # build holding_list
        if requiring_lockid not in lockid2holder:
            break
        holding_thread = lockid2holder[requiring_lockid]
        if (holding_thread, requiring_lockid) in holding_list:
            direct_ring_found = True
            break
        holding_list.append( (holding_thread, requiring_lockid) )
        # set next requiring_thread and requiring_lockid
        requiring_thread = holding_thread
        if requiring_thread in holding_requiring_dict:
            requiring_lockid = holding_requiring_dict[requiring_thread][1]
        else:
            # lock requiring and holding chain is broken,
            # so deadlock cannot happen.
            break;
    ####################
    if direct_ring_found:
        # return values:
        #    bool flag, whether direct-ring is found;
        #    requiring thread list;
        #    holding thread list;
        return (True, requiring_list, holding_list)
    else:
        return (False, requiring_list, holding_list)

def shrink( holding_requiring_dict, thread2lockid_list ):
    # shrink holding_requiring_dict by removing threads,
    # which exist in thread2lockid_list.
    for (thread, lockid) in thread2lockid_list:
        if thread in holding_requiring_dict:
            del holding_requiring_dict[thread]

def deadlock_ring_helper (holding_require_dict, lockid2holder):
    # deadlock ring with n itmes, for example:
    # 2-rings: thread [1] --> required [2]
    #          thread [2] --> required [1]
    # 3-rings: thread [1] --> required [2]
    #          thread [2] --> required [3]
    #          thread [3] --> reuqired [1]
    # and so on n-rings
    if 0 != len(holding_require_dict):
        # debug_holding_requiring_dict(holding_require_dict)
        while (len(holding_require_dict) != 0):
            # debug_holding_requiring_dict(holding_require_dict)
            # debug_lockid2holder(lockid2holder)
            requiring_thread = list( holding_require_dict.keys() )[0]
            deadlock, requiring_list, holding_list = deadlock_ring(
                requiring_thread, holding_require_dict, lockid2holder)
            if deadlock:
                return (True, requiring_list, holding_list)
            else:
                shrink(holding_require_dict, requiring_list)
                shrink(holding_require_dict, holding_list)
        return (False, [],  [])
    else:
        return (False, [],  [])

def check_deadlock(holding_requiring_dict):
    # holding_requiring_dict: locks information about holding and requiring
    # example:  thread x: ([holding locks], required lock)
    #           None --> none lock holding or required
    #    thread 1: ([lock1, lock2], lock3)
    #    thread 2: ([lock4, lock5], None) ----> remove
    #    thread 3: (None, None)  ---->  remove
    #    thread 4: (None, lock6) ---->  remove
    lockid2holder = pre_handle(holding_requiring_dict)
    thread_name = deadlock_itself(holding_requiring_dict)
    if thread_name is not None:
        lockid = holding_requiring_dict[thread_name][1]
        return (True, [(thread_name, lockid)], [(thread_name, lockid)])
    else:
        return deadlock_ring_helper(holding_requiring_dict, lockid2holder)

def describe_deadlock(requiring_relation, holding_relation):
    # describe deadlock which happend
    requiring_len = len(requiring_relation)
    holding_len = len(holding_relation)
    if requiring_len != holding_len:
        print("WARNING: size not match, requiring_relation %s, holding_relation %s" % 
            (str(requiring_relation), str(holding_relation) ))
    else:
        idx_rel = 0
        while idx_rel < requiring_len:
            print("\t %s require lockid %d, but its holer is %s." % (
                requiring_relation[idx_rel][0], requiring_relation[idx_rel][1], holding_relation[idx_rel][0]))
            idx_rel = idx_rel + 1

#=================================================  uttest area =====================================================

def uttest_results(testname, deadlock, requiring_list, holding_list):
    if (deadlock == False):
        print("[SUCCES] %s " % testname)
    else:
        print("[FAILED] %s " % testname)
        describe_deadlock(requiring_list, holding_list )

def uttest_ring1():
    deadlock, requiring_list, holding_list = check_deadlock( {"thread 1" : ([1], 1)} )
    uttest_results("uttest_ring1", deadlock, requiring_list, holding_list)

def uttest_ring1_with_none():
    deadlock, requiring_list, holding_list = check_deadlock( {"thread 1" : ([1], 1),
        "thread 2" : ([None], 1),
        "thread 3" : ([2], None),
        "thread 4" : ([None], None),
        "thread 5" : ([2], 3)
        } )
    uttest_results("uttest_ring1_with_none", deadlock, requiring_list, holding_list)

def uttest_ring2():
    deadlock, requiring_list, holding_list = check_deadlock( {"thread 1" : ([1], 2),
        "thread 2" : ([2], 1)} )
    uttest_results("uttest_ring2", deadlock, requiring_list, holding_list)

def uttest_ring3():
    deadlock, requiring_list, holding_list = check_deadlock( {"thread 1" : ([1], 2),
        "thread 2" : ([2], 3),
        "thread 3" : ([3], 1)} )
    uttest_results("uttest_ring3", deadlock, requiring_list, holding_list)

def uttest_ring4():
    deadlock, requiring_list, holding_list = check_deadlock( {"thread 1" : ([1], 2),
        "thread 2" : ([2], 3),
        "thread 3" : ([3], 4),
        "thread 4" : ([4], 1)} )
    uttest_results("uttest_ring4", deadlock, requiring_list, holding_list)

def uttest_ring5():
    deadlock, requiring_list, holding_list = check_deadlock( {"thread 1" : ([1], 2),
        "thread 2" : ([2], 3),
        "thread 3" : ([3], 4),
        "thread 4" : ([4], 5),
        "thread 5" : ([5], 1)} )
    uttest_results("uttest_ring5", deadlock, requiring_list, holding_list)

def uttest_noring6():
    deadlock, requiring_list, holding_list = check_deadlock( {"thread 1" : ([1], 2),
        "thread 2" : ([2], 3),
        "thread 3" : ([3], 4),
        "thread 4" : ([4], 5),
        "thread 5" : ([5], 6),
        "thread 6" : ([6], None) } )
    uttest_results("uttest_noring6", deadlock, requiring_list, holding_list)

def uttest_noring7():
    deadlock, requiring_list, holding_list = check_deadlock( {"thread 1" : ([1], 2),
        "thread 2" : ([2], 3),
        "thread 3" : ([3], 10),
        "thread 4" : ([4], 5),
        "thread 5" : ([5], 6),
        "thread 6" : ([6], 7),
        "thread 7" : ([7], 10)
        } )
    uttest_results("uttest_noring7", deadlock, requiring_list, holding_list)
def uttest_ring10():
    deadlock, requiring_list, holding_list = check_deadlock( {"thread 1" : ([1], 2),
        "thread 2" : ([2], 3),
        "thread 3" : ([3], 4),
        "thread 4" : ([4], 5),
        "thread 5" : ([5], 6),
        "thread 6" : ([6], 7),
        "thread 7" : ([7], 8),
        "thread 8" : ([8], 9),
        "thread 9" : ([9], 10),
        "thread 10" : ([10], 1)
        } )
    uttest_results("uttest_ring10", deadlock, requiring_list, holding_list)

if __name__ == '__main__':
    uttest_ring1()
    uttest_ring1_with_none()
    uttest_ring2()
    uttest_ring3()
    uttest_ring4()
    uttest_ring5()
    uttest_ring10()
    uttest_noring6()
    uttest_noring7()
