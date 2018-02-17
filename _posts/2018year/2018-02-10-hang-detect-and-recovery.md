---
layout: post
title: "关于hang问题的detect和解决调研"
date: 2018-02-11
category: 2018年
keywords: 总结
---

## 论文: what is system hang and how to handle it

论文下载： [what is system hang and how to handle it](http://www.cse.unsw.edu.au/~jingling/papers/issre12.pdf)

这篇论文主要研究的是OS hang问题，而不是针对普通的应用程序。在这篇文章之前，就已经有许多研究OS hang问题的论文提出了各种方法，主要分为了几个：

* 增加硬件模块，适用范围有限；
* 通过修改OS内核代码，定制化程度比较高；
* 监测IO\CPU外部资源使用。

如何定义一个hang问题呢？主要的方法有两个：一是从系统内部来定义，OS无法调度进程、使用cpu，也无法响应用户输入； 另一个是从系统外部来定义，OS无法响应用户空间的程序，无法对外提供服务了。 论文采用的是第二种视角，从使用服务的视角来看。

该论文主要研究的是两类hang现象。第一类是无限循环，结合interrupt/preemption来进行划分子类。第二类是不确定的等待，进行子类划分包括了deadlock、持锁sleep、异常资源消耗以及资源慢释放。 在划分范围之后，本论文使用performance metrics来进行观察和探测是否有异常发生。接下来，主要需要解决2个问题，第一个是选择哪些指标项，第二个是利用这些指标项如何detect hang。

对于第一个问题，论文主要是通过“要解决问题的范围 + 测试benchmark + 全面的指标项”，然后进行实验总结。在最初给出的60+多个指标项中，最终选取了如下几个指标项： 

* CPU方面的sys/usr/iowait；
* 处理器方面的run/block/context switch； 
* 内存方面的pages swapped out per second/unused memory；
* 磁盘IO的util。

第二个问题的解决方法，主要是通过给定指标项的正常范围，然后来确定它们的异常范围。

基于以上，论文创建了一个自愈系统，用来探测、诊断和恢复OS hang问题。该系统将探测和诊断集中一身，只是把这部分功能划分为了两级（出于性能考虑）：轻量级的探测；重量级的诊断。 在平常的情况下，只会进行指标项的有效范围性判定。一旦指标项异常发生告警，就会触发重量级的诊断，同时采集相关的详细信息。判定到是确定的某个hang原因后，就后调起自愈方法进行恢复。
