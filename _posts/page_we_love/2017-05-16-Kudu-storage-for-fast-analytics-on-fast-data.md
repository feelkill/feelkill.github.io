---
layout: post
title: "Kudu:在快速数据上快速分析的存储"
date: 2017-05-10
category: 论文
keywords: Kudu, 数据, 存储, 分析
---

论文题目： [Kudu:storage for fast analytics on fast data](kudu.apache.org/kudu.pdf) [快速下载](/pieces_of_work/concurrent_control/kudu.pdf)

论文时间： 2015.09.28

作者： Cloudera公司的一批大佬

![](http://blog.talkingdata.net/wp-content/uploads/2015/10/0.jpg)

> <SUP>[1]</SUP>Kudu，对应中文的含义应该是非洲的一种带条纹的大羚羊。
> Cloudera则给自己新开发的大数据存储系统命名为Kudu，应该代表了Kudu速度快是一大特点。
> 在Cloudera官方的博客上，对于Kudu的描述是：一个弥补HDFS和HBase之间的缺口的新型的存储，它能够更有效的利用现代硬件的CPU和IO资源，既能够支持分析，又能够支持更新、删除和实时查询。

## 摘要

Kudu是为结构化数据设计的开源存储引擎，它同时支持**低延时的随机访问**和**高效分析的访问模式**。Kudu使用水平分隔对数据进行分布，并且使用Raft来repliicate每一个分区，提供低平均恢复时长(low mean-time-to-recovery)和低尾延时(low tail latencies)。它主要处于Hadoop生态系统中，也支持Cloudera Impala, Spark, MapReduce等工具的访问。

## 1. 介绍

在Hadoop生态中，结构化存储有两种典型的实现方法：
* 静态数据集,
    * 二进制方式存储在HDFS中（Apache Avro/Parquet）
    * 欠缺考虑记录的更新，或高效地随机访问
* 可变数据集, 
    * 半结构化地存储在Apache HBase/Cassandra中
    * 考虑了记录级别的低延时读和写，但在顺序读上不如前者，不利用AP场景

正因为如此，实际中的Cloudera用户构建了比较复杂的架构系统来进行存储和分析。

> <SUP>[1]</SUP>说到开发Kudu的初衷，Cloudera的解释是他们在客户的现场做大数据项目时发现，真正客户面临的问题在当前的Hadoop生态系统下，都是一个混合的架构，如下图所示：

![](http://blog.talkingdata.net/wp-content/uploads/2015/10/12.jpg)

> 在这个架构中，HBase被用来当作数据载入和更新的存储，这个存储适合于实时的查询，而数据随后被处理为parquet格式的文件，从而适合后续的利用Impala等工具进行分析。

以上构架存在主要的问题是：
1. 应用架构必须写复杂的代码来管理两个系统间的数据流和数据同步问题； 
2. 运维者必须管理一致性的备份，安全策略，以及多个系统的监控； 
3. 在新数据到达HBase和可对新数据进行分析之间的延时较大； 
4. 把后来数据迁移到不变的存储集中，需要进行昂贵的重写、交换、分区和手动变换。

> 而Kudu则主要针对这个混合架构的需求所设计开发的一个存储系统，希望能够降低这种混合架构系统的复杂性，同时能够满足客户类似的需求。

> Kudu的设计目标：
> * 对于scan和随机访问都有非常好的性能，从而降低客户构造混合架构的复杂度
> * 很高的CPU利用效率，从而提高用户在现代CPU使用上的投入产出比
> * 很高的IO利用效率，从而更好的使用现代的存储
> * 能够对数据根据数据所在位置进行更新，从而减少额外的处理和数据的移动
> * 支持多数据中心的双活集群复制

Kudu在Hadoop生态系统中所处的角色和位置如下图所示。

![](http://blog.talkingdata.net/wp-content/uploads/2015/10/21.jpg)

## 高层次看Kudu

### 表和schemas

从使用者的角度来看，kudu是以表的形式进行结构数据存储的存储系统。一个kudu集群有多个表，每个表都是由shema进行定义，包含有限个列，每列有一个名字和类型，并且可以选择是否支持空值。这些列的一些有序的列可以定义为表的主键，主键有唯一性约束，并且作为删除和更新的索引。这些特性与传统的关系型数据库非常的相似，但是与Cassandra,mongodb,riak,bigtable等分布式数据存储却非常的不同。

与使用关系型数据库一样，kudu的用户必须要先在创建表时给定表的schema，如果插入不存在的列会报错，并且违反唯一性约束也会有相应的错误。用户可以通过alter table来增加或者删除列，但是主键列不能够被删除。

NoSQL的思想是，一切都是字节。我们不采取这个NoSQL的方法而是显式地声明列类型，主要是以下两个因素：
1. 与采取与类型相关的encoding
2. 允许我们将类似SQL的元数据导出到其他的系统中，例如BI或者数据挖掘工具

不过Kudu的设计不支持二级索引，这个限制和HBase是一样的； 也不支持除主键外的唯一性约束。另外，当前的kudu要求每一个表必须定义一个主键列。

### 写操作

对于kudu的写操作来说，insert,update,delete都必须指定主键才能进行。另外也和HBase一样，kudu不支持跨行级别的事务（multi-row transactional ）；也就是说，理论上每一个改动都是在它自己的事务内执行。

Kudu当前提供的主要接口是JAVA和C＋＋，当前python还是实验性支持。

### 读操作

对于读来讲，kudu只提供了一个scan操作来从表读取数据，不过用户可以给定一些条件来过滤结果（**谓词条件**）。Kudu的客户端API和服务端都会对谓词条件进行解释，以此来砍掉大量的不需要从磁盘读取、或从网络传输的数据。目前kudu支持两种条件比较:
* 列和常量进行比较
* 给定主键的范围

对于kudu的查询来讲，用户还可以限定只返回部分列（**投影操作**），因为Kudu的实际存储是列式的存储，这种限定可以大幅度的提高性能。

### 其他API

Kudu客户端库还提供了别的有用功能。特别地，Hadoop生态系统可通过数据位置(data location）的调度来获得更好的性能。 Kudu提供的API可让客户来确定数据范围到服务器的映射，从而辅助分布式执行框架（像Spark, MapReduce, Impala）的调度。

### 一致性模型

Kudu给客户提供了两种一致性模型：
* 默认是**快照一致性**，保证 read-your-writes 的一致性

    默认情况下，Kudu并不提供external consistency的保证。举个简单的例子
    1. client1 --> 进行写 r1
    2. client1 --message bus--> 与client2进行通信
    3. client2 --> 进行写 r2
    4. reader 结果看到了client2写的结果却没有看到client1写的结果

    reader无法捕捉到client1和client2之间的因果信赖关系。这在大多数的情况下，用户是可接受的，OK的。
* 时间戳

    执行写后，用户向客户端库要一个时间戳；这个时间戳会通过外部管道扩散到其他的客户端，这样就可以阻止跨越两个客户端的、之间有因果树信赖关系的写了。

    如果这个扩散过程太复杂的话，Kudu可选commit-wait方式（与Spanner一样）。在这种方式下，客户会被延一段时间，以保证后来的写可正确地因果有序。 这样子的话，是需要NTP的支持，或者是高精度的全局时间同步。

    时间戳的赋值是基于clock算法的，称为HybridTime，可以参考末尾的引用文章。

### 时间戳

Kudu内部使用时间戳来实现并发控制，它不允许用户手动设定一个写操作的时间戳。主要是因为只有高级用户才会有效地使用时间戳，而这部分用户是少量的； 对于大多数用户来讲，这个高级特性令他们是迷惑的。

对于写来讲，Kudu允许用户指定一个时间戳。这样，用户就可以执行point-in-time查询（过去的一个查询）； 同时，Kudu保证**构成一个简单查询(像在Spark或Impala)的不同的分布式任务**读取使用了同一个一致性快照。

## 架构

### Cluster角色

kudu的集群架构与HDFS,HBase架构类似，Kudu有一个Master Server负责元数据的管理，多个Tablet Server负责数据的存储。Master Server可以通过复制来是先容错和故障恢复。

### 分区

与大部分的分布式数据库系统一样，kudu的表是水平分区的，这些水平分区的表叫做tablets。每一行都会根据它的主键唯一的映射到一个tablet上。对于吞吐量要求比较高的情况下，一个大表可以分为10到100个tablets，每个tablet差不多可以是10G大小。

至于partition的方式，Kudu支持在创建表时给定一个partition schema，这个partition schema是由0个或者多个hash分区规则以及一个可选的范围分区规则组成。

* **hash分区**规则由主键列的子集列和分区bucket数量构成，例如：

  <center>DISTRIBUTE BY HASH(hostname, ts) INTO 16 BUCKETS</center>

  这个规则基本是采用拼接需要hash的列，对桶数求余，然后生成一个32位的整形作为结果的分区key。

* **范围分区**规则则是基于有序的主键列，将列的值按照能够保持顺序的编码进行处理，然后将数据进行相应的分区。

### replication复制

Kudu采用了Raft协议来实现表数据的复制，在具体的实现过程中，Kudu对于Raft协议也做了一些修改和增强，具体的表现在：

* 在Leader选举失败时，采用指数算法(Exponential Backoff)来重试
* 当一个新的leader在联系一个follower时，如果follower的log与自己不相同，kudu会立即跳回到最后的committedIndex，这能够大大减少在网络上传输的冗余的操作，而且实现起来简单，并且能够保证不一致的操作在一次往返后就被抛弃掉。

另外，kudu的复制不是复制磁盘上的存储的表的数据，而是复制操作日志。表的每个副本的物理存储是完全解耦的，它带来了如下的好处：

* 当一个副本在进行后台的一些物理层的操作（flush或者compact)时，一般其他节点不会同时对同一个tablet做同样的操作，因为Raft协议的提交是过半数副本应答，这样后台物理层操作对于提交的影响将会降低。
* 在开发过程中，kudu团队遇到过一些罕见的物理存储层race condition情况，因为物理存储的松耦合，这些race condition都没有造成数据的丢失。

#### 配置变化

### Kudu Master

#### 元数据的管理者

#### 集群的协调者

#### tablets目录

## tablet存储

### 简述

### RowSets

### MemRowSet的实现

### DiskRowSet的实现

### Delta Flushes

### 插入的路径

### 读的路径

### 延时物化

### Delta Compaction

### RowSet Compaction

### 调度管理

## 与Hadoop的集成

### MapR  + Spark

### Impala

## 性能评估

### 与Parquet的比较

### 与Phoenix的比较

### 随机访问的性能

## 阅读总结

## 阅读参考
1. [Kudu – 在快数据上的进行快分析的存储](http://blog.talkingdata.net/?p=3865&utm_source=tuicool&utm_medium=referral)
2. [Kudu：为大数据快速分析量身定制的 Hadoop 存储系统](http://www.oschina.net/news/73633/kudu-apache-hadoop)
3. [Kudu:支持快速分析的新型Hadoop存储系统](http://www.open-open.com/lib/view/open1470916252470.html)
4. [kudu论文阅读](http://www.cnblogs.com/xey-csu/p/5668403.html)
