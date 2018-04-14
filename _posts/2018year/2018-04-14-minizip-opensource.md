---
layout: post
title: "使用minizip来操作zip文件"
date: 2018-04-14
category: 2018年
keywords: zlib, minizip
---

## minizip简介

minizip可以用来从.zip文件中抽取出文件来。它与[WinZip](http://www.winzip.com/), [InfoZip](http://www.freesoftware.com/pub/infozip/), [PKZip](http://www.pkware.com/)是相兼容的。

与此相关的是zlib，这也是一个开源库，用来压缩和解压数据和文件的。.gz文件就是使用zlib可以创建的，一般来说，.gz文件中通常只包含一个文件，并且会使用zlib进行压缩处理。相反地，ZIP归档文件中通常则包含多个文件，并且会使用zlib进行压缩。

minizip的源码放置在zlib开源库包中，是在contrib/minizip目录下面。里面涉及的文件主要有：

* 压缩打包功能，主要文件zip.c, zip.h, ioapi.c等。除此之外，还有一个文件minizip.c演示了如何使用C接口来操作ZIP，同时它也是一个真正的zip压缩工具。
* 解压功能，主要文件unzip.c, unzip.h, ioapi.c等。除此之外，还有一个文件miniunz.c演示了如何使用C接口来解压.zip文件，同时它也是一个真正的zip解压命令工具。

## 压缩

压缩功能的API主要参考zip.h文件。伪代码如下：

```
// 创建一个zip归档文件
zip_fd = zipOpen64("test.zip")
    foreach 文本文件列表
        // 打开源文件(每一个要写入的文件)
        to_write = open('1.txt')
        // 打开目标文件(位于zip归档中)
        zip_inner_fd = zipOpenNewFileInZip("1.txt")
        // 读取文件中的数据，然后写入到zip中的文件里
        while ( read data into buffer from to_write)
            zipWriteInFileInZip(zip_inner_fd, buffer)
        // 关闭目标文件
        zipCloseFileInZip(zip_inner_fd)
        // 关闭源文件
        close(to_write)
// 关闭zip归档文件
zipClose(zip_fd)

```

可以看出，涉及到的主要API为(以下内容转自[使用Zlib库进行文件的压缩和解压](https://www.jianshu.com/p/cca8e5c858fc))

* zipOpen64
* zipClose
* zipOpenNewFileInZip
* zipCloseFileInZip
* zipWriteInFileInZip

使用 zipOpen64 来打开/创建一个 ZIP 文件，然后开始遍历要被放到压缩包中去的文件。针对每个文件，先调用一次 zipOpenNewFileInZip，然后开始读原始文件数据，使用 zipWriteInFileInZip 来写入到 ZIP 文件中去。zipOpenNewFileInZip 的第三个参数是一个 zip_fileinfo 结构，该结构数据可全部置零，其中 dosDate 可用于填入一个时间（LastModificationTime）。它的第二个参数是 ZIP 中的文件名，若要保持目录结构，该参数中可以保留路径。

## 解压

解压功能的API主要参考unzip.h文件。伪代码如下：

```
// 打开一个zip归档文件
zip_fd = unzOpen64("test.zip")
    // 获得zip归档中的文件数目
    unzGetGlobalInfo64(zip_fd, unz_global_info64)
    // 跳到第一个文件上
    unzGoToFirstFile(zip_fd)
    for (i = 0; i < unz_global_info64.number_entry; ++i)
        // 获得zip归档中的文件名
        unzGetCurrentFileInfo64(zip_fd, filename_in_zip)
        // 打开源文件(位于zip归档中)
        zip_inner_fd = unzOpenCurrentFile()
        // 创建目标文件
        to_write = open()
        // 读取文件中的数据，然后写入到zip中的文件里
        while ( unzReadCurrentFile(zip_inner_fd, buffer, len) )
            write(to_write, buffer, len)
        // 关闭目标文件
        close(to_write)
        // 关闭源文件
        unzCloseCurrentFile(zip_inner_fd)
        // 准备处理下一个文件
        unzGoToNextFile(zip_fd)
// 关闭zip归档文件
unzClose(zip_fd)

```

可以看出，涉及到的主要API为：以下内容转自[使用Zlib库进行文件的压缩和解压](https://www.jianshu.com/p/cca8e5c858fc)

* unzOpen64
* unzClose
* unzGetGlobalInfo64
* unzGoToNextFile
* unzGetCurrentFileInfo64
* unzOpenCurrentFile
* unzCloseCurrentFile
* unzReadCurrentFile

打开一个ZIP文件后，需要先使用unzGetGlobalInfo64来取得该文件的一些信息，来了解这个压缩包里一共包含了多少个文件，等等。目前我们用得着的就是这个文件数目。然后开始遍历ZIP中的文件，初始时自动会定位在第一个文件，以后处理完一个后用unzGoToNextFile来跳到下一个文件。对于每个内部文件，可用unzGetCurrentFileInfo64来查内部文件名。这个文件名和刚才zipOpenNewFileInZip的第二个参数是一样的形式，所以有可能包含路径。也有可能会以路径分隔符（/）结尾，表明这是个目录项（其实压缩操作的时候也可以针对目录写入这样的内部文件，上面没有做）。所以接下来要根据情况创建（多级）目录。unzGetCurrentFileInfo64的第三个参数是unz_file_info64结构，其中也有一项包含了dosDate信息，可以还原文件时间。对于非目录的内部文件，用 unzOpenCurrentFile，打开，然后unzReadCurrentFile读取文件内容，写入到真实文件中。unzReadCurrentFile返回 0 表示文件读取结束。

使用开源库最大的两个问题是：IO可否定制；内存管理可否定制。这对于产品集成来说，是非常重视的事情。下面分别来说明。

## IO定制

minizip的IO是可以定制的，这可以通过iozpi.h头文件中的结构体zlib\_filefunc64_def +   zlib\_filefunc64\_32\_def看出来。简单来说，这个结构体定义了文件IO操作的几个接口，主要如下：

* open64_file_func, 打开文件的函数原型
* read_file_func, 读取文件数据的函数原型
* write_file_func, 写入文件数据的函数原型
* tell64_file_func， 告诉当前fd在文件中偏移量的函数原型
* seek64_file_func, 对文件进行seek定位到指定偏移量的函数原型
* close_file_func, 关闭文件的函数原型
* testerror_file_func, 当文件IO错误时，用于返回文件错误信息的函数原型

这些接口都比较好理解，IO定制的时候需要全部实现。

## 内存管理定制

minizip的内存并没有像IO那样预留好接口，需要修改代码才能实现这样的接口。在unzip.c文件中有如下的代码：

```
#ifndef ALLOC
# define ALLOC(size) (malloc(size))
#endif
#ifndef TRYFREE
# define TRYFREE(p) {if (p) free(p);}
#endif
```

这也正说明了，如果要进行内存管理定制化的话，需要重新定义ALLOC和TRYFREE两个宏，并且需要进行源码及的个性。还好，minizip的license是比较友好的，是可以进行源码修改的。至于修改的方法，可以参考IO定制的方法进行即可。


## 参考文档
* [Minizip: Zip and UnZip additionnal library](http://www.winimage.com/zLibDll/minizip.html)
* [zlib opensource](https://www.zlib.net)
* [使用Zlib库进行文件的压缩和解压](https://www.jianshu.com/p/cca8e5c858fc)