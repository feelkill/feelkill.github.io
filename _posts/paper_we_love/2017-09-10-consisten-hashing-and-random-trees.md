---
layout: post
title: "一致性哈希表"
date: 2017-09-10
category: 论文
keywords: 一致性哈希表, consistent hashing, random trees
---

## 摘要

这篇论文是一致性hash表的开山鼻祖。它使用在分布式网络中的缓存协议中，解决了网络中的hot spot热点问题。

## 简介

大型网络中经常遇到的几个问题是：

* hot spot, 多个客户端同时地访问来自同一个服务端的数据；
* swamped, 在短时间内，同一个站点突然接收到这么多的客户端请求，有可能使得这个站点无法对外提供服务。

像这种中心化的CS服务模型，本论文所提供的工具方法都是适用的。

### 之前的工作

大多数使用proxy cache的方法来解决上面的两个问题，这种方法的基本原理就相当于数据库中的shared buffer的，其工作原理也基本是相同的。

有些论文使用了一组cache server来用作proxy cache。这种方法的缺点是，随着cache server数目的增长，管理这些cache server之间的缓存数据就成为了一个突出的问题。需要使用本论文中提出的一致性哈希来解决。

Harvest Cache也是一部分论文使用的方法，它大体使用的是树型方式来管理page cache的。这个方法的优点是分散了请求的压力，不会在短时间内形成高负载。缺点是，树的root节点在理论上是存在成为swamped的可能的。

Plaxton/Rajaraman算法则使用了随机+哈希的方法在多个cache中来平衡负载。这个算法存在的缺点同样也是swamped。

### 本论文的贡献

主要有两点：

1. random cache trees, 结合了后两种论文中的方法； 
2. 一致性哈希，对已有哈希的加强，可以应对网络中机器的go up/down问题；

## 模型

browers <--------->  caches <----------> servers

目标主要有三个: 阻止swamped; 减少cache memory的大小； 降低获取页的延时； 

## 一致性哈希

client和server之间有一层cache，用于减轻server的负载。那么，每一个cache只需要拥有其中的一部分数据。另外，client还需要知道向哪个cache去查询哪些数据对象。这个问题显示的方案是hash。server使用hash来把所有的对象分散到cache上去，而client使用hash来发现哪个cache缓存着数据对象。非一致性哈希有着灾难性的问题：所有数据得重分布； 之前的数据缓存全部作废了； 

一致性哈希的几个属性：

* smoothness, 从一个client的视角来看，当从/向cache set中增加或者移除掉一个机器时，需要向新机器中移动的数据量是最小的； 
* spread， 从所有client视角来看，“把一个数据对象赋于不同的cache”的总数目是小的； 
* load, 从所有client视角来看，“赋给某一个cache的不同对象”的总数目是小的；

### 定义

1、balance：哈希结果尽可能的平均分散到各个节点上，使得每个节点都能得到充分利用。

2、Monotonicity：上面也说了，如果是用签名取模算法，节点变更会使得整个网络的映射关系更改。如果是carp，会使得1/n的映射关系更改。一致性哈希的目标，是节点变更，不会改变网络的映射关系。

3、spread：同一份数据，存储到不同的节点上，换言之就是系统冗余。一致性哈希致力于降低系统冗度。

4、load：负载分散，和balance其实是差不多的意思，不过这里更多是指数据存储的均衡，balance是指访的均衡。

### 构造

可以参考[CSDN中的这篇文章](http://blog.csdn.net/sparkliang/article/details/5279393) 。

这篇文章中从理论上证明了几个重要的结论：

定论4.1 上面文章中描述的ranged hash family是满足上面所要求的4个属性的；

定论4.3 Every monotone ranged hash function is a 派-hash function and vice versa

一个派hash函数就是跟排列相关的函数，而Maglev hash正是此类函数簇的一个实现。

## 参考

* [一致性哈希表论文 Consistent Hashing and Random Trees:Distributed Caching Protocols for Relieving Hot Spots on the World Wide Web](https://www.akamai.com/us/en/multimedia/documents/technical-publication/consistent-hashing-and-random-trees-distributed-caching-protocols-for-relieving-hot-spots-on-the-world-wide-web-technical-publication.pdf)
* [一致性哈希算法](http://blog.csdn.net/sparkliang/article/details/5279393)
* [一致性哈希: Rendezvous hashing (also called HRW Hashing)](http://www.cnblogs.com/scotth/p/4873613.html)
* [Rendezvous hashing Wiki](https://en.wikipedia.org/wiki/Rendezvous_hashing)
* [Go implement of Rendezvous hash](https://github.com/tysontate/rendezvous)
* [Java implement of Rendezvous hash](https://github.com/clohfink/RendezvousHash)
* [Rendezvous or Highest Random Weight (HRW) hashing algorithm](http://www.csforge.com/?p=17)
* [分布式哈希表](http://www.cnblogs.com/scotth/p/4330670.html)
* [Distributed hash table Wiki](https://en.wikipedia.org/wiki/Distributed_hash_table)
* [using name-base mapping to increase hit rates.pdf]()
* [Consistent Hashing and Random Trees: Distributed Caching Protocols for Relieving Hot Spots on the World Wide Web]()
* [Microsoft Ananta: Cloud Scale Load Balancing]()