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
<center>来自postgresql源码文件htup_detail.h</center><br/>

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

还有一个需要关注的字段是t\_infomask，它是一个辅助的信息，与上面XMIN+XMAX两个信息配合进行对照使用的，主要是目的是为了减少对CLOG文件的读取和访问，减少IO次数。这个字段的主要可用值如下：

```
/*
 * information stored in t_infomask:
 */
#define HEAP_HASNULL			0x0001	/* has null attribute(s) */
#define HEAP_HASVARWIDTH		0x0002	/* has variable-width attribute(s) */
#define HEAP_HASEXTERNAL		0x0004	/* has external stored attribute(s) */
#define HEAP_HASOID				0x0008	/* has an object-id field */
#define HEAP_XMAX_KEYSHR_LOCK	0x0010	/* xmax is a key-shared locker */
#define HEAP_COMBOCID			0x0020	/* t_cid is a combo cid */
#define HEAP_XMAX_EXCL_LOCK		0x0040	/* xmax is exclusive locker */
#define HEAP_XMAX_LOCK_ONLY		0x0080	/* xmax, if valid, is only a locker */

 /* xmax is a shared locker */
#define HEAP_XMAX_SHR_LOCK	(HEAP_XMAX_EXCL_LOCK | HEAP_XMAX_KEYSHR_LOCK)

#define HEAP_LOCK_MASK	(HEAP_XMAX_SHR_LOCK | HEAP_XMAX_EXCL_LOCK | \
						 HEAP_XMAX_KEYSHR_LOCK)
#define HEAP_XMIN_COMMITTED		0x0100	/* t_xmin committed */
#define HEAP_XMIN_INVALID		0x0200	/* t_xmin invalid/aborted */
#define HEAP_XMIN_FROZEN		(HEAP_XMIN_COMMITTED|HEAP_XMIN_INVALID)
#define HEAP_XMAX_COMMITTED		0x0400	/* t_xmax committed */
#define HEAP_XMAX_INVALID		0x0800	/* t_xmax invalid/aborted */
#define HEAP_XMAX_IS_MULTI		0x1000	/* t_xmax is a MultiXactId */
#define HEAP_UPDATED			0x2000	/* this is UPDATEd version of row */
#define HEAP_MOVED_OFF			0x4000	/* moved to another place by pre-9.0
										 * VACUUM FULL; kept for binary
										 * upgrade support */
#define HEAP_MOVED_IN			0x8000	/* moved from another place by pre-9.0
										 * VACUUM FULL; kept for binary
										 * upgrade support */
#define HEAP_MOVED (HEAP_MOVED_OFF | HEAP_MOVED_IN)

#define HEAP_XACT_MASK			0xFFF0	/* visibility-related bits */
```

HEAP\_XACT\_MASK这个表示了在t\_infomask中有多少bit是用于事务信息的，有多少bit是用于其他存储属性的。可以看出，低四位是用于存储属性的，其他的12位是用于事务信息的。其中，最主要的几个位信息为：

* HEAP\_XMIN\_COMMITTED, 表示insert事务已经提交
* HEAP\_XMIN\_INVALID, 表示insert事务已经回滚或者是无效的
* HEAP\_XMAX\_COMMITTED, 表示delete事务已经提交
* HEAP\_XMAX\_INVALID，表示delete事务已经回滚或者是无效的
* HEAP\_UPDATED，表示该元组是update的新版本
* HEAP\_XMIN\_FROZEN, 表示这个元组已经被打上了frozen标识

从上面的这些信息里，也大体可以了解到在每条元组的事务信息区域时，同时存储了插入和删除事务的一些信息，并且对于事务的committed/rollback的状态有一些可用标识。

## 实例

先创建一个测试表：

```
CREATE TABLE test 
(
  id INTEGER,
  value TEXT
);
```

开启一个事务，查询当前事务ID（值为3277），并插入一条数据，xmin为3277，与当前事务ID相等。符合上文所述——插入tuple时记录xmin，记录未被删除时xmax为0

```
postgres=> BEGIN;
BEGIN
postgres=> SELECT TXID_CURRENT();
 txid_current 
--------------
         3277
(1 row)
postgres=> INSERT INTO test VALUES(1, 'a');
INSERT 0 1
postgres=> SELECT *, xmin, xmax, cmin, cmax FROM test;
 id | value | xmin | xmax | cmin | cmax 
----+-------+------+------+------+------
  1 | a     | 3277 |    0 |    0 |    0
(1 row)

```

继续通过一条语句插入2条记录，xmin仍然为当前事务ID，即3277，xmax仍然为0，同时cmin和cmax为1，符合上文所述cmin/cmax在事务内随着所执行的语句递增。虽然此步骤插入了两条数据，但因为是在同一条语句中插入，故其cmin/cmax都为1，在上一条语句的基础上加一。

