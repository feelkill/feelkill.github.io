---
layout: post
title: cmake构建系统的基理
date: 2021-01-24
category: 2021年
keywords: cmake, build systems, target, dependencies, library
---

# 概要

cmake构建系统中最核心的概念是target。 一个target可能是：

- an executable, 一个可执行目标。
- a library, 一个库目标。
- A custom target，一个定制化命令集。 

target之间的依赖关系是指两个方面：

- 构建顺序，谁先构建，谁后构建。
- 增量构建。当被依赖者改变之后，target重新生成的规则。 

# binary target 

主要包括两类：一类是binary executable，一类是binary library。 Dependencies between binary targets are expressed using the [`target_link_libraries()`](https://cmake.org/cmake/help/v3.18/command/target_link_libraries.html#command:target_link_libraries) command。 这一句是个重点，表明了target之间的依赖关系要通过函数target_link_libraries函数来传递。 

## binary executables

这跟通常理解的可执行文件是一致的，主要通过add_executable()函数来生成。 

## binary library

库的分类主要有静态库、动态库、object库三类。 

使用函数add_library()函数生成的库文件主要是静态库和动态库两类， 前者传入的是static参数，后者传入的是shared参数。 这二者一般也称为常规库。

object库是一个新颖的概念，它不同于静态库，可以简单理解为一个object files的集合。object library可以作为静态库生成的source列表，也可以作为可执行文件生成的source列表。

# 伪target

伪target有三种：imported target; alias target; interface library。 以下三种target还没有实践经验，使用后继续补充。

## imported target

表示一个预先存在的依赖项。 一般而言，这些target是由上游包定义的，一般可以认定为不可变的。当然，你也可以通过相应的函数接口来个性imported target的编译、链接属性。 

这类target有一个比较重要的属性是location。 默认情况下，imported target的定义范围是它定义的目录，它可以从子目录进行访问和使用，但却不能从父目录和兄妹目录进行访问。 当前，你也可以定义一个global imported target，以供整个构建系统全局访问。

## alias target

相当于给已有的target起了个别名。 这类target整个构建系统来讲，是局部的。 

## interface library

特别类似于imported target，主要区别在于：

- 没有location属性。

- 可变的。

这类库主要有几个使用场景：

- Header-only library。  这种场景下，库文件 只有头文件，没有实现文件 。 
- 使用一个完全以target为焦点的设计。 什么意思呢？interface library的编译、链接选项可以传递给要生成的可执行目标。