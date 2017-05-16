---
layout: post
title: "Kudu:在快速数据上快速分析的存储"
date: 2017-05-10
category: 论文
keywords: Kudu, 数据, 存储, 分析
---

论文题目： [Kudu:storage for fast analytics on fast data](kudu.apache.org/kudu.pdf) [快速下载](/pieces_of_work/concurrent_control/kudu.pdf)

## 摘要

Kudu是为结构化数据设计的开源存储引擎，它同时支持**低延时的随机访问**和**高效分析的访问模式**。Kudu使用水平分隔对数据进行分布，并且使用Raft来repliicate每一个分区，提供低平均恢复时长(low mean-time-to-recovery)和低尾延时(low tail latencies)。它主要处于Hadoop生态系统中，也支持Cloudera Impala, Spark, MapReduce等工具的访问。

## 1. 介绍

在Hadoop生态中，结构化存储典型地有两种实现方法：
* 静态数据集,
    二进制方式存储在HDFS中（Apache Avro/Parquet）
    
* 动态数据集, 
