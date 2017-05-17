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

### 写操作

### 读操作

### 其他API

### 一致性模型

### 时间戳

## 架构

### Cluster角色

### 分区

### replication复制

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
