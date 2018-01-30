---
layout: post
title: "Pingmesh论文"
date: 2018-01-30
category: 2018年
keywords: Pingmesh, 网络故障, DC
---

论文为 [A Large-Scale System for Data Center Network Latency Measurement and Analysis](http://conferences.sigcomm.org/sigcomm/2015/pdf/papers/p139.pdf)

## 要解决什么问题

* 定界，判定数据中心里发生的问题其原因是否为网络故障
* SLA，定义和跟踪网络SLA
* network troubleshooting

## 问题背景

数据中心的网络拓扑结构是分层的，主要分为了三层结构：

1. 第一层tier：Pod。数十个servers使用NIC连接到ToR 交换机，形成一个Pod
2. 第二层tier：PodSet。数十个Pod连接到leaf交换机，共同构成了PodSet。
3. 第三层tier: 数据中心。由多个PodSet连接到Spine交换机上，共同构成了DC。

最后，多个DC通过Inter-DC网络进行连接。DC使用Autopilot框架来管理，在这个框架中，主要使用Cosmos进行数据存储，使用SCOPE语言进行作业的分析和处理。Pingmesh正是建立在这一套管理框架上的共享服务。

## Pingmesh的设计和实现

主要由三部分构成：控制器； 代理； 数据的分析和处理。

**控制器**

控制器的主要作用有三点：

1. 决定server之间如何probe
2. 依据网络拓扑来生成每个server的pinglist
3. 每个server通过RESTful来获取pinglist

核心的设计主要是pinglist的生成算法，其要点如下：

* 多层次的完全图设计，主要是Pod内、DC内、DC间
* ping动作只在server间进行
* Pod内，所有server参与ping操作
* DC内，所有server参与ping操作
* DC间，只选择一部分的server参与ping操作

**代理**

代理的主要作用有三点：

1. 下载pinglist文件
2. 通过tcp/http来发起探测
3. 将探测数据以timer或者阈值的方式上报存储

核心的设计主要是ping操作不影响性能，其要点如下：

1. 与DC内的其他程序连接保持一致，使用TCP/HTTP连接
2. 为了可以区分网络还是程序的问题，不使用能用库，而是自行开发了轻量级网络库
3. 包长度可配置
4. 每次的probe使用不同的connect、port，以尽可能地多路径探测

从论文所给的测试数据来看，内存控制在了45MB之内，CPU使用平均率为0.26%，网络使用为几十Kb/s（整个带宽为Gb/s）。

**数据分析和处理**

这一部分的主要作用是：

1. 对延时数据进行存储和分析
2. 基于延时数据进行可视化、上报和告警

Agent会做一些本地计算，包括了

1.  丢包率
2. 50%的网络延时
3. 90%的网络延时

SCOPE处理主要按不同的时间间隔进行的，包括

1.  准实时处理，以10分钟频率的处理，数据消费要在20分钟左右； 
2. 非实时处理，主要以1小时和1天为频率，主要用于：SLA跟踪； network black-hole detection； 丢包探测；
 
在实际处理中，SAL跟踪是以20min delay工作效果最佳的；

## 测试效果

主要从三个方面来定义了具体的SLA：

* 丢包率，正常值在 4*10^(-5)
* P50的延时，占比50%的延时数值
* p99的延时，占比99%的延时数值为 500 ~560us

然后使用简单的阈值进行判定是否发生了异常，同时会保留2个月的延时数据进行跟踪和分析。

## 吸取到的经验

* 监测服务要always-on
* 可视化分析
* 微服务，组件松耦合

## 心得

论文中关于数据中心的网络监测方法，从实质上来说，并没有什么取巧或者花哨的点，使用了最笨、最实在的方法来全覆盖整个网络的实时情况。只是在实现上，更多地关注“从性能上不要影响现成的业务”。另外，对于监测数据如何进行分析处理，本论文并没有展开说明，这也恰恰是数据分析方面更应该关注的。