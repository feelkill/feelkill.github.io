---
layout: post
title: "使用基于命名的映射来提升命中率"
date: 2017-09-22
category: 论文
keywords: 一致性哈希表, consistent hashing, random trees
---

## 摘要

问题： 多个client向一组服务器请求关于某个对象的服务， 怎么样可以使得这些服务都访问到同一个服务器，以提升命中率？

方法： 本文使用了HRW（Highest Random Weight）的方法， 在客户端使用此方法来解决此问题，以减少响应时间。

## 简介

背景问题中的CS服务的特点：

* 由一组服务器来响应client端的所有请求，这些服务器是等同的功能和容量/能力； 
* 在发送请求之前，client端已拥有了所有服务器的信息。 从client来看，服务端是对等的；
* 服务端有一个 hit rate的说法，主要用来快速响应；例如，服务端是作为cache使用；
* 跨服务器进行对象复制的收益是微乎其微的； 

符合上面特点的一些典型域：

* client-side WWW proxy caches
* real-time producer-consumer system

算法name-based mapping的典型描述就是： maps requests to servers such that requests for the same object are sent to the same server, while requests for different objects are split among multiple servers.

对象和服务器之间的 **affinities 亲和性** 是指 all clients send requests for the same object to the same server. cache affinities的研究，将task发送到已经缓存了数据的处理器上，是可以提升cache hit rate.

![](/assets/2017/hash-name-based-mapp00.jpeg)

多处理器系统与分布式系统的区别在于：

* 中心化调度与非中心化调度， 分布式系统中cleint对服务端的请求是独立的，非中心化的； 
* 延时性，负载信息的及时更新在分布式系统中延时较大； 
* request migrate, 在分布式系统中几乎是不可能的，但是在多处理器系统是很常见的； 

论文的目标有两个：
1. 提升cache hit rates;
2. 通过适当调度来减少latency;

本论文的主要贡献：
1. mapping requests to servers模型的建立；
2. 提出了name-based mapping算法HRW；

## mappings的目标

1. load balancing
  * “从cluster中选择一个server”引入的延迟必须尽可能地小；  local decision VS remote exchange.
  * 要保证延迟在各个服务端之间是均匀的，每个服务端应该接收到均匀的、等量的请求, 与对象大小无关，与对象流行度的分布无关； 

  请求模型主要有：传统的泊松分布； Packet Train， 请求是 in batches/trains到达的(采用这种模型)。 通过公式推导证明两点：coefficient关联系数趋于0时， 服务端之间的负载是平衡的。
2. low mapping overhead
3. high hit rate, 减少replication,提升命中率； 
4. minimal disruption. 对象的重分布必须必可能得少。
  * disruption coefficient: the fraction of the total number of objects that must be remapped when a server comes up or go down.
  * disruption bounds: 1/m <= disruption coefficient <= 1, 其中m是活跃服务端的数目;

## mapping requests to servers的模型


## 参考
* using name-base mapping to increase hit rates