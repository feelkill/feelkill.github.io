---
layout: post
title: "linux网络栈中的排队"
date: 2017-06-21
category: 网络
keywords: 网络安全, TCP, TSO, GSO, USO
---

数据包队列是任何网络栈的一个核心组件。它允许模块进行异步通信，提升了性能，也有延时的负面问题。本文主要是解释：IP数据包在linux网络栈中哪个位置进行排队，如何控制缓存来减少延时，像BQL这些特性是如何减少延时的。

![](/assets/2017/figure_1_v2.png)

<center>Figure 1 – Simplified high level overview of the queues on the transmit path of the Linux network stack</center>

## 驱动器队列（aka ring buffer)

驱动器队列位于IP栈和NIC之间。这种队列是典型的先进先出（FIFO）的环缓存，可以认为它是一个固定大小的缓存。该队列并不包含包数据，相反它包含的是指向SKBs（socket kernel buffers）数据结构的描述信息；SKBs里才包含了包数据，用于穿透整个kernel。

![](/assets/2017/figure_2_v2.png)

<center>Figure 2 – Partially full driver queue with descriptors pointing to SKBs</center>

驱动器队列的输入源是IP栈，IP栈对所有的IP包进行排队。数据包可能由本地产生，也可能是需要路由到另一个NIC的、半路接收到的（此时设备作为路由器使用）。硬件驱动器会把数据包出队，然后通过data bus发送到NIC硬件进行传输。

驱动器队列存在的原因是，无论什么时候系统有数据要传输，数据对NIC来讲都是可用的，可立即转发出去。也就是说，驱动器队列给了IP栈一个可以异步地排队数据的地方（这里的异步是对硬件的操作来讲的）。另一个可选的设计是，当物理介质准备好传输时，NIC向IP栈要数据；但是这种方案里，IP栈并不能够立即响应这种请求，这种设计就会浪费掉可价值的传输机会，从而导致较低的吞吐量。另一个相反的方法是，数据包创建好后，IP栈一直等到硬件准备好可以传输数据；这种方案也不理想，这是因为IP栈被阻塞了，它不能够去做别的事情去了。

## 来自栈的超大包

多数的NIC都有自己固定的MTU限制，它表示了物理介质能够传输的最大帧。对于以太网来讲，默认的MTU是1500字节，但是一些以太网是可以支持[Jumbo Frames ](http://en.wikipedia.org/wiki/Jumbo_frame)最大到9000字节的。在IP网络栈中，MTU限制了发送到设备进行传输的数据包的大小。比方说，一个程序向TCP socket写了2000字节的数据，然后IP栈需要创建两个IP包，保证这两个包大小是小于等于1500 MTU的。那么， 对于大的数据传输来讲，小的MTU会使得大量的小包被创建出来，然后通过驱动器队列才能够传输出去。

为了避免传输路径上大量的包产生的负载，linux内核进行了一系列的优化：TSO， UFO， GSO。所有的这些优化措施都允许IP栈直接创建大于MTU的包并直接传给NIC。对于IPV4来讲，最大可以创建65536字节的包，将放到驱动器队列中。对于TSO和UFO而言，由NIC硬件来对单个大包进行切割，保证切分后的小包是可以在物理介质上进行传输的。对于没有硬件支持的NIC来说，GSO则可以从软件层次上来完成相同的功能，再把数据包放到驱动器的等待队列中去。

前面说过，驱动器队列中是一些固定数目的描述信息，这些信息指向了不同大小的数据包。因为TSO，UFO和GSO允许更大的数据包，这些优化有一个负面的问题是，极大地增加了队列中进行排队的字节数目。图3说明了这个与图2相比较的概念。

![](/assets/2017/figure_3_v2.png)

<center>Figure 3 – Large packets can be sent to the NIC when TSO, UFO or GSO are enabled. This can greatly increase the number of bytes in the driver queue.</center>

剩余的文章将主要聚焦于传输路径。linux的接收端也有类似于TSO,UFO,GSO的优化。这些优化的目标也是减少每一个包的overhead。特别是，[GRO](http://vger.kernel.org/~davem/cgi-bin/blog.cgi/2010/08/30)允许NIC驱动器把接收到的包合并为单个大包，然后传递给IP栈。当转发数据包时，GRO允许原始的数据包再次构建出来。然而，有一个问题是，当大的数据包在转发的传输端进行切割时，它将导致有多个小包一次进入等候队列。这种micro-burst包对inter-flow latency有负面作用的。

## 挨饿和延时

IP栈和驱动器之间的队列引入了两个问题：挨饿； 延时。

如果NIC驱动器唤醒了，去传输队列中拉数据包，而队列却是空的，那么硬件就是丢失一次传输的机会，从而会降低系统的吞吐量。这就是所谓的挨饿。需要注意的是，系统并没有任何东西需要传输时，此时队列是空的； 这种是一种正常的情形，而不是挨饿。与挨饿相关的一种复杂情形是，IP栈向队列中增添数据包，而硬件驱动器则异步地从队列中抽取数据包。更遭的是，增添/抽取事件的间隔时长是随着系统负载和外部条件而变化的； 外部条件，像网络接口的物理介质。比方说，在一个繁忙的系统中，IP栈很少有机会向缓存中增添数据包，而硬件抽取数据包的机会就会增加。从这一点来看，有一个大的缓存是有利的，它减少了挨饿的几率，保证了高吞吐量。

对于一个繁忙的系统，一个大的缓存可以维持高吞吐量； 但是，它也有相应的负面作用，就是引入了较大的延时。

![](/assets/2017/figure_4_v2.png)

<center>Figure 4 – Interactive packet (yellow) behind bulk flow packets (blue)</center>


上图中，驱动器队列中几乎全部是TCP段（蓝色的）。队列的最后一个是VoIP数据包（黄色的）。这种交互式的程序典型地以固定的间隔发射出小的数据包，它们对延时是敏感的。而TCP段则以较大的频率产生了大的数据包，快速地填充了队列。那么后面小包的传输便会被延迟。

## 术语
* packet 数据包，网络封包
* latency 延时
* Driver Queue 驱动器队列
* Ring Buffer 环缓存
* Socket Kernel Buffers, SKBs
* TCP segmentation offload, TSO 
* UDP fragmentation offload, UFO
* generic segmentation offload, GSO
* generic receive offload, GRO

## 参考
* [Queueing in the Linux Network Stack](https://www.coverfire.com/articles/queueing-in-the-linux-network-stack/)
