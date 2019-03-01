# Block Device Settings, aka "Readahead" for MongoDB
### Jason Fowler, Technical Services Engineer

## What is `readahead` ?

`Readahead` is a setting on a block device (usually a storage device like a harddrive or NAS) that controls how much data is fetched whenever a read from that block device happens. Disk seeks on spinning disks are very expensive, but accessing sequential blocks of data is relatively cheap. Since many applications tend to access data sequentially, it makes sense that if you're going to pay the cost to do a disk seek to read in data, you should try to read some extra data after.

We (MongoDB Technical Services) have observed that using 256 blocks `readahead` on filesystems hosting both the database and backups, the snapshot creation speed improved.

If `readahead` is set too high MongoDB won't be able to use all the RAM available on the machine effectively. This is because each disk read will be pulling a lot of extra data which will take up room in memory, but will never be accessed before being paged out to make room for data read in by another read operation.  Please see below for more information on setting `readahead` for MongoDB.

## How do I know how to find `readhead` settings?

### Linux commands to **find** `readahead` for device:

To list all devices, type `sudo blockdev --report`

(The following assumes `/dev/sda` as the block device.)

### BLOCKDEV
`sudo blockdev --getra /dev/sda`

### UDEVADM
`sudo udevadm info -a -p /sys/block/sda`

### HDPARM
`sudo hdparm -a /dev/sda`

### TUNED
### Red Hat/Centos
The [tuned tool](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/performance_tuning_guide/chap-red_hat_enterprise_linux-performance_tuning_guide-tuned_) is typically included in Red Hat and derivatives, eg Centos/Amazon Linux
"Tuned is a daemon that uses udev to monitor connected devices and statically and dynamically tunes system settings according to a selected profile."  It is a tool used for much more than just setting disk `readahead` and is provided here for information purposes.

Please see the [documentation](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/performance_tuning_guide/chap-red_hat_enterprise_linux-performance_tuning_guide-storage_and_file_systems) for more information on Red Hat (and derivatives) performance and storage tuning.

##  What do I do when I want to make a change to the `readahead` settings?

While all the above tools are great for finding and setting `readahead` for storage systems, `hdparm` is the easier tool to use (IMHO) on both Red Hat and Debian Linux derivatives.

**Installation**:

`sudo {apt|yum} install hdparm`

### How fast is the disk?
/sudo hdparm -t /dev/sda
dev/sda:
 Timing buffered disk reads: 1496 MB in  3.00 seconds = 498.47 MB/sec

### Linux commands to **set** `readahead` for device:

(The following assumes `/dev/nvme0n1` as the block device.)

- `sudo blockdev --report`

```
RO    RA   SSZ   BSZ   StartSec            Size   Device
rw   256   512  4096          0     64424509440   /dev/nvme0n1
rw   256   512   512       4096     64422395392   /dev/nvme0n1p1
rw   256   512  4096       2048         1048576   /dev/nvme0n1p128
```

- `sudo hdparm -a /dev/nvme0n1`

```
/dev/nvme0n1:
 readahead     = 256 (on)
```