```
INSERT INTO test VALUES(2, 'b'), (3, 'c');
INSERT 0 2
postgres=> SELECT *, xmin, xmax, cmin, cmax FROM test;
 id | value | xmin | xmax | cmin | cmax 
----+-------+------+------+------+------
  1 | a     | 3277 |    0 |    0 |    0
  2 | b     | 3277 |    0 |    1 |    1
  3 | c     | 3277 |    0 |    1 |    1
(3 rows)

```

将id为1的记录的value字段更新为’d’，其xmin和xmax均未变，而cmin和cmax变为2，在上一条语句的基础之上增加一。此时提交事务。

```
UPDATE test SET value = 'd' WHERE id = 1;
UPDATE 1
postgres=> SELECT *, xmin, xmax, cmin, cmax FROM test;
 id | value | xmin | xmax | cmin | cmax 
----+-------+------+------+------+------
  2 | b     | 3277 |    0 |    1 |    1
  3 | c     | 3277 |    0 |    1 |    1
  1 | d     | 3277 |    0 |    2 |    2
(3 rows)
postgres=> COMMIT;
COMMIT
```

开启一个新事务，通过2条语句分别插入2条id为4和5的tuple。

```
BEGIN;
BEGIN
postgres=> INSERT INTO test VALUES (4, 'x');
INSERT 0 1
postgres=> INSERT INTO test VALUES (5, 'y'); 
INSERT 0 1
postgres=> SELECT *, xmin, xmax, cmin, cmax FROM test;
 id | value | xmin | xmax | cmin | cmax 
----+-------+------+------+------+------
  2 | b     | 3277 |    0 |    1 |    1
  3 | c     | 3277 |    0 |    1 |    1
  1 | d     | 3277 |    0 |    2 |    2
  4 | x     | 3278 |    0 |    0 |    0
  5 | y     | 3278 |    0 |    1 |    1
(5 rows)

```

此时，将id为2的tuple的value更新为’e’，其对应的cmin/cmax被设置为2，且其xmin被设置为当前事务ID，即3278

```
UPDATE test SET value = 'e' WHERE id = 2;
UPDATE 1
postgres=> SELECT *, xmin, xmax, cmin, cmax FROM test;
 id | value | xmin | xmax | cmin | cmax 
----+-------+------+------+------+------
  3 | c     | 3277 |    0 |    1 |    1
  1 | d     | 3277 |    0 |    2 |    2
  4 | x     | 3278 |    0 |    0 |    0
  5 | y     | 3278 |    0 |    1 |    1
  2 | e     | 3278 |    0 |    2 |    2

```

在另外一个窗口中开启一个事务，可以发现id为2的tuple，xin仍然为3277，但其xmax被设置为3278，而cmin和cmax均为2。符合上文所述——若tuple被删除，则xmax被设置为删除tuple的事务的ID。

```
BEGIN;
BEGIN
postgres=> SELECT *, xmin, xmax, cmin, cmax FROM test;
 id | value | xmin | xmax | cmin | cmax 
----+-------+------+------+------+------
  2 | b     | 3277 | 3278 |    2 |    2
  3 | c     | 3277 |    0 |    1 |    1
  1 | d     | 3277 |    0 |    2 |    2
(3 rows)

```
提交旧窗口中的事务后，新旧窗口中看到数据完全一致——id为2的tuple排在了最后，xmin变为3278，xmax为0，cmin/cmax为2。前文定义中，xmin是tuple创建时的事务ID，并没有提及更新的事务ID，但因为PostgreSQL的更新操作并非真正更新数据，而是将旧数据标记为删除，并插入新数据，所以“更新的事务ID”也就是“创建记录的事务ID”。

```
 SELECT *, xmin, xmax, cmin, cmax FROM test;
 id | value | xmin | xmax | cmin | cmax 
----+-------+------+------+------+------
  3 | c     | 3277 |    0 |    1 |    1
  1 | d     | 3277 |    0 |    2 |    2
  4 | x     | 3278 |    0 |    0 |    0
  5 | y     | 3278 |    0 |    1 |    1
  2 | e     | 3278 |    0 |    2 |    2
(5 rows)

```

说到MVCC的话，必然不能够绕过两个概念，一个是snapshot(快照)，一个是事务隔离级别。那么，这三者之间又是一种什么样的关系呢？下面几篇文章将接着这个话题来说，先会说一下快照与事务隔离级别。

## 参考
* [Postgresql的隐藏系统列](http://my.oschina.net/Kenyon/blog/63668) 
* [PostgreSQL Concurrency with MVCC](https://devcenter.heroku.com/articles/postgresql-concurrency)
* [postgresql的MVCC实现](https://my.oschina.net/Kenyon/blog/108850)
* [heap tuple header struct](https://github.com/postgres/postgres/blob/master/src/include/access/htup_details.h)
* [postgresql的MVCC原理](http://www.jasongj.com/sql/mvcc/)