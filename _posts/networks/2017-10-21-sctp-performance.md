---
layout: post
title: "SCTP网络性能的相关论文"
date: 2017-10-21
category: 网络
keywords: linux network, sctp, data center
---

# SCTP Performance in Data Center Environments

本论文是英特尔公司发表的，发表时间为2014年10月，由Krishna Kant发表。

## 简介

本论文首先对SCTP进行了简单介绍，然后对TCP和SCTP进行了黑盒式地对比它们在linux中的实现和性能；接着对比了采取相应地优化后，SCTP所带来的性能提升。最后讨论了SACK，并进行了总结。

## SCTP的特点与数据中心的要求

TCP的特点主要有:

* 面向流的，保序的传输； 
* 使用贪婪方案来增加流速；
* 使用AIMD（缓慢增长、急速下降）的窗口方法来控制堵塞控制；
* 经过几十年的发展，已经相当稳定了。
* 一些缺点：缺少完整性检查； DoS攻击，等等。

SCTP的一些特点包括：

* multi-stream, 多流。一个association可以有多个流（逻辑通道）。流控和堵塞控制仍然是基于association的。
* Flexible ordering, 保序是在每一个流里的，而不是整个association;
* Multi-homing, 多宿机； 
* DoS保护
* Robust association establishment： CRC检验以及心跳机制；
* Each SCTP operation (data send, heartbeat
send, connection init, ...) is sent as a “chunk” with its own header to identify such things as type, size, and other parameters.

数据中心的一些要求：

* much higher data rates
* much smaller and less variable round-trip times (RTTs)
* higher installed capacity and hence less chances of severe congestion 堵塞少
* low to very low end-to-end latency requirements 低延迟
* unique quality of service (QoS) needs

针对这些要求，所需要的是

* a low protocol processing overhead is more important than improvements in achievable throughput under sustained packet losses 快速处理协议
* achieving low communication latency is more important than using the available BW most effectively 低通信延迟
* a crucial performance metric for data center transport is number of CPU cycles per transfer (or CPU utilization for a given throughput) 单位传输的CPU使用
* packet losses should be actively avoided, rather than tolerated 避免丢包
* delay based congestion control is much preferred in a data center than a loss based congestion control 堵塞算法的选择
* demands a much higher level of availability, diagonosability and robustness
* fairness property is less important than the ability to provide different applications bandwidths

RDMA可以减少内存拷贝，但是，an effective implementation of RDMA becomes very difficult on top of a byte stream abstraction。所以才会考虑SCTP。

## SCTP与TCP的性能比较

