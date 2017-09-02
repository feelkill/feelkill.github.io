---
layout: post
title: "PostgreSQL之高速缓存"
date: 2017-09-01
category: 数据库
keywords: PostgreSQL, 高速缓存，SysCache, CatCache, RelCache
---

pg的内存部分，本地高速缓存是一个绕不过去的话题。它主要包括了两个部分:Catalog Cache; Relation Cache。理解二者的关键信息有：

* Catalog Cache主要缓存了最近使用过的系统表的元组。
* Relation Cache主要缓存了最近使用过的表的模式（schema信息)，主要包括了表约束、列约束以及列的定义信息等。
* 系统表本身也是有schema的，它的信息也会缓存在relation cache中。
* Relation Cache相关的主要数据结构体是RelationData，这个结构体的信息是从pg\_class、pg\_type、pg\_attribute、pg\_proc、pg\_constraint等这些系统表中的元组抽取出来的、组合而成的表信息；

总体来讲，其实**高速缓存主要是给系统表（数据字典）的数据的快速访问提供了独立的读缓存** 。普通的用户数据则是**使用shared buffer进行读写缓存**的，当然系统表数据（数据字典）的写缓存也是放在shared buffer的。

## Catalog Cache

catcache的**总体思想还是哈希**；它并没有使用通用的哈希表，而是自己**使用链表 + 数组的方式**重新构造了自己独特的哈希表。这个读缓存主要向外提供两个功能：

1. 精确查找；
2. 模糊查找；

单个系统表的catcache中最多有4个查找关键字。当调用者使用4个关键字进行查找时，使用的是精确查找功能，返回的只有一条元组；当调用者使用不到4个关键字进行查找时，使用的是模糊查找功能，返回的可能有多个元组。所知道的范围内，pg\_proc这个系统表对函数的查找是会使用到模糊查找的功能的。

![catalog cache detail](/assets/2017/pg-catalog-cache.png)

这个图给出了从catcache中查找元组的整体过程，它涉及到了catcache实现代码中的所有关键的数据结构。另外，要注意的是还有一个结构体是cachedesc以及它的数组cacheinfo静态数组，

```
/*
 *		struct cachedesc: information defining a single syscache
 */
struct cachedesc
{
	Oid			reloid;			/* OID of the relation being cached */
	Oid			indoid;			/* OID of index relation for this cache */
	int			nkeys;			/* # of keys needed for cache lookup */
	int			key[4];			/* attribute numbers of key attrs */
	int			nbuckets;		/* number of hash buckets for this cache */
};

========= 从cacheinfo静态数组中截取的一个元素 =========

	{AttributeRelationId,		/* ATTNUM */
		AttributeRelidNumIndexId,
		2,
		{
			Anum_pg_attribute_attrelid,
			Anum_pg_attribute_attnum,
			0,
			0
		},
		128
	},
```

可以看到，这个结构体主要给出了catcache中的几个关键要素：表OID； 索引OID； 查询关键字； 以及哈希桶个数。以给出的例子来讲，对系统表 pg_attribute的字段attnum进行了缓存，索引为 AttributeRelidNumIndexId, 查询关键字有2个分别为attrelid和attnum， 哈希桶的数目为128.正是依据这些基本的关键信息来建立起整个哈希表的。

对于上图中的详细介绍，可以参考pg数据库内核分析一书。除此外，还有几个要点是：

1. 当使用精确查找时，直接将图中的HeapTupleData部分的数据返回给了调用者；
2. 当使用模糊查找时，通过CatCList结构返回给调用者，调用者需要依次遍历这个链表；
3. dead的缓存元组并不会马上清除掉，而是要等到它的引用计数为0时才会清除。如果这个缓存元组还位于某个CatCList中的话，还需要等待CatCList的引用计数也为0时，方才会被清除；
4. 负元组的问题。负元组表示，使用某个关键字的查找结果是空，那个元组是不存在于这个系统表内的，所以无法在内存和磁盘上查找得到。为了避免反复在磁盘上去查找这样的元组带来的IO开销，所以将查询过的关键信息记录在了缓存中，并标识为负元组。
5. catalog cache是一个只读缓存，意味着不可以进行写操作。当需要进行写操作的时候，必须使用与普通元组一样的shared buffer的写缓存路径。

## Relation Cache

relcache要相对简单得多，它就是使用了普通的哈希表来管理表模式的。key为表的OID，value为表的模式信息（RelationData)。只要给出表的OID，就可以得到对应的schema信息。很显然的，如果查找不到的话，是会到磁盘上去scan相应的系统表，然后把信息拼起来，填充到哈希表中的，最后再返回给调用者。

## Cache的同步与失效

## 彩蛋

1. 内存上下文相对相简单一些，使用者只需要像malloc/free/remalloc一样调用它的接口就可以了。但是要注意的几个点是
  * 内存上下文是按照树形结构组织的；
  * 处于树节点中的内存上下文进行reset/delete操作是会产生级联效果的，即它对所有的子树是生效的；
  * 遗留了一个问题是：内存上下文怎么使用效率是最高的？能否有一个方法来监测它的使用指标不？