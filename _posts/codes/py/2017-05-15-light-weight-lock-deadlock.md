---
layout: post
title: "自己平时用于改进的一些脚本"
date: 2017-05-15
category: 代码片断
keywords: postgresql, deadlock, lightlock, python
---

1. 用于检测postgres轻量级锁的死锁问题 ==> [Download](/pieces_of_codes/light_weight_lock_deadlock.py3)
2. 将文件中所有行末尾的最后一个字符删除掉
``` shell
sed -i 's/.$//' test_file
```
