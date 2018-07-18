---
layout: post

title: "论文：关于并发控制论文集的小结"

date: 2018-07-14

category: 2018年

keywords: 并发控制，悲观并发控制， 乐观并发控制， OCC，

---

## 论文：On Concurreny Control by Multiple Versions

### 时间

 1982 ACM

### 主要贡献

定义了MVSR（MultiVersion Serializability），并给出了关于MVSR的几个定理和推论。

### 关键要点

#### 数据多版本的核心思想

更新数据并不覆盖已有的数据，而是新增一个版本的数据；这样，当并发读请求时，可以选择一个合适版本的数据来响应。

#### 串行化与MVSR的关系

并发控制有两个基本的目标：保证尽可能多的并行； 保证并发执行的正确性。而串行化（ Serializability ）是实现后者目标的主要方法。

实现并发控制的路径是多样的，其中多版本数据是常见的一种。MVSR就是实现多版本数据方法中、保证并发正确性的一个方法理论。

#### 相关定理和推论

定理1： MVSR是一个完全NP问题

定理2： 当调度s是一个有向不循环图时，它是一个MVSR

定理3： 在action模型中，MVSR等同于串行化（Serializability）

定理4： MVSR是多版本方法中能够达到并行度的上限值。也就是说，serializability 相当于一个版本，MVSR相当于无穷个版本；在这二者之间，存在一个无限的、严格的、包括特级关系（infinite strict hierarchy）。 如果可以保留数据的k+1个版本的话，并发控制的调度就有多于k种。 （By keeping up to k+1 versions of each entity one can “serialize” more schedules than with k. ）

定理5： DMVSR cannot be scheduled on-line, even for the restricted two-step model. 其中，满足定理2的MVSR称为DMVSR。 

## 论文：Concurrency Control in Distributed Database Systems

### 时间

1981年 ACM

### 主要贡献

可以看作是分布式数据库中并发控制技术的一个总述。它将并发问题分解为两个子问题：读写冲突；写写冲突。然后，针对这两个子问题介绍了相应的解决方案，主要是加锁、时间戳两个方法。

### 关键要点

本论文认为，并发控制算法的正确性应该从用户的期望进行定义。有两点可验证：1） 期望1，用户提交给DB的所有事务最终都是执行完成的；2） 期望2，用户无论是以并行还是独占的方法提交了一个事务，它的执行结果是相同的。

本论文同样是从串行化的概念出发，将冲突问题分解为了**读写冲突**、**写写冲突**两个子问题，给出了几个定理。

- 定理1定义了a serialization order，它是从conflict的角度来定义可串行化的概念。由此也看出，并发控制本质上是对这些冲突操作的控制；实现这些控制的算法就称为a synchronization technique.

- 定理2是定理1的延伸。读写冲突和写写冲突可以分别采取不同的技术来解决，然后保证存在一个整体上的serialization order来使得可串行化。

引入了两个概念：synchronization technique 用来指解决读写冲突的方法；concurrency control 用来指解决写写冲突的方法。

#### SYNCHRONIZATION TECHNIQUES BASED ON TWO-PHASE LOCKING

锁的从属管理由两个规则来保证：1） 锁的冲突模式，不同的事务不可能同时拥有冲突模式的锁； 2） 2PL协议。其中，第1点主要取决于锁的冲突/排他模式，第2点主要指两阶段锁协议。

2PL主要分为两个阶段：

1. growing phase，在该阶段中只能够获取锁，不能够释放锁。
2. shrinking phase，一旦开始释放第一个锁，那么就不能够再获取锁、只能一直释放锁。

locked point就是指第一个阶段的末尾点，该点决定了a serialization order。

2PL的主要算法变种有4种：基本实现；Primary Copy 2PL； voting 2PL； Centralized 2PL。2PL中需要注意死锁的问题，其解决方法主要有两种：

- 死锁预防

  1.  preemptive，特点是锁的持有者让出了锁资源

     Wound-Wait技术，请求锁的事务Ti优先级较高，则等待； 否则的话，abort另一低优化级事务Tj。

  2. nonpreemptive，特点是锁的等待者放弃了锁请求

     Wait-Die技术， 请求锁的事务Ti优先级较低，要么死等锁资源，要么aborted重新执行。

  3. 重新调整资源顺序

     PG就采用了这种方法。

- 死锁检测

  本地的死锁检测一般使用有向循环图进行detect。对于死锁环中的某个victim事务，可以考虑其运行时长、拥有资源数目等进行选择。

  全局的死锁检测two techniques for constructing global waits-for graphs: centralized and hierarchical deadlock detection。基本思想都是周期性地向某个探测站点发送本地死锁探测结果并进行全局合并。

#### SYNCHRONIZATION TECHNIQUES BASED ON TIMESTAMP ORDERING

