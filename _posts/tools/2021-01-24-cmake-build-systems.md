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

# 构建规格和使用条件

与编译构建相关的头文件目录、编译宏、编译选项（对应函数为[`target_include_directories()`](https://cmake.org/cmake/help/latest/command/target_include_directories.html#command:target_include_directories), [`target_compile_definitions()`](https://cmake.org/cmake/help/latest/command/target_compile_definitions.html#command:target_compile_definitions) and [`target_compile_options()`](https://cmake.org/cmake/help/latest/command/target_compile_options.html#command:target_compile_options) )操作函数明确了binary target的构建规格和使用条件。这些命令会相应地将target属性中与头文件目录、编译宏、编译选项传播出去，也可能包括INTERFACE_*相关的属性。

这些命令有三种模式：private; public; interface.  private模式只会传播**非INTERFACE_**的属性。 interface模式只会传播**INTERFACE_**的属性。 而public模式会同时将两种属性都传播出去。 每一个命令都可以将每种模式多次使用。

要注意的是，使用条件并不是为了方便使用，也不是建议，而是必要条件。

## target属性

[`INCLUDE_DIRECTORIES`](https://cmake.org/cmake/help/latest/prop_tgt/INCLUDE_DIRECTORIES.html#prop_tgt:INCLUDE_DIRECTORIES)传入的参数是与头文件目录相关的，传入顺序是重要的、要讲究的。

[`COMPILE_DEFINITIONS`](https://cmake.org/cmake/help/latest/prop_tgt/COMPILE_DEFINITIONS.html#prop_tgt:COMPILE_DEFINITIONS)传入的参数是编译宏定义，传入顺序并不重要。

[`COMPILE_OPTIONS`](https://cmake.org/cmake/help/latest/prop_tgt/COMPILE_OPTIONS.html#prop_tgt:COMPILE_OPTIONS)传入的参数是编译优化选项相关的， 其传入顺序也是要讲究的。

这三个函数影响的是源文件的编译。 而 [`INTERFACE_INCLUDE_DIRECTORIES`](https://cmake.org/cmake/help/latest/prop_tgt/INTERFACE_INCLUDE_DIRECTORIES.html#prop_tgt:INTERFACE_INCLUDE_DIRECTORIES), [`INTERFACE_COMPILE_DEFINITIONS`](https://cmake.org/cmake/help/latest/prop_tgt/INTERFACE_COMPILE_DEFINITIONS.html#prop_tgt:INTERFACE_COMPILE_DEFINITIONS) and [`INTERFACE_COMPILE_OPTIONS`](https://cmake.org/cmake/help/latest/prop_tgt/INTERFACE_COMPILE_OPTIONS.html#prop_tgt:INTERFACE_COMPILE_OPTIONS)里的内容则是使用条件； 使用者需要使用它们来正确地编译和链接自己的target。 让这一点起作用的桥梁，是函数target_link_libraries()的调用。

## 使用条件的传递

通过函数target_link_libraries()的调用，可以使得使用条件得以传递给被依赖者target。 同样，传递模式也是三种：private; interface; public。 

private模式表示，使用条件不会被传递，仅是链接要使用的库文件 。

public模式表示，使用条件全部会传递给被依赖者target，包括了头文件和库文件。

interface模式表示，仅使用头文件的依赖关系，不使用库文件的依赖关系。

这里要稍微区别一下两处的模式（或者也可称为权限控制）。 前面与include/defination/options相关的权限控制，是从被依赖者的角度来讲，我控制哪些属性允许别人使用； 后面与link相关的权限控制，是从依赖者的角度来讲，我控制我使用哪些属性。

## 接口属性冲突了怎么办？

在属性传递过程中，如果发生了冲突怎么办？ 基本想法就是Compatible Interface Properties。

此外，还有部分属性是用于调试的。

## 生成表达式

生成表达式的理念很简单，就是运行时生成条件或集合。 当前生成表达式在头文件目录和链接库的设置函数中各有区分，在使用的时候可以参考手册。

## 输出文件

输出文件主要是指与target对应的、磁盘上生成的动态库文件、静态库文件、可执行文件。这几类文件都可以通过接口中属性参数的值来指定。

## 目录范围的命令

以target\_为前缀的三个函数影响范围是target，而不带target\_前缀的[`add_compile_definitions()`](https://cmake.org/cmake/help/latest/command/add_compile_definitions.html#command:add_compile_definitions), [`add_compile_options()`](https://cmake.org/cmake/help/latest/command/add_compile_options.html#command:add_compile_options) ,[`include_directories()`](https://cmake.org/cmake/help/latest/command/include_directories.html#command:include_directories)作用相似，只是影响范围仅在目录范围之内。

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