---
layout: post
title: "postgresql之Snapshot"
date: 2017-08-02
category: 数据库
keywords: postgresql, snapshot, 快照
---

## 概述

Postgres中快照的作用是什么？我觉得下面一句话应该是简要而中肯的：

> 快照记录了数据库当前某个时刻的活跃事务列表。通过快照，可以确定某个元组的版本对于当前快照是否可见。

这里面有几个主要的要点是,

* 快照其实是一组静态的数据，它记录的是某个时刻可以反应数据库中现有事务的状态，包括已提交、运行中、已回滚的；
* 必须还得有一些规则，再对照着快照和元组的版本信息，才能够综合地判定这个元组是否可见；
* 元组是否可见，是需要一个快照再加上一个判定规则才能够成立的；

对于元组的多版本信息，已有介绍。本文章主要介绍快照及其使用规则。

## 快照

postgres中快照的主要数据结构如下，它主要描述了某一时刻数据库内所有事务的状态。

```
typedef struct SnapshotData 
{ 
    SnapshotSatisfiesFunc satisfies;    /*行测试函数指针*/ 


    TransactionId xmin;            /* id小于xmin的所有事务更改在当前快照中可见 */ 
    TransactionId xmax;            /* id大于xmax的所有事务更改在当前快照中可见 */ 
    uint32        xcnt;            /* 正在运行的事务的计数 */ 
    TransactionId *xip;            /* 所有正在运行的事务的id列表 */ 
    /* 忽略了其他不关注的字段 */
} SnapshotData;

```

这个结构体就完整的表达了一个快照。它里边有什么呢？某个时刻点上整个数据库里所有事务的当前状态。首先要知道，数据库中的事务标识xid是递增的。结构体中的两个数值和一个数组将整个事务范围划分为了几个范围：

* <xmin, 表示了已经提交的事务的部分集合；
* \>xmax, 表示了未来的事务，比最大的活跃事务都要大的事务；
* xip[xcnt], 用数组存储了所有的活跃事务数值；
* 其他事务，指的是属于[xmin, xmax]但是又不在数组xip[]中的事务，它们的事务状态可能是已提交的，也可能是回滚了，由CLOG来决定；

这里需要注意的是，所有的事务范围被划分为了四个部分，所有活跃事务存储在了一个数组中，它们是一个点的集合，而不是一个连续范围的集合。这一部分的信息完全地表述了文章开始所述的第一点。紧接着，就需要说明与快照相对应的一些规则。不同的判定规则应用于不同的可见性判定，主要提供的判定规则有：

* SnapshotNowData/HeapTupleSatisfiesUpdate
* SnapshotSelfData
* SnapshotAnyData
* SnapshotToastData
* HeapTupleSatisfiesDirty
* HeapTupleSatisfiesMVCC
* HeapTupleSatisfiesVacuum

## 快照判定规则

其实对于所有的判定规则，源代码中在函数头上面的注释中都给出了给要义，可以将它们看为精华所在；这一点在理解透之后，就会意识到。

### HeapTupleSatisfiesMVCC

这个规则主要适用的场景就是对用户表的正常查询，所有从用户发起的、对表数据的查询select语句都会使用这个判定规则。

```
01020 /*
01021  * HeapTupleSatisfiesMVCC
01022  *      True iff heap tuple is valid for the given MVCC snapshot.
01023  *
01024  *  Here, we consider the effects of:
01025  *      all transactions committed as of the time of the given snapshot
01026  *      previous commands of this transaction
01027  *
01028  *  Does _not_ include:
01029  *      transactions shown as in-progress by the snapshot
01030  *      transactions started after the snapshot was taken
01031  *      changes made by the current command
01032  *
01033  * This is the same as HeapTupleSatisfiesNow, except that transactions that
01034  * were in progress or as yet unstarted when the snapshot was taken will
01035  * be treated as uncommitted, even if they have committed by now.
01036  *
01037  * (Notice, however, that the tuple status hint bits will be updated on the
01038  * basis of the true state of the transaction, even if we then pretend we
01039  * can't see it.)
01040  */
01041 bool
01042 HeapTupleSatisfiesMVCC(HeapTupleHeader tuple, Snapshot snapshot,
01043                        Buffer buffer)
```

符合以下条件的元组以该规则判定是可见的，

1. 生成该快照时刻，所有已提交的事务（涉及的元组）
2. 该事务的先前命令（生成的元组）

但是不包括

1. 该快照中的活跃事务（所涉及的元组）
2. 取得快照之后方才开始的事务
3. 本事务中本命令中做了修改（的元组）

