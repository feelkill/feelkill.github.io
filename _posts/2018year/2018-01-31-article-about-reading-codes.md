---
layout: post
title: "阅读代码的技巧"
date: 2018-01-31
category: 2018年
keywords: 总结，分享，阅读，代码，修复，缺陷
---

## 引子

上周有一个将近半年没有解决掉的问题，我集中精力分析core文件，然后通过阅读源代码，竟然把根因找出来，解决掉了。 

这周也有一个低概率问题，涉及到了第三方开源库libevent，该问题发现了快一个月，分析一直没有突破。周一组内安排我投入，我花了一天的时间把libevent的原理弄大致明白，再把源代码梳理了一次，反复推理了几次，竟然把根因找出来了，问题得到了解决。

基于这两个事情，组内同事问我关于代码阅读来修复缺陷的事。我之前也没有好好想过这方面的小结。对于代码的书写和阅读，从误入软件开发这个行业开始，我是一直有自省的，例如：如何书写代码才能更少地犯错？如何阅读代码才能够更快地理解？如何阅读代码才能够更快地发现问题？等等。我想，这可能只是一个开始，写得不一定会很全面和细致，后面还会有此类的一些总结。还是按照现有风格吧，想到哪里，就写到哪里。

## 书写代码

关于写代码的技巧性说明，网上文章很多。谈谈自己的另外一些看法。

### **晚上不要写代码** 

无数个事实说明，晚上提交的代码必然会引入新的问题，晚上最好不要写代码，进行问题的修复。对于平常工作的人来讲，一整天的工作是很花费精力的。基本来讲，到正常下班时间的时候，大脑很难再有精力继续创造了。比较好的建议，晚上时间用来自己学习充电。

### **连续写代码时长不要超过4个小时**

这一点跟上一点稍有差别，在于连续写代码的时长。对于自己而言，能够安静地坐着写代码，会产生一种非常满足感。但是，连续长时间写代码的时候，经常会发现一段时间之后，写代码的质量是会下降的，主要的表现在于：思考的速度会减慢；问题思考会遗漏，代码分支很容易考虑不全面；还有一种时，问题的思考进入一种do while(1)的无效循环中。

### **反复阅读实现逻辑，找出可能的漏洞**

许多问题是可以直接在书写代码的时候发现和解决掉的。这可以由两点来保证：第一种就是高效的阅读代码逻辑，发现可能的漏洞； 第二种，配合上详细的流程图，能够看出哪里有了遗漏。流程图的方法应该在功能设计的时候就用了，到了代码实现细节的时候，阅读代码是更好的选择。书写代码之后，需要立即进行反复地阅读，反复思考可能存在的问题，哪些情况没有考虑到。

### **最好能够使用用例进行全面测试覆盖**

TDD，测试驱动开发是一种非常不错的选择，用来保证开发代码的功能逻辑是100%正确的、符合预期的。不过，并不是所以的函数都需要做，对于if分支很少，代码逻辑非常简单的函数来讲，是没有必要的。如果if else if分支中判定逻辑比较复杂，同时存在逻辑上的与、或、非组合的话，建议进行TDD方法。毕竟，凡人脑袋能够思考到的层次是不多的，寻找逻辑问题时，也常常是单点地看，可能会把已经修复好的问题再次open了。那么，有一组用例来保证不引入或者打开issure是非常明智的方法。

### **把你的代码翻译成你的母语**

提高书写代码的方法还有一种，就是传说中的小黄鸭法：跟前放一个小黄鸭，然后把你书写的代码读给它听。其实这个方法的本质时，把自己书写的代码读出来，反馈给自己，让大脑来看是否存在可能的逻辑缺陷。那么，阅读代码时你会使用什么样的语言呢？还是C语言的方式吗？以我看来，不应该用C语言，而应该使用你的母语，把它像讲故事或者说道理一样地讲述出来。在这个过程中，既是使用另一种方法来检阅代码，也是实践小黄鸭方法的最好途径。

## 阅读代码

### **使用好的IDE不中断思考**

阅读代码的首要前提是，不能打断思维的连续性。所以，使用一个好的IDE软件是必不可少的。在windows下面，建议使用source insight这个软件，它可以让开发人员更专注于代码阅读本身，而不是操作代码关系本身。

### **使用你的母语翻译正在阅读的代码**

代码是一种语言，母语是另一种语言。你阅读代码的时候，应该把代码语言翻译为母语来叙述；写代码则相反，是把母语的逻辑翻译为了代码语言的。所以，阅读代码更好的方法就是把它翻译为你的母语，对着小黄鸭说这段代码的功能是什么，逻辑是什么样的，如何实现的。我使用这种方法的时间比较长久，个人认为效果是相当不错的。

### **理解它的逻辑和内在的想法**

阅读代码的直接目的是想弄明白这段代码究竟要实现什么功能，它使用了什么算法，这个算法的核实思想是什么，算法本身是否有漏洞，实现细节上是否与算法本身不符之处，等等。所以，阅读代码一定要努力地去理解它所表达的内容，而不是一团代码过去，不知所以，更不用讲其背后传达的算法和逻辑了。

### **打破线性思维，并发、异步和时间窗**

在多核、多线程实现中，一定要打破线性思维。很简单，两个线程的执行次序是未知的，多次执行谁前谁后都不一定。协同资源上的如果不做保护的话，就会有异步的问题，即使上逻辑上看着是ok的，也可能会存在时间窗的问题。不要理所当然地认为，pthread_create函数没有调用返回，子线程就不会执行完毕。对于同一个线程来讲，信号处理同样会打破线性关系的。

### **阅读，阅读，再阅读**

阅读代码能力的提高，没有捷径，只有反复地阅读，阅读，再阅读。这跟学习英语、学习数学这些科目是一个道理的，需要不停地训练和积累。亦无他，唯熟耳。