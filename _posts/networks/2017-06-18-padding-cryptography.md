---
layout: post
title: "加解密中的padding"
date: 2017-06-18
category: 网络
keywords: 加密, 解密, 网络安全, padding, PKCS7
---

## 为什么要padding？

好多现有的加密算法都是块加密算法。它们要求输入的明文是块的整数倍,比方说128bit为一个块大小。但是，很明显地，用户输入的数据并不能够保证恰好是算法块的倍数。所以，才会在最后一部分数据的部分增加padding，以填充完整使得输入要进行加密的数据成为要求块的倍数。

## bit padding

位填充适用于任何大小的消息。

位填充的做法是，在消息部分的最后添加一个1和正数个0。0个数取决于算法要求的块的边界。比方说，块大小为32bit，而现有消息是23bit，那么就需要再增加9bit，即一个1，8个0.

> ... | 1011 1001 1101 0100 0010 011**1 0000 0000** |

有的采用了两步padding，它们一般会把位填充方法作为第一个填充方法来使用，像MD5和SHA1。而 ISO/IEC 9797-1则把它定义为了第二种填充方案（Padding Method 2）来使用。

## ANSI X.923

是一种字节填充方式，首先填充整数个0作为前缀，最后一个字节是填充字节的数目。

比方，块大小为8字节，最后需要填充4个字节，那么填充的样例如下：

> ... | DD DD DD DD DD DD DD DD | DD DD DD DD **00 00 00 04** |

## ISO 10126

对最后一个块进行填充随机的字节，最后一个字节来表示总共填充了多少个有字节。

比方，块大小为8字节，填充了4个字节，那么最后一个字节为04,前面为随机填充的字节数值。

> ... | DD DD DD DD DD DD DD DD | DD DD DD DD **81 A6 23 04** |

## PKCS7

```
01
02 02
03 03 03
04 04 04 04
05 05 05 05 05
06 06 06 06 06 06
etc.
```

填充样式为上面的某行之一。该填充模式是在 RFC 5652进行描述的。其特征是，需要填充多少个字节，就使用该数值的重复值。

比方， 块大小为8字节，需要填充的字节数目为4，那么就填充4个04

> ... | DD DD DD DD DD DD DD DD | DD DD DD DD **04 04 04 04** |

## ISO/IEC 7816-4

ISO/IEC 7816-4:2005 方案等同于位填充方式，只是进行了字节填充。在实际中，第一个字节是一个强制的字节0x80，后续的所有数值全部是 0x00（如果有存在的必要的话）。

比方，块大小为8字节，需要填充4个字节，那么样例为

> ... | DD DD DD DD DD DD DD DD | DD DD DD DD **80 00 00 00** |

如果需要填充1个字节，那么样例为

> ... | DD DD DD DD DD DD DD DD | DD DD DD DD DD DD DD **80** |

## Zero padding

零填充则很简单，直接对所有需要填充的字节以0x00进行填充。 只是这种方案不是加密算法的标准方案，但它也在哈希和MAC中作为填充方案使用。

比方，块大小为8字节，需要进行4字节填充，那么

> ... | DD DD DD DD DD DD DD DD | DD DD DD DD **00 00 00 00** |

## 参考
* [cryptography padding](https://en.wikipedia.org/wiki/Padding_(cryptography))
* [浅谈这次ASP.NET的Padding Oracle Attack相关内容](http://www.cnblogs.com/JeffreyZhao/archive/2010/09/25/things-about-padding-oracle-vulnerability-in-asp-net.html)
* [科普哈希长度扩展攻击(Hash Length Extension Attacks)](http://www.freebuf.com/articles/web/31756.html)
* [Length extension attack](https://en.wikipedia.org/wiki/Length_extension_attack)
