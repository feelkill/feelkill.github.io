---
layout: post

title: "论文：关于并发控制论文集的小结"

date: 2018-07-14

category: 2018年

keywords: 并发控制，悲观并发控制， 乐观并发控制， OCC，

---

## 论文：On Concurreny Control by Multiple Versions

### 时间

 1982 ACM

### 主要贡献

定义了MVSR（MultiVersion Serializability），并给出了关于MVSR的几个定理和推论。

### 关键要点

#### 数据多版本的核心思想

更新数据并不覆盖已有的数据，而是新增一个版本的数据；这样，当并发读请求时，可以选择一个合适版本的数据来响应。

#### 串行化与MVSR的关系

并发控制有两个基本的目标：保证尽可能多的并行； 保证并发执行的正确性。而串行化（ Serializability ）是实现后者目标的主要方法。

实现并发控制的路径是多样的，其中多版本数据是常见的一种。MVSR就是实现多版本数据方法中、保证并发正确性的一个方法理论。

#### 相关定理和推论

定理1： MVSR是一个完全NP问题

定理2： 当调度s是一个有向不循环图时，它是一个MVSR

定理3： 在action模型中，MVSR等同于串行化（Serializability）

定理4： MVSR是多版本方法中能够达到并行度的上限值。也就是说，serializability 相当于一个版本，MVSR相当于无穷个版本；在这二者之间，存在一个无限的、严格的、包括特级关系（infinite strict hierarchy）。 如果可以保留数据的k+1个版本的话，并发控制的调度就有多于k种。 （By keeping up to k+1 versions of each entity one can “serialize” more schedules than with k. ）

定理5： DMVSR cannot be scheduled on-line, even for the restricted two-step model. 其中，满足定理2的MVSR称为DMVSR。 