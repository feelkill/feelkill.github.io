---

layout: post

title: "FTA基本介绍和使用"

date: 2018-05-19

category: 2018年

keywords: Fault Tree Analysis, NASA, EDrawMax, OpenFTA, Free FTA

---

## 简介

FTA是PRA和系统可靠性评估中所使用的最重要的工具之一。FTA既适用于对现有的系统进行分析，也适用于分析正在设计中的系统。它可以对故障概率进行估算，也可以提供组件对故障的贡献程度，用于识别最需要进行改善的组件。

NASN在1981年的时候关于FTA就写过一版，到2002年的时候又更新过一版，本文是基于2002版阅读基础上的小结，主要是列出原文档中的要点以及自己的一点认识。原文主要分为两大部分，第一部分是关于相关概念介绍的，第二部分是几个case，用来演示FTA对实际系统的分析。

## 概念

FTA是从failure space(故障空间)来分析系统的。这种方法属于自顶向下的推演，与此相对应的是自底向顶的分析方法，例如FMEA方法。一个完整的FTA分析方法主要从几个步骤进行：

1. Identify the objective for the FTA.  定义目标
2. Define the top event of the FT.  定义顶级事件
3. Define the scope of the FTA.  定义范围
4. Define the resolution of the FTA.  定义粒度
5. Define ground rules for the FTA.  定义原则
6. Construct the FT.  构建故障树
7. Evaluate the FT.  评估故障树
8. Interpret and present the results. 解释和展示结果

![](/assets/2018/fta-step2.png)

在实际使用中，上面的步骤可以适当地裁减。可以看到，FTA的核心在于尽可能地全覆盖所有故障，然后对所有故障进行定性和量化地分析，找出里边风险较大的、需要解决的故障，给出必要的防御、探测和恢复的措施。围绕这一点来看，步骤2、6、7、8是不可缺少的；步骤1、3、4、5是实现目标的辅助手段，帮助目标可达成。

The top event defines the failure mode of the system that will be analyzed. 在这里，top event应该是围绕目标而给出的，那么就有可能存在多个top event；在这种情况下，只需要把所有的top event列出来，并对所有top event逐个进行分析即可。

对于分析范围，最佳实践是从接口和系统状态来划分界线。What is in the analysis will be those contributors and events whose relationship to the top undesired event will be analyzed. What is out of the analysis will be those contributors that are not analyzed. 可以看到，事件、引起事件的问题以及它们之间的关系是故障树的主要元素。

The resolution is the level of detail to which the failure causes for the top event will be developed. 范围和粒度可以依据实际要分析的事件进行调整。

For each event that is analyzed, the **necessary and sufficient immediate** events that result in the event are identified . 构建故障树的基本做法是，对于要分析的事件小步后退，回答给出直接原因。所有分解出出来的事件都按照此方法进行分析、分解，直到最小的、不可分解的事件出现，或者遇到最底层的根因。

故障树构建完成之后，就需要对故障树进行评估，主要包括定性地分析和量化分析。

## 术语

1. FTA， Fault Tree Analysis , 故障树分析
2. PRA，Probabilistic Risk Assessment， 可能风险评估



## 参考

1. [Fault Tree Handbook with Aerospace Fault Tree Handbook with Aerospace Applications Applications](https://kscddms.ksc.nasa.gov/Reliability/Documents/Fault_Tree_Handbook_with_Aerospace_Applications_August_2002.pdf)
2. [EMFTA in Github](https://github.com/cmu-sei/emfta)
3. [Open FTA](http://openfta.com/default.aspx)
4. [EdrawMax, 亿图画图软件，可画FTA](http://www.edrawsoft.cn/edrawmax/)
5. [EdrawMax 英文网站](https://www.edrawsoft.com/edraw-max.php) 
6. [draw.io Github](https://github.com/jgraph/drawio) 
7. [Process on在线绘图](https://www.processon.com/;jsessionid=B92F7EC85134BF79472917B09273C5FC.jvm1) 
8. [https://mermaidjs.github.io](https://mermaidjs.github.io) 