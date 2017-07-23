---
layout: post
title: "gdb的python扩展"
date: 2017-07-15
category: 工具
keywords: linux, gdb, python, extension
---

之前简单地介绍过了一个关于gdb脚本的文章，提到了关于这类脚本先天性的缺陷，其实主要在于处理数据的能力要弱得很。gdb的扩展脚本支持了python + Guile这两种，前者为常见的编程语言；后者则在中国区内不怎么流行的。所以就主要以对python扩展脚本为学习了。

在进入正文之前需要理解一个核心的点是：python扩展本身的作用与gdb脚本的作用是一样的，只不过是使用python来替换gdb本身的实现。python使用的是面向对象的思想来实现的。在介绍之前，我们需要有一个整体的理解。



## 参考

* [gdb externsion](https://sourceware.org/gdb/onlinedocs/gdb/Extending-GDB.html)