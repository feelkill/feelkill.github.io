---
layout: post
title: "gdb脚本基本入门"
date: 2017-07-08
category: 工具
keywords: gdb, scripts, extension
---

本文的目的在于介绍一下gdb扩展脚本是怎么书写和使用的。最常见的gdb扩展脚本有两种：gdb脚本; python脚本。本文主要是指gdb scripts，关于python script会在单独的另一个文章中进行入门介绍。

gdb脚本的扩展称之为[Sequences](https://sourceware.org/gdb/current/onlinedocs/gdb/Sequences.html#Sequences)。说白一点，就是你在gdb交互界面是中怎么使用的，就简单地把这些命令按序写在一个文件中即可；这是最基本的思想。当然，除此之外，还有一些较为特殊的用于控制跳转方面的。

## 定义一个gdb函数

把具有一定功能的gdb命令组合起来，然后再给它一个好听易记的名字，这就是gdb的函数，直接使用关键字define开始就行。例如，
```
1.  define adder
2.    print $arg0 + $arg1 + $arg2
3.  end
```

这就定义了一个adder的函数，这个函数需要以关键字end来结束。可以稍微详细地说明一下。第1行以关键字开头定义了一个adder名字的函数；第2行定义了这个函数执行的gdb命令；第3行以关键字end结束了这个函数。 在第2行中还给出函数参数的名字，第1个参数为arg0，第2个参数为arg1, 依次类推地；当前最新版本中支持的参数个数是不受限的了。

关于著名的缩进大战这个问题，纯看个人喜好了。我建议使用2个空格进行缩进就行； gdb本身是没有缩进要求的，但是应该不可以使用tab缩进的， 因为tab在gdb交互界面中是一个用于输出提示命令作用的。

## gdb脚本的主要语法

整体来看，C语法是怎么样写的，gdb脚本的语法就怎么写，并且好多的判定和关键字也是相同的。以下面的例子来看：

```
define adder
  set $i = 0
  set $sum = 0
  while $i < $argc
    eval "set $sum = $sum + $arg%d", $i
    set $i = $i + 1
  end
  print $sum
end
```

定义需要使用的局部变量，是使用set $i = 0的方法； 按我的理解，gdb是没有声明一说的，它是直接定义并赋值的，所以变量的前面是需要直接使用$符号的。

多个命令之间可以放在不同行上，单个命令独占一行； 行与行之间不需要C语句的;分隔符。 当然，能不能将多个命令放在一行上呢，猜测是可以的（自己没有试过），不过不太建议；这样不易于阅读。

变量的类型不受约束的，都可以是你自己调试代码中的结构体等复杂数据结构体。至于属于哪种类型，这要看你赋的初值了；简单地可以将它理解为自动类型推导吧，这不影响你对它的使用的。

两个变量之间的运算，满足你在交互式界面中使用print后面的所有运算表达式就行。对于自增操作，只能使用 $i=$i+1的方法；抱歉，没有C语言的 ++ 或者 +＝ 这种，毕竟只是命令脚本。

来简单看一下与C语言中对照的控制关键字，有些还是有区别的（循环控制）

* if/else
* while
* loop_break
* loop_continue
* end

if/else的使用方法与C语法是一致的，可以使用的形式有： if  + end; if + else + end。 if后面的bool表达式使用C逻辑与、或、非来拼起复杂逻辑来。

while循环与C语言的while是一致的，同样以end结束整个循环。逻辑表达式与上面所述是一致的。

由于C语言中的break/continue已经被使用于gdb中的打断点和继续调试的命令，所以gdb中的while控制结构中不能够再使用这两个来进行结构控制，对应使用的就是 loop_break + loop_continue这两个。

## 输出控制

输出控制主要有如下几种方法：

1. p/print， 直接使用gdb中的输出命令来输出结果；
2. echo text, 可以在这种方法中使用不可打印的字符； 
3. output expression, 直接输出表达式对应的数值， 不再输出换行， 不再输出‘$nn=’前缀； 
4. output/fmt expression, 与上相同，多了格式控制输出符; 
5. print template, expression  与C语言中的printf是非常地相似的，只是控制符不尽相同的
6. eval template, expression  先对template部分做格式化， 然后调用eval来计算对应字符串

## 如何使用

首先使用source命令把脚本内容加载进来。然后直接使用函数名＋参数的方式来执行已经定义好的命令序列即可。

对于调试过程中的脚本，可以重复地使用上面的步骤来测试gdb脚本； 当提示是否覆盖已有函数的定义时，直接选择yes就好。

把gdb函数定义中的关键字define直接换为document，就可以为对应函数名写帮助文档了。这样，你只有直接使用 help <function name>的方法就可以查看到函数的使用说明了。

## 存在的缺陷

gdb脚本最大的一个问题是，无法处理获得的数据，或者说是已有的gdb命令在处理和加工数据方面显得很无力和低效。除此之外，还有一个是，它的执行效率也是比较低的。

正是这一问题的存在，所以才更有必要使用python脚本来扩展处理。当然，这是我认为最主要的原因：数据处理和加工。效率方面，则感觉不是有很大地提升了；想想，debug版本里处理这些问题，效率的要求也显得不是那么太重要了，关键还是得先可以处理数据。

## 参考

* [GDB官方文档](https://sourceware.org/gdb/current/onlinedocs/gdb/Extending-GDB.html#Extending-GDB)

