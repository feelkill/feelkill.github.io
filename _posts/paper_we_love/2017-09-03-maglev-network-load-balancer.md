---
layout: post
title: "Maglev:一个快速可靠的网络负载均衡软件"
date: 2017-09-03
category: 论文
keywords: Maglev, 负载均衡， 一致性哈希， 网络负载
---

论文：[Maglev: A Fast and Reliable Software Network Load Balancer](http://static.googleusercontent.com/media/research.google.com/zh-TW//pubs/archive/44824.pdf)

## 术语

* network load balance 网络负载均衡
* service's endpoint, 服务终结点
* generic routing encapsulation, GRE
* Direct Server Return, DSR

## 摘要

传统网络的负载均衡是通过硬件来做的，而Maglev是通过软件来实现的负载均衡系统，由google开发的， 主要为Google Cloud Platform提供网络负载均衡，从2008年服务至今。它的主要特点是：

* 专门为包的处理性能做过优化
* 配备了一致性哈希和连接trace特性，考虑了故障的问题

## 背景

![Figure 1: hardware load balancer and Maglev](http://www.evanlin.com/images/2016/maglev1.png)

网络负载均衡器是谷歌网络基础设施的重要组件。在上图中，它同多个设备组成，逻辑上主要位于路由器和TCP/UDP服务器的之间。主要功能有两个： 匹配功能，将包映射到对应的服务器； 将包转发到服务的终结点上。

传统的负载均衡器由专门的硬件来实现，主要的缺点有：

* 扩展性差
* 无法满足高可用性要求
* 缺少弹性和可编程性
* 升级昂贵

使用软件化的负载均衡系统则可以解决上面的这些问题。设计和实现这样的系统有较高的复杂性和挑战：

1. 系统中的每一个机器个体都必须提供高吞吐量
2. 系统作为一个整体对外提供连接的持续性(connection persistence)：属于相同连接的包应该发送给相同的服务终结点；

## 系统总述

![Figure 2:Maglev packet flow](https://segmentfault.com/img/remote/1460000009565792?w=1556&h=934)

Maglev是部署在谷歌的前端服务的位置上，包含了大小可变的集群。上图是一个简化了的架构。

谷歌对外提供服务是使用的VIP，这不同于物理IP；一个物理IP对应于一个network interface，而一个VIP对应于Maglev背后的多个服务的终结点。Maglev通过BGP把VIP告知路由器，然后路由器把这个VIP告知谷歌的骨干网，再接着由骨干网转而告知整个因特网。最后，整个VIP将会被整个网络全球可访问。

当用户敲入www.google.com的时候，浏览器将向DNS发起查询，DNS服务则会考虑到用户的物理位置以及每一个服务的负载，告知用户一个最近的前端服务、并把对应的VIP也一并给用户。然后，浏览器将会使用这个VIP建立一个新的连接。

当路由器接收到这个VIP包后，它把这个包通过ECMP转发到其中的一个Maglev机器上。这个Maglev机器接收到这个包后，它首先要选择与此VIP相应的一个服务终结点，使用GRE把外部IP头打包进这个数据包里，这样这个包就可以转发到服务终结点。

当数据包到达选好的服务终结点后，会对包进行解封并消费。响应包会带上VIP和用户IP放进IP包里边，我们使用DSR把响应直接发送给路由器；Maglev不需要处理返回包，这种包一般都比较大。本论文主要聚焦的是进来的用户阻塞问题，DSR的实现不在本论文之内。

Maglev的两个主要作用是：

1. 告知路由器它的VIP地址； 
2. 把进来的数据包给后端的服务终结点；

![Figure 3: Maglev config (BP stands for backend pool)](/assets/2017/maglev-config.png)

所以每个Maglev都配置有一个控制件和一个转发件（示图），这两部分都需要从配置对象中了解到VIP信息，要么是从文件 中读取，要么是通过RPC从外部系统中读取。

控制组件会周期性地检查forwarder的健康状态， 以保证路由器发送过来的数据包是转发给健康的Maglev机器的。

每一个VIP配置有一个或多个后端池（图中的BP），除非特别指定，一般后端就是服务的终结点。一个后端池可能包含对应服务终结点的物理IP，也可能递归地包含别的的后端池。每一个后端池关联着一个或者多个的健康检查方法，以确保数据包转发到的是健康的服务点。

config manager负责解析和校正配置对象。所有配置的更新都是原子性的。

可以对maglev进行shard配置，这样可以为不同的VIP集合进行配置和服务。sharding技术提供了性能的隔离性，并确保了服务的质量。

## forwarder的设计和实现

![Figure 4: Maglev forwarder structure](https://segmentfault.com/img/remote/1460000009565793?w=1122&h=766)

linux内核并不涉及这些。总体来讲，

## 参考
* [論文中文導讀 Maglev](http://www.evanlin.com/maglev/)
* [Wiki Consistent_hashing](https://en.wikipedia.org/wiki/Consistent_hashing)
* [Go implementation of maglev hashing](https://github.com/dgryski/go-maglev)
* [每天进步一点点——五分钟理解一致性哈希算法(consistent hashing)](http://blog.csdn.net/cywosp/article/details/23397179)
* [Distributed Systems Part-1: A peek into consistent hashing!](https://loveforprogramming.quora.com/Distributed-Systems-Part-1-A-peek-into-consistent-hashing)
* [Google Maglev 牛逼的网络负载均衡器](https://segmentfault.com/a/1190000009565788)