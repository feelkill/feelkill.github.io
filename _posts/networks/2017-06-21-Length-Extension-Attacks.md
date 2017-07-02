---
layout: post
title: "长度扩展攻击"
date: 2017-06-21
category: 网络
keywords: 加密, 解密, 网络安全, length extension attacks
---

## 引子

我在看openssl padding的问题时，在Wiki上发现了关于长度扩展攻击的说明；网上查找文章，发现了这一篇文章描述了长度扩展攻击的细节，我阅读了好几次才算理解了，所以按照自己的理解方法把这篇文章重新规整了一下。此文不是我的原创，只是拿来适当地补充和重新组合，以易于理解。

## hash与MACs的区别

加密学的不同术语的区别主要是它们的目的不同。

* Integrity, 完整性，接收者如何相信消息是没有被修改过的
* Authentication, 认证，接收者如何相信消息是来自于发送者的

hash主要用来保证数据的完整性，而MAC主要是保证完整性和认证。

hash的输入是消息本身，它不再需要额外的输入。你可以通过hash后的值来检查你接收到的消息数据是否中间被人修改了。

而MAC则还需要一个key作为种子。这样子，可以保证不仅数据本身是没有修改过的，而且保证了是发送者是我们所期望的那个。否则，在不知道key的情况下，就可以有攻击者会使用这个来生成刺探消息了。

## MAC的简单例子

最简单的MAC算法是这样的：服务器把key和message连接到一起，然后用摘要算法如MD5或SHA1取摘要。

例如，假设有一个网站，在用户下载文件之前需验证下载权限。这个网站会用如下的算法产生一个关于文件名的MAC：
```
mac = hash（key + filenmae）
```

最终的下载ULR可能是：
```
http://example.com/download?file=report.pdf&mac=563162c9c71a17367d44c165b84b85ab59d036f9
                                 ^        ^     ^                                      ^
                                  filename      <---------- user_mac ------------------>
```

当用户发起请求要下载一个文件时，将会执行如下过程

```
input: key, filename, user_mac
mac = hash（key + filenmae）
if mac == user_mac:
   then download file;
else
   error report
```

这样，只有当用户没有擅自更改文件名时服务器才会执行下载。实际上，这种生成MAC的方式，给攻击者在文件名后添加自定义字串留下可乘之机。

## 最简单的攻击

哈希摘要算法，如MD5,SHA1, SHA2等，都是基于Merkle–Damgård结构。这类算法有一个很有意思的问题：如果你知道message和MAC，只需再知道key的长度，尽管不知道key的值，也能在message后面添加信息并计算出相应MAC。

> Example: message + padding +extension

继续用上面的例子，对文件下载的功能进行长度扩展攻击：
```
  http://example.com/download?file=report.pdf%80%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%A8/../../../../../../../etc/passwd&amp;mac=ee40aa8ec0cfafb7e2ec4de20943b673968857a5

                                  <-message-><-----------------padding ------------------------------------------------------------------------------------------------------><---- extension --------------->     <----- mac part  value -------------------->
```

### hash函数的工作原理

哈希函数以区块为单位操作数据。比如说，MD5, SHA1, SHA256的区块长度是512 bits 。大多数message的长度不会刚好可以被哈希函数的区块长度整除。这样一来，message就必须被填充(padding)至区块长度的整数倍。比方说，你的原URL（message部分只指report.pdf部分）为:
```
 http://example.com/download?file=report.pdf
```

进行区块填充后的URL文本为:
```
 http://example.com/download?file=report.pdf\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xA8
```

#### 对于padding部分的说明

这一部分需要考虑key部分在内，这个例子中使用的key长度为11字节，而filename的长度为10字节。区块大小为512bit，而message部分的大小为21byte*8=168bit，那么padding部分的长度为344bit，即43byte。上面消息部分后面的部分为padding部分，原文中这部分（即\xyy形式的数据部分）恰好总共有43个。这部分的模式与之前wiki中所述的任何一个都对不上，比较有特征的是两个数字：第一个\x80，这是ISO/IEC 7816-4模式的特征；最后一个字节则是0xA8，值为168，恰好为填充bit的个数。所以，最好的理解方法是，这部分的padding方式应该是已知的、公开的另一种padding方式；这不会对于后面的理解造成大的困惑。

