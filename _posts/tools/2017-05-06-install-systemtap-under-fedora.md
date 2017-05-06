---
layout: post
title: "install systemtap under fedora"
date: 2017-05-06
---

# 目的

记录在fedora OS下面安装systemtap过程中所遇到的问题以及解决的方法。

# OS环境

fedora 25 

kernel version: 4.9.xx-yy.f25.x86_64 ( 当时的小版本未记录，以xx-yy来替代 )

# 安装过程

首先需要获得正确的linux kernel版本号: —— 这一点相当地重要，后续的kernel包都需要使用到这一信息，当且仅当kernel包版本是与该版本号对应一致的，安装才会成功

```shell
[zhangchaowei@bogon jekyll_blog]$ uname -r
4.9.xx-yy.f25.x86_64
```

安装systemtap需要root权限的。在fedora系统下已经有了现成的命令是可以直接安装这些kernel包的，主要命令如下：

```shell
[root@bogon jekyll_blog]$ yum install systemtap systemtap-runtime
```

上面命令执行成功后， 可以查看一下与stap命令相关的执行文件有哪些,stap命令之后使用了TAB按键:

```shell
[root@bogon tools]$ stap
stap         stapdyn      stap-merge   stap-prep    stap-report  staprun      stapsh       
[root@bogon tools]$ stap
```

可以看到，stap是已经安装好了，但是它还是不能够成功使用的。这还需要安装对应版本的kernel包，主要是devel,-debuginfo和-debuginfo-common三个包。使用如下命令：

```shell
[root@bogon jekyll_blog]$ stap-prep
```

很悲惨地来讲，上面这一个命令很多情况下是很失败的，特别是对于小版本来说，很可能就不存在与之对应的那三个包。哪怎么办呢？ 答案是先查看一下，哪些kernel版本是存在这三个包的。这个可以从下面两个地址上进行查询：

[RPM resource kernel-devel: https://www.rpmfind.net/linux/rpm2html/search.php?query=kernel-devel](https://www.rpmfind.net/linux/rpm2html/search.php?query=kernel-devel)

[RPM  search: http://rpm.pbone.net/](http://rpm.pbone.net/)

在以上两个网站中输入对应的os过滤条件，就可以看到有哪些kernel-devel/kernel-debuginfo包是可用的。由于我是kernel 4.9版本，搜索的较高版本为4.10，主要是kernel-devel-4.10.13-200.fc25.x86_64.rpm这个了。接着，就需要fedora os kernel版本来匹配这个了。有两条路，要么升内核，要么降内核。幸运地是，我只需要直接升级内核就可以。 查询可用内核如下：

```shell
[root@bogon jekyll_blog]$ yum list kernel
```

而kernel 4.10.13-200.fc25.x86_64正好是查询结果，是可以正确升级上去的版本。没啥可说的，升内核版本吧。降内核的问题没有遇到过，不知道是不是相同的操作，按我的想法，降内核应该是有一定内险的，要慎重！

```shell
[root@bogon jekyll_blog]$ yum install --best --allowerasing  kernel.x86_64
```

内核升级成功之后，是需要重新启动操作系统的。重新成功之后， 再次执行如下命令：

```shell
[root@bogon jekyll_blog]$ stap-prep
```

这条命令就可以成功执行完了。需要的时间要长一些，要耐心地等待会。

最好再重新启动电脑，然后测试一下是否可以正确运行的。

```shell
[root@bogon jekyll_blog]$ stap -ve 'probe begin { log("hello world") exit() }'
Pass 1: parsed user script and 474 library scripts using 276068virt/73728res/7372shr/66612data kb, in 390usr/60sys/1521real ms.
Pass 2: analyzed script: 1 probe, 2 functions, 0 embeds, 0 globals using 278576virt/76520res/7552shr/69120data kb, in 30usr/0sys/53real ms.
Pass 3: translated to C into "/tmp/stapUn78es/stap_1e2f9a61e29975c49b8bd29d6e02b7db_1113_src.c" using 278576virt/76520res/7552shr/69120data kb, in 0usr/0sys/0real ms.
Pass 4: compiled C into "stap_1e2f9a61e29975c49b8bd29d6e02b7db_1113.ko" in 3020usr/1200sys/11828real ms.
Pass 5: starting run.
hello world
Pass 5: run completed in 10usr/40sys/512real ms.
```

恭喜你，systemtap已经成功安装在你的操作系统上了。下一步，就看你怎么用它了。

# 参考文档

* [安装systemtap的主要官方指导文档 https://sourceware.org/systemtap/SystemTap_Beginners_Guide/using-systemtap.html#using-setup](https://sourceware.org/systemtap/SystemTap_Beginners_Guide/using-systemtap.html#using-setup)
* [内核安装参考 http://www.2cto.com/os/201204/125945.html](http://www.2cto.com/os/201204/125945.html)
* [RPM resource kernel-devel: https://www.rpmfind.net/linux/rpm2html/search.php?query=kernel-devel](https://www.rpmfind.net/linux/rpm2html/search.php?query=kernel-devel)
* [RPM  search: http://rpm.pbone.net/](http://rpm.pbone.net/)