SCTP的实现主要有两个， 一是[LK-SCTP](http://lksctp.sourceforge.net/), 另外一个是开源版本[KAME](http://www.sctp.org)。本论文方要采取前者进行测试比较。

**测试环境**

1. two 2.8 GHz Pentium IV machines (HT disabled) with 512 KB second level cache (no level 3 cache) 
2. R.H 9.0 with 2.6 Kernel
3. one or more Intel Gb NICs
4. One machine was used as a server and the other as a client
5. Multi-streaming tests were done using a small traffic generator that we cobbled up 多流测试
6. iPerf sends back to back messages of a given size

**测试配置**

1. checksum offload
2. transport segmentation offload (TSO)

checksum calculation is very CPU intensive. In terms of CPU cycles, CRC-32 increases the protocol processing cost by 24% on the send side and a whopping 42% on the receive side。很明显地，需要把CRC32的代码去掉；这一功能可由专门的硬件来完成。

TSO for SCTP would have to be lot more complex than that for TCP and will clearly require new hardware.所以，把TCP TSO功能禁止掉了。

**比较维度**

1. Average CPU cycles per instruction (CPI)
2. Path-length or number of instructions per transfer (PL)
3. No of cache misses per instruction in the highest level cache (MPI)
4. CPU utilization
5. Achieved throughput.

**第一组比较**

测试方法的要点有：

* a single connection running over the Gb NIC
* pushing 8 KB packets as fast as possible under zero packet drops
* The receive window size was set to 64 KB (>the small RTT 56us)

测试的主要结果：

* 无论是发送还是接收，SCTP可以达到与TCP几乎相同水平的吞吐量;
* 发送端的SCTP CPU utilization是TCP的2.1X来
* 发送端的cache miss要比TCP低
* 发送端的执行指令数目是TCP的3.7X来 ；
* 发送端的整体CPI是TCP的60%；
* 接收端的特性整体与上面保持一致，但是要有所改善，这是因为rev端所做的会少；

解释测试结果：inefficient implementation of data chunking, chunk bundling, maintaining several linked data structures, SACK processing, etc.

**第二组比较**

测试方法的变化主要是：

* 使用64byte大小进行传输测试，而不是8KB;
* 分别调整窗口大小为64KB和128KB大小； 

测试的主要结果：

* 在默认的64KB设置下，TCP的吞吐量要比SCTP略好； —— 这与期望是不相符的；
* 在128KB的情况下，TCP的吞吐量则要比SCTP好再多； —— 这是由于更少的数据结构操作

在数据中心的环境中，低延时要比高吞吐量重要得多，所以将NO-DELAY设置打开是一个正确的选择。by default, whenever the window allows a MTU to be sent, SCTP will build a packet from the available application messages instead of waiting for more to arrive

### 多流的性能

**测试环境**

* 使用1.28KB大小进行测试 —— 避免单个NIC成为瓶颈
* 使用DP (dual processor)配置  —— 避免CPU成为瓶颈
* a single NIC with one connection (or association)

**测试结果**

* 总体来讲，TCP与SCTP中的单流测试吞吐量是相平的，但是SCTP的多流单连接的测试结果要差一些； 
* 2 associations 1 stream 与 1 associations 2 streams的比较
    * 后者的吞吐量要比前者少28%
    * CPU utilization同样是后者比前者低28%
    * send / recv二者的观察结果是一致的

in effect, the streams are about the same weight as associations; furthermore, they are also unable to drive the CPU to 100% utilization. 究其原因，与锁和同步问题相关。

更进一步的检验可以发现sctp在实现和规范上的问题。

* sendmsg()函数的实现， locks the socket at the beginning of the function & unlocks it when the message is delivered to the IP-Layer. This problem can be alleviated by a change in the TCB (transport control block) structure along with finer granularity locking
* A more serious issue is on the receive end – since the stream id is not known until the arriving SCTP has been processed and the chunks removed, there is little scope for simultaneous processing of both streams.

### SCTP性能加强

**实现上的问题**

* Both of these structures are dynamically allocated & freed by LK-SCTP
* Each chunk is managed via two other data structures
* a total of 3 memory to memory (M2M) copies before the data appears on the wire.

**对应的措施**

* Avoid dynamic memory allocation/deallocation in favor of pre-allocation or use of ring buffers
* Avoid chunk bundling only when appropriate
* Cut down on M2M copies for large messages

**规范上的问题**

* one SACK per packet
* the frequency of SACKs in SCTP becomes too high and contributes to very substantial overhead
* the maximum burst size (MBS). While the intention of MBS is clearly rate control, specifying it as a constant protocol parameter or embedding a complex dynamic algorithm in the transport layer is not a desirable approach.
* transmission control block (TCB).  
    * the size of the association structure is an order of magnitude bigger at around 5KB. 
    *  Large TCB sizes are undesirable both in terms of processing complexity and in terms of caching efficiency

## Performance under Errors

a reduction in SACK frequency is detrimental to throughput performance at high drop rates, but is desirable at lower drop rates.

## 参考
* [SCTP Performance in Data Center Environments](https://www.researchgate.net/publication/266865697_SCTP_Performance_in_Data_Center_Environments)