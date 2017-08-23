---
layout: post
title: "PostgreSQL之元组结构"
date: 2017-08-23
category: 数据库
keywords: PostgreSQL, 元组, tuple struct
---

在页结构讲完之后，理所当然需要说明的就是元组的结构。主要以堆元组的结构为主，索引元组的结构也并无差异，区别主要在于元组头的信息结构，列结构则大同小异。上图一目了然，如下：

![](/assets/2017/pg_tuple_struct.png)

一个完整的元组主要由两大部分构成，元组头和列数据；其中，元组头部分是保证8字节对齐的，列数据部分也会填充相应的padding数据来保证这一点，所以整个完整的元组也是8字节对齐的。其实，在说到列数据的部分，是必定绕不开数据类型以及其元信息的（包括类型OID、对齐字节数目、字符串类型，等等）；这一部分的信息也会在其中进行必要的说明。

## 元组头

如上图所示，元组头部分也应该分为两个部分， 前一部分是固定长度部分，后一部分是变长部分；二者总长度还需要是8字节的倍数。所谓固定与变长，也其实是相对是否可以直接使用结构体这种方式决定来说的。

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

	uint8		t_hoff;			/* sizeof header incl. bitmap, padding */

	/* ^ - 23 bytes - ^ */

	bits8		t_bits[FLEXIBLE_ARRAY_MEMBER];	/* bitmap of NULLs */

	/* MORE DATA FOLLOWS AT END OF STRUCT */
};
```

在如上所表述的元组头结构体中，t\_hoff在内之前的所有结构属于固定部分； t\_bits开始则属于变长的部分。

变长部分的长度由表定义中列的数目来决定，它记录了各个列对应值是否为null的关键信息； 当然，如果所有列都不存在null值的话，这一变长部分是不存在的，这一关键的信息会直接记录在固定部分的t\_infomask中（不存在HEAP_HASNULL标识）。 如果有一个列的数值是null的话，标识HEAP\_HASNULL就会存在， 那么这个变长部分就要存在，并且需要存储所有列的对应值是否为null，一个bit一个列，直接相当于是一个bitmap。其实这一部分还会存储一个系统字段， 就是OID列； 如果表定义中指定了其元组是需要OID系统列的话，最后的4个字节会用来存储该元组的一个OID数值。

t\_hoff记录了整个元组头的字节数，包括了null bitmap和padding部分；当然也包括了系统列OID所占的空间。

t\_infomask是一个比较重要的成员，它存储了相当重要的一些标识；这些标识主要包括两类标识：列数据存储方面的； 元组事务信息方面的。

  1. 列数据属性方面的主要有4个： 是否有空值，与null直接相关； 是否有变长列，直接与数据类型相关（定长数据类型和变长数据类型）； 是否有外线存储（外线存储的部分再讲）；该元组是否有自己的OID系统列的数值。
  2. 元组事务信息方面的，主要也是有6个：插入事务xid是否已提交; 插入事务xid是否无效； 删除事务xid是否已提交； 删除事务xid是否无效；该元组是否locked；该元组是否为一个更新后的元组。

t\_infomask2这一部分主要存储了两部分信息：一部分是该元组中的实际列的数目； 另一部分是重要的标识信息。第一部分占用了11个bit，也就是说最大可存储2047，实际上支持的列的最大列数目为1600。另一部分是两个重要的标识，与HOT技术相关。当发生hot update的时候，旧元组会被打上HEAP\_HOT_\UPDATED的标识，而新元组则会被打上HEAP\_ONLY\_TUPLE的标识，以标明二者是HOT关联起来的两个版本的元组。

t\_ctid这个部分则直接与元组的更新链是相关的。旧版本元组里这个字段存储了新元组的位置，它相当于一个指针的作用；当这个字段的实际数值与元组自身的位置是相等的时候，表明了它是更新链上的最后一个元组，表明了更新链的终结。需要注意的是，正常的普通更新链是可以跨越页的，而HOT是不跨越页、不同版本的元组是位于相同的页的。也正是这一点，导致了redirected item的存在。

结构体的第一个成员是一个联合体，最常见的是HeapTupleFields这部分的信息。它主要包括了三个成员信息：xmin, 插入事务的xid； xmax， 删除事务的xid； cid， 执行命令id。前两者要好理解一些，对于cid是与执行单条sql语句中、执行过程中不同的command相关的，每当执行一次command id ++时，就会有一个进入一个新的command中。

## 数据类型

## 列数据部分

## form tuple

## deform tuple