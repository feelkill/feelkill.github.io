---
layout: post
title: "Reactor设计模式"
date: 2018-02-17
category: 2018年
keywords: Reactor, 设计模式, Design Pattern
---

论文地址：[Reactor An Object Behavioral Pattern for Demultiplexing and Dispatching Handles for Synchronous Events](http://www.dre.vanderbilt.edu/%7Eschmidt/PDF/reactor-siemens.pdf)

参考链接已经把Reactor模式讲得很是明了了，只把一些关键的图和文字要点copy+paste了过来。

![Reactor模式](/assets/2018/Reactor_Simple.png)

![Reactor模式结构UML图](/assets/2018/Reactor_Structures.png)

**Handle**

即操作系统中的句柄，是对资源在操作系统层面上的一种抽象，它可以是打开的文件、一个连接(Socket)、Timer等。由于Reactor模式一般使用在网络编程中，因而这里一般指Socket Handle，即一个网络连接（Connection，在Java NIO中的Channel）。这个Channel注册到Synchronous Event Demultiplexer中，以监听Handle中发生的事件，对ServerSocketChannnel可以是CONNECT事件，对SocketChannel可以是READ、WRITE、CLOSE事件等。

**Synchronous Event Demultiplexer**

阻塞等待一系列的Handle中的事件到来，如果阻塞等待返回，即表示在返回的Handle中可以不阻塞的执行返回的事件类型。这个模块一般使用操作系统的select来实现。在Java NIO中用Selector来封装，当Selector.select()返回时，可以调用Selector的selectedKeys()方法获取Set<SelectionKey>，一个SelectionKey表达一个有事件发生的Channel以及该Channel上的事件类型。上图的“Synchronous Event Demultiplexer ---notifies--> Handle”的流程如果是对的，那内部实现应该是select()方法在事件到来后会先设置Handle的状态，然后返回。不了解内部实现机制，因而保留原图。

**Initiation Dispatcher**

用于管理Event Handler，即EventHandler的容器，用以注册、移除EventHandler等；另外，它还作为Reactor模式的入口调用Synchronous Event Demultiplexer的select方法以阻塞等待事件返回，当阻塞等待返回时，根据事件发生的Handle将其分发给对应的Event Handler处理，即回调EventHandler中的handle_event()方法。

**Event Handler**

定义事件处理方法：handle_event()，以供InitiationDispatcher回调使用。

**Concrete Event Handler**

事件EventHandler接口，实现特定事件处理逻辑。

![模块交互流程](/assets/2018/Reactor_Sequence.png)

## 参考链接

* [Reactor模式详解](http://www.blogjava.net/DLevin/archive/2015/09/02/427045.html)
* [Reactor Pattern WikiPedia](https://en.wikipedia.org/wiki/Reactor_pattern#cite_ref-1)
* [SEDA: An Architecture for Well-Conditioned, Scalable Internet Services](http://nms.lcs.mit.edu/~kandula/projects/killbots/killbots_files/seda-sosp01.pdf)

