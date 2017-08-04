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


## 与MVCC的关系

整体来讲，前一文章所述的元组的多版本信息也顶多是提供了一个可以进行并发控制的基础信息； 它需要与本节所述的快照以及规则结合起来，才能够决定一个元组的某个版本是否对一个快照可见的。

待补图

## 参考
* 《PostgreSQL数据库内核分析》