### 算法运行过程
示例中使用SHA1算法，其主要过程如下：

1. 初始值（又叫registers）被设置为这组数：67452301, EFCDAB89, 98BADCFE, 10325476, C3D2E1F0. 
2. 紧接着，填充message，再将其分割为512bits的区块。
3. 算法轮流操作每个区块，进行一系列的计算并更新registers的值。
4. 一旦完成了这些运算，registers里的值就是最终的哈希值。

第三步是一个有意思的步骤，很明显：**上一个区块输出的临时MAC值，再加上下一个512bit的区块数据，输出的MAC值再作为下下一个512bit的区块的输入**。 也就是说，这是一个可迭代的过程，如果我们知道了临时MAC值，然后自己伪造一个假的512bit区块，那么必然能够制造出一个假的MAC值来，用这个伪造的MAC值来欺骗服务器。

### 如何计算extension部分

计算扩展值得第一步是创建一个新的MAC。我们首先对待扩展的值：上例中的‘/../../../../../../../etc/passwd’进行哈希摘要。但是，在进行摘要之前，我们要把registers里的初始值设置为原始message的MAC。你可以将其想象为让SHA1函数从服务器上的函数运行结束的地方继续进行。

攻击者的 MAC = SHA1(extension + padding) <- 覆盖registers初始值

这个攻击有个前提，**在传入服务器的哈希函数时，扩展值必须存在于单独的区块中**。所以我们的第二步，就是计算出一个填充值使得 key + message + padding == 512 bits 的整数倍。在此例中，key是11个字符的长度。因此填充之后的message是这样的：
```
report.pdf\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xA8
```

传送到服务器的填充及扩展之后的message以及新的MAC：

```
http://example.com/download?file=report.pdf%80%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%A8/../../../../../../../etc/passwd&mac=ee40aa8ec0cfafb7e2ec4de20943b673968857a5
```

服务器要进行摘要运算的被攻击者篡改过的message如下：
```
key + message + padding to the next block        <-- 这一部分为真实的数据部分
+ extension + padding to the end of that block   <-- 这一部分是欺骗的数据部分，需要伪造者进行伪造
```

上面这部分的需要伪造的就是extension部分，只要padding方法是已知的公开的，那么伪造者很容易就可以获得欺骗的新MAC值。

服务器算出的哈希值将是ee40aa8ec0cfafb7e2ec4de20943b673968857a5，正好与我们添加扩展字串并覆盖registers初始值所计算出来的一样。这是因为攻击者的哈希计算过程，相当于从服务器计算过程的一半紧接着进行下去。

## 如何进行攻击

为了简单，在这个例子中我透露了密钥长度是11位。在现实攻击环境中，攻击者无法获知密钥长度，需要对其长度进行猜测。只有获得了key的长度信息，才能够自行填充消息数据。

继续之前的例子，假设当MAC验证失败时，这个存在漏洞的网站会返回一个错误信息（HTTP response code 或者response body中的错误消息之类）。当验证成功，但是文件不存在时，也会返回一个错误信息。如果这两个错误信息是不一样的，攻击者就可以计算不同的扩展值，每个对应着不同的密钥长度，然后分别发送给服务器。当服务器返回表明文件不存在的错误信息时，即说明存在长度扩展攻击，攻击者可以随意计算新的扩展值以下载服务器上未经许可的敏感文件。

## 如何防止攻击

解决这个漏洞的办法是使用[HMAC](https://en.wikipedia.org/wiki/HMAC)算法。该算法大概来说是这样 ：MAC = hash(key + hash(key + message))， 而不是简单的对密钥连接message之后的值进行哈希摘要。

具体HMAC的工作原理有些复杂，但你可以有个大概的了解。重点是，由于这种算法进行了双重摘要，密钥不再受本文中的长度扩展攻击影响。HMAC最先是在1996年被发表，之后几乎被添加到每一种编程语言的标准函数库中。

## 参考
1. [科普哈希长度扩展攻击(Hash Length Extension Attacks) ](http://www.freebuf.com/articles/web/31756.html)
2. [Length extension attack](https://en.wikipedia.org/wiki/Length_extension_attack)
