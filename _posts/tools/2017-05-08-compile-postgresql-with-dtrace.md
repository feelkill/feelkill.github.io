---
layout: post
title: "compile postgres with --enable-dtrace option "
date: 2017-05-08
category: 工具
keywords: systemtap, dtrace, fedora, postgresql
---

## 目的

使用systemtap支持的--enable-dtrace特性来编译postgresql代码，让其支持probe功能。

## 环境

OS: fedora 25, kernel 4.10.13-200.fc25.x86_64

```shell
[zhangchaowei@bogon postgres-master]$ stap --version 
Systemtap translator/driver (version 3.1/0.168, rpm 3.1-2.fc25)
Copyright (C) 2005-2017 Red Hat, Inc. and others
This is free software; see the source for copying conditions.
tested kernel versions: 2.6.18 ... 4.10-rc8
enabled features: AVAHI BOOST_STRING_REF DYNINST JAVA PYTHON2 PYTHON3 LIBRPM LIBSQLITE3 LIBVIRT LIBXML2 NLS NSS READLINE
```

postgresql: 9.6devel

## 安装过程

首先，需要安装成功安装systemtap, 叁考[fedora下安装systemtap](../06/install-systemtap-under-fedora.html)。对于用户态的支持，systemtap官方文档建议安装另外一个包systemtap-sdt-devel;使用root权限进行安装，安装成功之后，建议重新启动一下系统。

```shell
[root@bogon ~]yum install systemtap-sdt-devel
```

然后，对于普通用户使用systemtap，需要将该用户加入到stapusr/stapsys/stapdev中的其中之一的用户组里，也可以将用户加入到所有的用户组内。这样，才可以获得必要的执行权限。

```shell
[zhangchaowei@bogon postgres-master]$ groups
zhangchaowei stapusr stapsys stapdev
```
然后，需要设置环境变量，主要是关于DTRACE/TRACEFLAGS的。DTRACE主要是与systemtap相关，而TRACEFLAGS主要是对于64位机器来讲进行设置的；后者也可以在编译前的configure中进行指定的，我们在后面进行configure设置。在$HOME/.bashrc文件中设置$DTRACE和$STAP两个环境变量，结果如下：

```shell
[zhangchaowei@bogon postgres-master]$ echo $DTRACE
/usr/bin/dtrace
[zhangchaowei@bogon postgres-master]$ echo $STAP
/usr/bin/stap
```
同时需要设置库的链接位置， 在$HOME/.bashrc文件中增加以下一行：

```shell
export LD_LIBRARY_PATH=/usr/lib64/systemtap:$LD_LIBRARY_PATH
```

这里需要注意的一个点是，**$DTRACE的变量值设置为了dtrace，而不是之前安装好的stap**。为什么呢？可以看一下两者有什么区别吧，

```shell
[zhangchaowei@bogon postgres-master]$ file /usr/bin/dtrace 
/usr/bin/dtrace: Python script, ASCII text executable
[zhangchaowei@bogon postgres-master]$ file /usr/bin/stap
/usr/bin/stap: ELF 64-bit LSB shared object, x86-64, version 1 (GNU/Linux), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 2.6.32, BuildID[sha1]=42bb86fbce04158ccdfc562fd3e5a4ac758a934c, stripped
```

很明显了，stap是安装的真正的二进制可执行文件，而dtrace只是一个python脚本。可以使用vim去看一下dtrace脚本的内容，可以知道这个脚本主要是处理与Dtrace工具(另一个操作系统平台下安装的系统工具)中的一些命令参考，主要是-C,-G, -h这三个参数；因为stap命令没有这几个参数，是处理不了的。为了让postgresql可以编译成功，使用了脚本处理了这样的一个差异；即用python脚本处理生成了头文件和.o文件的。：( 我在这一点上吃了个大亏，折腾了一天，把stap的官方文章读了一次又一次，试图在$DTRACE=/usr/bin/stap的前提下完成了这一项编译工作，正要自己撸起袖子写一个转换脚本时，突然发现了dtrace脚本，差点吐血。

下面就可以开始正常的编译postgresql代码了，依次执行下面的命令即可:

```shell
chmod +x configure
./configure CC="gcc" --enable-dtrace --enable-profiling --with-python --with-ldap --with-openssl  --with-libxml --with-libxslt TRACEFLAGS='-64' --prefix=/home/zhangchaowei/Documents/pg/codes/install
make 
make install
```

## 可能的问题

如果$DTRACE配置错误为stap的话，会遇到如下的错误
```shell
/usr/bin/stap -C -h -s probes.d -o probes.h.tmp
/usr/bin/stap: invalid option -- 'C'
Try '--help' for more information.
Makefile:38: recipe for target 'probes.h' failed
```
其他一些依赖库的安装失败，则会有相应的提示； 同时也可以在网上很容易地搜索到相应的解决方法，此处不再列出。

## 参考文章

* [IBM对于system安装和使用介绍](https://www.ibm.com/developerworks/cn/linux/l-cn-systemtap3/index.html)
* [IBM对于system安装和使用介绍](https://www.ibm.com/developerworks/cn/linux/l-systemtap/)
* [postgresql对dtrace的介绍](https://www.postgresql.org/docs/8.4/static/install-procedure.html)
* [网上最常见的一篇关于介绍postgresql+systemtap的文章](http://blog.163.com/digoal@126/blog/#m=0&t=1&c=fks_084068084086080075085082085095085080082075083081086071084)
* [维基对于用户态控针的详细说明](https://sourceware.org/systemtap/wiki/AddingUserSpaceProbingToApps)
* [Dtrace命令行说明](http://dtrace.org/guide/chp-dtrace1m.html)
* [Utrace](https://github.com/utrace/linux/tree/utrace-3.3)
* [Utrace wiki](https://sourceware.org/systemtap/wiki/utrace)