上面规则判定的详情是在函数HeapTupleSatisfiesMVCC中实现的，可以参考下图。（待补充）

### SnapshotNowData

```
00322 /*
00323  * HeapTupleSatisfiesNow
00324  *      True iff heap tuple is valid "now".
00325  *
00326  *  Here, we consider the effects of:
00327  *      all committed transactions (as of the current instant)
00328  *      previous commands of this transaction
00329  *
00330  * Note we do _not_ include changes made by the current command.  This
00331  * solves the "Halloween problem" wherein an UPDATE might try to re-update
00332  * its own output tuples, http://en.wikipedia.org/wiki/Halloween_Problem.
00333  *
00352  */
00353 bool
00354 HeapTupleSatisfiesNow(HeapTupleHeader tuple, Snapshot snapshot, Buffer buffer)
```

符合以下条件的元组对于该规则是可见的，

1. 当前时刻所有已提交事务（涉及的元组）
2. 本事务前面命令所（更新的元组）

但是不包括符合如下条件的无组

1. 本事务中本命令中做了修改（的元组）

上面规则判定的详情是在函数HeapTupleSatisfiesNow中实现的，可以参考下图（待补充）。

### SnapshotSelfData

```
00141 /*
00142  * HeapTupleSatisfiesSelf
00143  *      True iff heap tuple is valid "for itself".
00144  *
00145  *  Here, we consider the effects of:
00146  *      all committed transactions (as of the current instant)
00147  *      previous commands of this transaction
00148  *      changes made by the current command
00149  *
00150  * Note:
00151  *      Assumes heap tuple is valid.
00152  *
00164  */
00165 bool
00166 HeapTupleSatisfiesSelf(HeapTupleHeader tuple, Snapshot snapshot, Buffer buffer)
```

符合以下条件的元组对于该规则是可见的，

1. 当前时刻所有已提交事务（涉及的元组）
2. 本事务前面命令所（更新的元组）
3. 本事务中本命令中做了修改（的元组）

可以对比一下与NOW规则的区别。上面规则判定的详情是在函数HeapTupleSatisfiesSelf中实现的，可以参考下图（待补充）。

### HeapTupleSatisfiesDirty

```
00830 /*
00831  * HeapTupleSatisfiesDirty
00832  *      True iff heap tuple is valid including effects of open transactions.
00833  *
00834  *  Here, we consider the effects of:
00835  *      all committed and in-progress transactions (as of the current instant)
00836  *      previous commands of this transaction
00837  *      changes made by the current command
00838  *
00839  * This is essentially like HeapTupleSatisfiesSelf as far as effects of
00840  * the current transaction and committed/aborted xacts are concerned.
00841  * However, we also include the effects of other xacts still in progress.
00842  *
00843  * A special hack is that the passed-in snapshot struct is used as an
00844  * output argument to return the xids of concurrent xacts that affected the
00845  * tuple.  snapshot->xmin is set to the tuple's xmin if that is another
00846  * transaction that's still in progress; or to InvalidTransactionId if the
00847  * tuple's xmin is committed good, committed dead, or my own xact.  Similarly
00848  * for snapshot->xmax and the tuple's xmax.
00849  */
00850 bool
00851 HeapTupleSatisfiesDirty(HeapTupleHeader tuple, Snapshot snapshot,
00852                         Buffer buffer)
```

符合以下条件的元组对于该规则是可见的，

1. 当前时刻所有已提交的事务和活跃事务（所涉及的元组）
2. 本事务前面命令（修改的元组）
3. 本事务当前命令（修改的元组）

可以再对比一个该规则与上面的规则的区别。上面规则判定的详情是在函数HeapTupleSatisfiesSelf中实现的，可以参考下图（待补充）。

### SnapshotAnyData

很简单的一种判定规则，即所有元组在这种规则下都是可见的。

### 其他

还有HeapTupleSatisfiesVacuum + SnapshotToastData + HeapTupleSatisfiesUpdate这三个是没有详细说明的，这可以在后面涉及到vacuum/toast/update的时候进行详细的说明。最后，可以对上面几个规则作一个对比图如下：

## 与MVCC的关系

整体来讲，前一文章所述的元组的多版本信息也顶多是提供了一个可以进行并发控制的基础信息； 它需要与本节所述的快照以及规则结合起来，才能够决定一个元组的某个版本是否对一个快照可见的。

待补图

## 参考
* 《PostgreSQL数据库内核分析》