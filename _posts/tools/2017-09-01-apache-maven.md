---
layout: post
title: "java的下载链工具maven"
date: 2017-09-01
category: 工具
keywords: maven, java
---

## 介绍

 Maven is a software project management and comprehension tool. Based on
 the concept of a Project Object Model (POM), Maven can manage a project's
 build, reporting and documentation from a central piece of information.

 Maven是一个软件的项目管理和整合的工具。它基于POM理念，可以管理一个项目的构建、报告和文档。最新的文档可以在[https://maven.apache.org/](https://maven.apache.org/)里找到。

## 安装

**系统要求：**

* JDK 1.7或更高版本
* 内存： 无最小要求
* 磁盘： 安装的最小要求是100MB
* 操作系统要求： Windows 2000或更高版本; Unix系统无最小要求;

**安装过程：**

1. 解压压缩包，
  *  tar zxvf apache-maven-3.x.y.tar.gz  (unix OS)
  *  unzip apache-maven-3.x.y.zip  (Windows OS)
2. 解压后将看到apache-maven-3.x.y"目录被创建出来了。
3. 将该路径加入到PATH环境变量中，或者将这个目录mv到已有的PATH环境的目录下面
  * export PATH=/usr/local/apache-maven-3.x.y/bin:$PATH (Unix OS), 可以将该命令加入到~/.bashrc中；
  * set PATH="c:\program files\apache-maven-3.x.y\bin";%PATH% (Windows)
4. 确保JAVA_HOME已经设置并且是正确的;
5. 运行mvn --version来查看输出是否为预期的mvn版本信息。

## 参考
* [官网下载地址](http://maven.apache.org/download.cgi)
* [安装指导](https://maven.apache.org/download.html#Installation) 
* [Home Page](https://maven.apache.org/)
* [Release Notes](https://maven.apache.org/docs/history.html)
* [Mailing Lists](https://maven.apache.org/mail-lists.html)
* [Source Code](https://git-wip-us.apache.org/repos/asf/maven.git)
* [Issue Tracking](https://issues.apache.org/jira/browse/MNG)
* [Wiki](https://cwiki.apache.org/confluence/display/MAVEN/)
* [Available Plugins](https://maven.apache.org/plugins/index.html)
