---
layout: post
title: "postgresql之MVCC	"
date: 2017-08-01
category: 数据库
keywords: postgresql, mvcc, 并发控制
---

对postgresql也学习了一段时间了，感觉到更多是要对已学习的知识进行总结和结构化，所以会慢慢地写一些关于数据库方法的文章。

## 背景

并发控制，本质上是读写并发的问题。在这之前，锁应该是最简单的实现并发控制的手段；可以通过共享锁和排他锁来控制对同一个对象的读写访问，它的特点是：**读读共享**，**读写阻塞**，**写写阻塞**。使用锁的一个最大问题是，写阻塞了读，读也会阻塞写；而这个场景在数据库中很常见的。

MVCC全称是Multiversion Concurrency Control(多版本并发控制)的缩写，从字面意义来看，就是为了解决并发控制的问题。 MVCC主要解决的就是上面所述的**写阻塞读、读阻塞写**的问题。使用MVCC之后，写不再阻塞读、读不再阻塞写。多版本概念是针对更新对象来讲的，在数据库中，最直接的更新对象就是元组(tuple)，其实现也就是在元组上增加了相应的多版本信息；当读操作时，可以读取到对应版本的元组；当写操作时，不是对现有元组进行直接更新，而是使用一个拷贝进行。正是这样，实现了对同一个元组对象的多版本管理，从而实现了“写不阻塞读、读不阻塞写”，提高了并发。

## 实现

在不同的数据库里，其存储形式是不一样的，实现方式也不同。在PostgreSQL里，新老版本数据是混在一起的，Oracle和Innodb里是分开存储的，像Oracle有回滚段（UNDO段）。oracle的实现细节需要再了解，这里主要是说postgresql的实现。

与MVCC紧密相关的一个概念是时间（点），这可以由真正的时间值来实现，也可以用一个递增有序的逻辑数值来表示。postgresql中采用了后者，并同时来标识一个事务，即XID。当一个事务开始的时候，Postgres会增加XID值并赋给当前的事务，Postgres也会对系统里的每一个元组附上事务信息，这可以用来判断该行在其他事务中是否可见。

那么，XID在postgresql中是怎么与MVCC挂起钩来着呢？这就要看最主要的insert/update/delete三个操作了； 其中，postgresql对update的实现基本等同于delete+insert的。所以，等同地可以只看一下insert/delete是怎么使用XID的。主要的数据结构涉及两下，如下所详述。

```
typedef struct HeapTupleFields
{
	TransactionId t_xmin;		/* inserting xact ID */
	TransactionId t_xmax;		/* deleting or locking xact ID */

	union
	{
		CommandId	t_cid;		/* inserting or deleting command ID, or both */
		TransactionId t_xvac;	/* old-style VACUUM FULL xact ID */
	}			t_field3;
} HeapTupleFields;
```
<center>来自postgresql源码文件htup_detail.h</center>

当插入一个元组的时候，Postgres存储XID值并叫它 XMIN；这是一个隐藏字段，就专门地存储与insert相关的事务数值，参照上面结构体中的t\_xmin成员。对当前事务来说，每一个XMIN值比当前事务的XID要小、并且该事务是已提交的元组，对于当前事务都是可见的。举个很简单的例子：你可以开启一个事务，假如以begin开始，然后插入几行数据，在Commit之前，这些数据对其他事务来说都是不可见的，直到你做了Commit。一旦我们做了Commit操作(XID会增长)，对其他事务来说已经满足XMIN<XID，所以其他事务就能看到在该事务提交后的东西。获得当前事务的XID值比较简单：SELECT txid_current();

对于DELETE和UPDATE来说，MVCC的机制也是类似的，略有不同的是Postgres在执行DELETE和UPDATE操作时对每一个元组还存储了XMAX这一隐藏列。也是通过这个字段来决定当前的删除或者更新对其他事务来说是否可见。

```
struct HeapTupleHeaderData
{
	union
	{
		HeapTupleFields t_heap;
		DatumTupleFields t_datum;
	}			t_choice;

	ItemPointerData t_ctid;		/* current TID of this or newer tuple (or a
								 * speculative insertion token) */

	/* Fields below here must match MinimalTupleData! */

	uint16		t_infomask2;	/* number of attributes + various flags */

	uint16		t_infomask;		/* various flag bits, see below */
	
	-------------  只需要关注以上的结构成员即可  -------------------------

	uint8		t_hoff;			/* sizeof header incl. bitmap, padding */

	/* ^ - 23 bytes - ^ */

	bits8		t_bits[FLEXIBLE_ARRAY_MEMBER];	/* bitmap of NULLs */

	/* MORE DATA FOLLOWS AT END OF STRUCT */
};
```

对于update操作，各个版本的元组是怎么样的联系起来的呢？ 这是由上面结构中的t\_ctid这个存储字段进行链接起来的，它就相当于链表中的指针作用一样。它的指向是从更旧版本的元组指向更新版本的元组；当这个值正好指向是自身的位置时，那么就表明已经遍历到了链的最后一个元组上了。

还有一个需要关注的字段是t\_infomask，它是一个辅助的信息，与上面XMIN+XMAX两个信息配合进行对照使用的，主要是目的是为了减少对CLOG文件的读取和访问，减少IO次数。

## 参考
* [Postgresql的隐藏系统列](http://my.oschina.net/Kenyon/blog/63668) 
* [PostgreSQL Concurrency with MVCC](https://devcenter.heroku.com/articles/postgresql-concurrency)
* [postgresql的MVCC实现](https://my.oschina.net/Kenyon/blog/108850)
* [heap tuple header struct](https://github.com/postgres/postgres/blob/master/src/include/access/htup_details.h)