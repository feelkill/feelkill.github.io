---
layout: post
title: "OpenSSL: PKI组成"
date: 2017-06-12
category: 工具
keywords: OpenSSL, CA
---

![](/assets/2017/openssl-pki-00.png)

### 基本过程：

1. 请求者生成一个CSR，并把它提交给CA；
2. CA基于CSR产生一个证书，并把它返回给请求者； 
3. 在某个时间点，证书如果被撤消的话，CA把它加入到CRL中； 

### 组件

**Public Key Infrastructure (PKI)**

公钥基础设施，一种安全架构，信任由可信的CA签名来传递

**Certificate Authority (CA)**

证书授权中心，产生证书和CRL

**Registration Authority (RA)**

注册中心，处理PKI的登记

**Certificate**

证书，CA签发的直接绑定了公钥和用户ID

**Certificate Signing Request (CSR)**

证书签发请求，里边包含了用于认证的公钥和ID

**Certificate Revocation List (CRL)**

证书撤消列表，由CA产生

**Certification Practice Statement (CPS)**

证书使用声明，描述了一个CA的结构和处理过程

### CA的类型

**Root CA**

处于PKI里CA的根结点层次，也叫根CA，只生成CA认证（证书）

**Intermediate CA**

处于根CA和签发CA中间的层次，只生成CA认证（证书）

**Signing CA**

签发CA，处于PKI CA的最底层，只生成用户认证（证书）

### 证书类型

**CA Certificate**

一个CA的证书。用于签发证收和CRL

**Root Certificate**

根证书，处于PKI的根结点上，是自签发的。是PKI的可信网络

**Cross Certificate**

主要用于连接两个PKI，一般成对出现。

**User Certificate**

终端用户的证书，主要用于邮件保护，服务器认证，客户端认证。 它不能够签发别的的证书。

### 文件格式

**Privacy Enhanced Mail (PEM)**

文本格式，base-64编码的数据，with header and footer line. OpenSSL优选使用的格式

**Distinguished Encoding Rules (DER)**

二进制格式，主要在windows环境中使用，同时也是网上证书和CRL下载的官方格式

