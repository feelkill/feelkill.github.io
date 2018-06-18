---
layout: post

title: "论文：关于乐观并发控制方案的观察研究"

date: 2018-06-18

category: 2018年

keywords: 乐观并发控制， OCC， 

---

## 摘要

OCC的一个假设前提是，**事务过程中的读写冲突是非常少的**。在事务提交之前，需要校验是否有冲突发生。**冲突发生的解决方案主要是事务回滚**。本论文主要介绍和比较了两种OCC方案，并且研究了一些实现上的细节，以及与两阶段锁协议的优缺点比较。

## 简介

先定义事务串行化的概念：be serializable or has the property of serial equivalece if there exists at least one serial shedule of execution leading to the same results for every transaction and to the same final state of the database. （注解：这一概念的定义与前面介绍OCC文章中对此的定义是非常相似的，可以直接参考）。

传统使用两阶段锁协议。论文[On Optimistic Control Methods for Concurrency Control](http://feelkill.github.io/pieces_of_work/concurrent_control/On%20Optimistic%20Methods%20for%20Concurrency%20Control.pdf)指出了这种方法存在的一些缺点。

### OCC基本原则

OCC的设计是为了减少加锁负载，它的一个假设前提是：事务中的冲突是非常少见的。因而，它把冲突检测延迟到了事务提交的时间点。一旦发生冲突，该事务就撤消回滚。OCC把事务分成了三个阶段：read phase; validation phase; write phase。其中， read phase的结束对应了DBMS的EOT(end of transaction)。

#### Read phase

对于每一个事务，都对应一个事务缓存（transaction buffer），该缓存由DBMS来控制和维护。只读对象可能存在于该缓存中，也可能不存在； 如果一个对象不存在缓存中，就需要从system buffer或者磁盘上来读取该对象。然而，被修改的对象是肯定存在于事务缓存中的；一个事务中，对同一个对象的反复修改是在本地副本上进行的。

事务修改的粒度可以是页，也可以是记录。使用前者冲突会更大，一般使用后者。（备注：在该阶段，如果要直接对全局数据库对象进行修改，而又不想采取加锁策略，就需要使用时间戳方案，这是另一类的并发控制了）。

#### Validation phase

这个阶段检查是否与其他并行事务发生冲突。如果确定发生冲突，则该事务回滚； 否则的话， 该事务正常提交。

#### Write phase

只读事务不存在此阶段，只有写事务才有。在这个阶段，需要REDO日志来防止介质故障，可以在2PC协议的第一个阶段完成。

此阶段所述的“写”并不是指把数据刷到磁盘上，而是指数据的变更直接全局可见。

### Validation of Serial Equialence

为了验证串行化准则，需要为事务赋于一个唯一的事务号Ti，赋值时间点可以在read phase的结束时，也可以延迟到验证成功之后。每次赋于事务号之后，TNC(事务号计数器)就自增1。If Ti finishes its read phase before Tj (i.e. Ti is validated before Tj), then Ti < Tj holds. ( 如果Ti在Tj之前结束了read phase，那么就说Ti < Tj是成立的)

为了能够串行化，事务Ti和Tj必须遵守下面的两个规则：

1. <u>规则1：no read dependency 不存在读依赖</u>
   - <u>规则1.1: Ti不会读取被Tj修改的数据</u>； 
   - <u>规则1.2:Tj不会读取被Ti修改的数据</u>；
3. <u>规则2：no overwriting 不存在覆盖写</u>
   - <u>Ti不会去覆盖写已经被Tj写入的数据，反之亦然</u>。



有两种基本方法来保证规则1和规则2：

1. Ti和Tj之间没有时间重叠；
2. Ti和Tj之间没有数据重叠（对象集没有重叠）；
3. 前两条可以分别适用于读集合和写集合，从而构造更多的协议。



这引出了如下的OCC可替代方案：

1. no time overlap at all 时间上根本没有重叠。 事务Ti和Tj完全是顺序是执行的，直接保证了规则1和规则2。
2. no time overlap of write pahse 写阶段没有时间重叠。
   - Tj事务不会读取已经被Ti修改了的数据。 这保证了规则1.2；
   - Ti完成了写阶段，之后Tj才开始了写阶段（没有时间重叠； Tj不能够影响Ti的读阶段）。这保证了规则1.1和1.2。
3. no object set overlap of write sets 写集合不存在对象重叠
   - Tj事务不会读取已经被Ti修改了的数据。 这保证了规则1.2；
   - Ti事务不会读取已经被Tj修改了的数据。（Ti读阶段和Tj写阶段不存在时间重叠；Tj不能够影响Ti读阶段）这保证了规则1.1；
   - Ti和Tj的写集合是分离的（没有数据重叠从而允许写阶段的并发执行）。这保证了规则2。
4. no object  set overlap of read sets and write sets 
   - 完全无依赖允许并发执行，从而保证了规则1 和规则2。

论文[On Optimistic Control Methods for Concurrency Control](http://feelkill.github.io/pieces_of_work/concurrent_control/On%20Optimistic%20Methods%20for%20Concurrency%20Control.pdf)对前三种可选方法同样进行了别样论述。方法1是显而易见的。 方法2提供了OCC的最基本方法，下面的两种不同方法正是基于方法2进行论述的。

### Backward Oriented OCC



### Forward Oriented OCC

