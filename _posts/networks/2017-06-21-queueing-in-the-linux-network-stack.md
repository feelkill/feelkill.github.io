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


上图中，驱动器队列中几乎全部是TCP段（蓝色的, bulk flow type）。队列的最后一个是VoIP数据包（黄色的, interactive flow type）。这种交互式的程序典型地以固定的间隔发射出小的数据包，它们对延时是敏感的。而TCP段则以较大的频率产生了大的数据包，快速地填充了队列。那么后面小包的传输便会被延迟。为了进一步说明这种行为，我们考虑基于下面假设的一个场景：

* 网络接口的传输能力是 5Mbit/sec, 或 5,000,000bits/sec
* 来自bulk流的单个包大小为 1500字节或者 12000位
* 来自于interactive流的包大小为500字节
* 队列深度是128，即有128个描述结构
* 当前队列中有127个bulk数据包，1个interactive数据包（处于最后队列的最后）

给定上面的假设后，抽取127个bulk数据包，为interactive数据包创建一个传输的时机为 (127 * 12,000) / 5,000,000 = 0.304, 也就是ping结果的延时为304毫秒。这个延时的量级已经超越了交互式程序所能接受的，但是这甚至还不表示整个路由的时长，这只是把它之间的所有数据包传输时间。正如前所述，如果开启TSO/UFO/GSO的话，驱动器队列中的数据包可以更大，比1500字节还要大。这将会使得延时问题更突出。

由oversized, unmanaged缓存引起的大延时问题是已知的，称为[Bufferbloat](http://en.wikipedia.org/wiki/Bufferbloat)。关于这个现象还详细的描述可以参考[Controlling Queue Delay](http://queue.acm.org/detail.cfm?id=2209336 )和[Bufferbloat](http://www.bufferbloat.net/)项目。

正如上所讲，选择驱动器队列的恰当大小是一个Goldilocks问题——它不能太小，否则就会有吞吐的问题；它也不能太大，否则就会有延时的问题。

## Byte Queue Limits(BQL)

BQL是linux内核(>3.3.0)的一个新特性，它尝试着去解决驱动器大小自动调节的问题。它加了一层，当前系统条件下，计算能够避免挨饿问题的最小缓存大小，来开启或关闭排队功能。前面说过，排队数据量越小，队列中等候的数据包所经历的延时越小。

这里的关键点是，驱动器队列的实际大小是不会随BQL而改变的； 而是，BQL计算出了一个限制值，当前应该有多少数据可以进行排队（以字节来计算）。超过这个限制的字节必须由这一增加层进行保持或者丢弃。

BQL在这两个事务发生时启用：当数据进入驱动器队列时； 当一次传输完成之时。 BQL算法的一个简化版本如下，LIMIT指的是BQL计算出来的值。

```
****
** After adding packets to the queue
****

if the number of queued bytes is over the current LIMIT value then
        disable the queueing of more data to the driver queue
```

需要注意的是，队列中的数据量是会超过LIMIT值的，这是因为数据先进入了队列，然后LIMIT才进行得检查。 当TSO／UFO／GSO开启的时候，单个操作就能把大量的字节放入队列； 这些吞吐量的优化是有负面效果的，它使得等候的数据量要比期望的要高。如果你确实更关注延时，那可能想把这些特性关闭掉。可以看文章的后面，如何关闭这些特性的。

BQL的第二阶段是在硬件传输完数据之后执行的（简单的伪代码）：
```
****
** When the hardware has completed sending a batch of packets
** (Referred to as the end of an interval)
****

if the hardware was starved in the interval
        increase LIMIT

else if the hardware was busy during the entire interval (not starved) and there are bytes to transmit
        decrease LIMIT by the number of bytes not transmitted in the interval

if the number of queued bytes is less than LIMIT
        enable the queueing of more data to the buffer
```

可以看出，BQL是基于测试设备是否会挨饿而进行调整的。如果挨饿发生了，那么增大LIMIT值，使得更多的数据可以进入队列，减少挨饿的机会。如果设备在整个检测间隔内是繁忙的，那么肯定队列中还存在可以传输的数据，那么在当前的系统情况下，队列要比所需要的大了，此时减少LIMIT值来约束延时。

用实际的例子来说明BQL对排队数据的影响。我的服务器折驱动器队列的大小默认为256.以太网的MTU是1500字节。在TSO／GSO不开启的情况下，这意味着最多有 256 * 1,500 = 384,000字节是可以进入驱动器队列的。然而，BQL计算出来的LIMIT值为3012字节。可以看到，BQL大大地约束了队列中的等候数据量。

BQL使用的是字节为单位，驱动器队列的大多数的包队列大小都不是使用字节为单位的。后者的单位从字节数上来讲是可变的； 与这相比，字节的数目与物理介质的传输时间有着更直接的关系。

BQL通过限制队列中的数据来避免挨饿的问题，从而减少了网络延时。另外，它还有一个重要的影响是，把等候的点从驱动器队列移到了排队策略（queueing discipline）上。QDisc层实现了更复杂的排队策略。下一章将介绍linux的QDisc层。

## Queuing Disciplines (QDisc)

驱动器队列是简单的FIFO队列。它对待所有的数据包是平等的，没有区分不同流的数据包的能力。这个设计保证了NIC驱动软件的简单和快速。更先进的以太网和大多数无线NIC支持多个独立的传输队列，但是这些队列是相似的，使用的是典型的FIFO。然而，使用较高的层来负责选择使用哪一个传输队列。

QDisc层就是IP栈和网卡驱动器队列之间的三名治（见图1）。它实现了traffic管理，包括traffic classification（分类）, prioritization（优先级划分） and rate shaping(速率整形)。这一层可以通过透明的tc命令来进行配置。要理解QDisc层，关键是它的三人概念：QDisc, 分类和过滤。

QDisc是比标准的FIFO队列更复杂的、用于拥堵队列的linux抽象。这个接口允许在不修改IP栈和NIC驱动器的情况下来实行复杂的队列管理行为。默认情况下，每一个网络接口都会分配一个[pfifo_fast](http://lartc.org/howto/lartc.qdisc.classless.html) QDisc，这是基于TOS位实现了一个简单的 three band prioritization scheme。抛开默认值不说，pfifo_fast远不是最佳的选择，因为它默认有着很深的队列（看下面的txqueuelen），并且它不感知流。

与QDisc最相关的第二个概念是分类(class)。不同的QDisc可能实现分类来处理不同小类的拥堵。比方说，[HTB](http://lartc.org/manpages/tc-htb.html) QDisc允许用户配置500Kbps和300Kbps分类。并不是所有的QDisc会支持多个分类，这些称为有类(classful)QDisc。

过滤（也叫为分类过滤）机制用于将拥堵分类为一个特殊的QDisc或分类。有着许多不同类型的过滤，其复杂度也不同。[u32](http://www.lartc.org/lartc.html#LARTC.ADV-FILTER.U32)是最普通的、也是最易用的流过滤的。[这篇文章](http://git.coverfire.com/?p=linux-qos-scripts.git;a=blob;f=src-3tos.sh;hb=HEAD)虽然有些陈旧，但是你可以发现一些流过滤的例子。

对于更多的QDisc/class/filter细节，可以参考[LARTC HOWTO](http://www.lartc.org/howto/)手册和tc手册。

## 传输层和QDisc之间的缓存

回看一下前面的图片，你就会发现排队策略层之上是没有数据包队列的。 这意味着，网络栈直接把数据包放到了排队策略中，或者是抛给了上层的socket缓存中，如果队列已满的话。 很明显下一个问题是，当栈有大量的数据要发送时，会发生什么？这将导致TCP连接有着大的拥堵窗口，或者更坏的是上层应用尽它可能地快速地发送UDP包。答案是，对一个有单条队列的QDisc而言，驱动器队列也有相同的问题，这在图4中画了出来。也就是说，单个高带宽或者高数据包率的流能够耗尽队列的所有空间，从而引起数据包丢失，给其他流增加大的延时。更坏的是，这创建了另一个可以[使用标准队列](http://queue.acm.org/detail.cfm?id=2209336)的缓存点； 它增加了延时，引起TCP的RTT和拥堵窗口堵塞问题的计算。因为linux默认是pfifo_fast QDisc，它有一个高效的单队列（因为大多数traffic标识为TOS=0），所以这种现象也是常见的。

从linux 3.6.0(2012-09-30)，linux内核有了一个叫TCP Small Queues的新特性，它目的就是为了解决TCP的这种问题。TCP Small Queues对每一个TCP流进行限制，任何时候都对它可以进入QDisc和驱动器队列的字节数目进行约束。有一个有意思的边效是，使得内核可以及早地推回到应用，这允许应用可以更高效地优化对socket的写。当前(2012-12-28)，对于来自于其他传输协议的单个流来讲，还是可能会冲跨(flood)QDisc层的。

另一个解决传输层洪水的问题是用一个有多个队列的、每一个网络流一个队列的QDisc。Stochastic Fairness Queueing (SFQ) and Fair Queueing with Controlled Delay (fq_codel) QDiscs 恰好解决了这个问题。

## 如何操作linux中的队列大小

### 驱动器队列(Driver Queue)

[ethtool](http://linuxmanpages.net/manpages/fedora12/man8/ethtool.8.html)命令用于控制以太网设备的驱动器队列大小。它同样也支持低层接口的统计功能，以及开启和关闭IP栈和驱动特性的能力。

-g标识显示了驱动器队列(ring)的参数：
```
[root@alpha net-next]# ethtool -g eth0
Ring parameters for eth0:
Pre-set maximums:
RX:        16384
RX Mini:    0
RX Jumbo:    0
TX:        16384
Current hardware settings:
RX:        512
RX Mini:    0
RX Jumbo:    0
TX:        256
```

从上面的输出可以看到，这个NIC驱动器的传输队列默认有256个描述结构。早期的bufferbloat研究里，经常建议减小驱动器队列的大小，这样就可以减少延时。有了BQL的引入（假设你的NIC驱动器是支持的），再没有什么理由去修改这个队列大小了（看下面如何配置BQL）。

ethtool允许你来管理TSO／UFO／GSO这些优化特性。 -k标识显示了当前的offload设置，-K用于修改这些特性。
```
[dan@alpha ~]$ ethtool -k eth0
Offload parameters for eth0:
rx-checksumming: off
tx-checksumming: off
scatter-gather: off
tcp-segmentation-offload: off
udp-fragmentation-offload: off
generic-segmentation-offload: off
generic-receive-offload: on
large-receive-offload: off
rx-vlan-offload: off
tx-vlan-offload: off
ntuple-filters: off
receive-hashing: off
```
因为TSO，GSO，UFO，GRO大大地增加了驱动器队列中排队的字节数目，所以如果你想优化延时而非吞吐量时，应该把这些优化特性禁掉。要注意的是，当禁掉这些特性后，你会注意到CPU或者吞吐量会下降，除非你的系统正在高速地处理数据。

### Byte Queue Limits (BQL)

由于BQL算法是自调节的，所以你没有必要太多地调整它。当然，如果你在低比特率时确实很[关注优化延时](https://gettys.wordpress.com/2012/05/01/bufferbloat-goings-on/#comment-4053)，那么你可能想覆盖掉计算出来的LIMIT值。BQL状态和配置可以在/sys目录下面找到，需要基于NIC的位置和名字。我的服务器上eth0的目录是

```
/sys/devices/pci0000:00/0000:00:14.0/net/eth0/queues/tx-0/byte_queue_limits
```

这个目录下在面的文件有：
* hold_time: 修改LIMIT值的间隔，以ms为单位
* inflight: 尚未传输还在等待的字节数目
* limit: BQL计算出来的LIMIT值，如果NIC驱动不支持BQL的话，值为0
* limit_max: 可配置的最大LIMIT值。 如果优化延时，则将此值设置较低
* limit_min:可配置的最小LIMIT值。如果优化吞吐量，则将此值设置较高

要设置一个硬码的上限限制，可以使用下面的命令把值写入到limit_max文件中去
```
echo "3000" > limit_max
```

### txqueuelen是什么？

前面已经提过早期讨论bufferfloat时静态减小NIC传输队列的想法。传输队列的当前大小可以通过ip和ifconfig命令来获得。 令人迷惑的是，这些命令对传输队列长度的命名是不同的（黑体字）

> [dan@alpha ~]$ ifconfig eth0<br>
> eth0      Link encap:Ethernet  HWaddr 00:18:F3:51:44:10 <br>
>           inet addr:69.41.199.58  Bcast:69.41.199.63  Mask:255.255.255.248<br>
>           inet6 addr: fe80::218:f3ff:fe51:4410/64 Scope:Link<br>
>           UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1<br>
>           RX packets:435033 errors:0 dropped:0 overruns:0 frame:0<br>
>           TX packets:429919 errors:0 dropped:0 overruns:0 carrier:0<br>
>           collisions:0 **txqueuelen:1000**<br>
>           RX bytes:65651219 (62.6 MiB)  TX bytes:132143593 (126.0 MiB)<br>
>           Interrupt:23<br>

> [dan@alpha ~]$ ip link<br>
> 1: lo:  mtu 16436 qdisc noqueue state UNKNOWN <br>
>     link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00<br>
> 2: eth0:  mtu 1500 qdisc pfifo_fast state UP **qlen 1000**<br>
>     link/ether 00:18:f3:51:44:10 brd ff:ff:ff:ff:ff:ff<br>

linux中传输队列的长度默认为1000个数据包，这是一个比较大的缓存，特别是对一个低带宽来讲。

有意思的问题是，这个变量究竟控制着什么呢？我不太清楚，所以我花了一些时间来查看linux源码。我所知的是，txqueuelen只用来作为某些排队策略的队列长度的一个默认值。特别地，
* pfifo_fast (linux默认的排队策略）
* sch_fifo
* sch_gred
* sch_htb
* sch_plug
* sch_sfb
* sch_teql

回看图1， 这个参数控制的是排队策略盒子（上面所列的QDiscs）中队列的大小。对于这些大多数的排队策略，tc命令中的limit参数将覆盖掉txqueuelen的默认值。总得来说，如果你不使用上面所列的排队策略，或者你覆盖了队列的长度，那么txqueuelen值就是没有意义的。

另外，我发现了一点令人迷惑之处： ifconfig命令显示了关于网络接口的低层细节（像MAC地址），但是txqueuelen参数却指的是较高层的QDisc层。更合理的应该是，ifconfig应该显示驱动器队列的大小。

传输队列的长度使用ip/ifconfig命令来进行配置。
```
[root@alpha dan]# ip link set txqueuelen 500 dev eth0
```

注意一下，ip命令使用txqueuelen参数；但是，当显示接口信息时，它却使用的是 qlen —— 这是另一个不协调的地方。

### 排队策略

如前所述，linux内核有大量的排队策略，每一个都实现了自己的数据包队列和行为。详细地描述如何配置每一个QDiscs并不在本文的范围之内，这个可以查看tc手册。你可以在man tc qdisc-name(比方，man tc htb或者man tc fq_codel）中找到详情。[LARTC](http://www.lartc.org/)也是一个非常有用的资源，只是没有更新特性的信息。

下面是一些与tc命令的相关提示，可能会对你有用：
* The HTB QDisc implements a default queue which receives all packets if they are not classified with filter rules. Some other QDiscs such as DRR simply black hole traffic that is not classified. To see how many packets were not classified properly and were directly queued into the default HTB class see the direct_packets_stat in “tc qdisc show”.
* The HTB class hierarchy is only useful for classification not bandwidth allocation. All bandwidth allocation occurs by looking at the leaves and their associated priorities.
* The QDisc infrastructure identifies QDiscs and classes with major and minor numbers which are separated by a colon. The major number is the QDisc identifier and the minor number the class within that QDisc. The catch is that the tc command uses a hexadecimal representation of these numbers on the command line. Since many strings are valid in both hex and decimal (ie 10) many users don’t even realize that tc uses hex. See one of [my tc scripts](http://git.coverfire.com/?p=linux-qos-scripts.git;a=blob;f=src-3tos.sh;hb=HEAD) for how I deal with this.
* If you are using ADSL which is ATM (most DSL services are ATM based but newer variants such as VDSL2 are not always) based you probably want to add the “linklayer adsl” option. This accounts for the overhead which comes from breaking IP packets into a bunch of 53-byte ATM cells.
* If you are using PPPoE  then you probably want to account for the PPPoE overhead with the ‘overhead’ parameter.

### TCP Small Queues

对于每一个socket，TCP队列的限制可以通过 /proc文件来查看和控制：
```
/proc/sys/net/ipv4/tcp_limit_output_bytes
```
我的理解是，在任何正常的情况下，你都不需要去修改这个值。

## 非你所能控的超大队列

不幸地是，并不是所有影响你网络性能的超大队列都是你可控的。更普遍地，这些问题依赖底层设备或者服务提供商的自身设备。对于后者，你是无能为力的，因为你无法控制这些拥堵。然而，你在上流方向是可以调整拆封的，让它低于链接速率。你可以参考这些tc脚本的例子：[我所使用的](http://git.coverfire.com/?p=linux-qos-scripts.git;a=summary); [一些相关的性能结果](http://www.coverfire.com/archives/2013/01/01/improving-my-home-internet-performance/)

## 总结

数据包缓存中的排队是一个必需的组件。恰好地管理这些缓存的大小对于达到好的网络延时是至关重要的。与在减少延时中有着重要的角色的“固定的缓存大小”相比，实际的方案是对队列中数据量的智能管理。这可以通过动态方案，例如BQL和[active queue management(AQM)](http://en.wikipedia.org/wiki/Active_queue_management)技术（像Codel），来更好的实现。This article outlined where packets are queued in the Linux network stack, how features related to queueing are configured and provided some guidance on how to achieve low latency.

## 相关链接
* [Controlling Queue Delay ](http://queue.acm.org/detail.cfm?id=2209336)
* [Presentation of Codel at the IETF ](https://www.coverfire.com/archives/2012/08/13/codel-at-ietf/)
* [Bufferbloat: Dark Buffers in the Internet ](http://cacm.acm.org/magazines/2012/1/144810-bufferbloat/fulltext)
* [Linux Advanced Routing and Traffic Control Howto (LARTC) ](http://www.lartc.org/howto/)
* [TCP Small Queues on LWN](http://lwn.net/Articles/507065/)
* [Byte Queue Limits on LWN](http://lwn.net/Articles/454390/)

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
* queueing discipline, 排队策略
* traffic 拥堵，堵塞
* Hierarchical Token Bucket, [HTB](http://lartc.org/manpages/tc-htb.html)

## 参考
* [Queueing in the Linux Network Stack](https://www.coverfire.com/articles/queueing-in-the-linux-network-stack/)
