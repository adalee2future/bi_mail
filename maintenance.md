# 邮件报表运维

假设系统发件人为data-report@abc.com  

## 项目地址

### 邮件报表系统

`bi_mail`

### 邮件报表配置

`reports`

配置通常有两个文件，一个是cfg，格式为json，需要保证json合法，验证json合法可以在<https://jsonlint.com/>验证，具体有哪些关键字，可以看项目`reports`里的README文档；另一个是sql，SQL文件

## 登录服务器

登录邮件报表系统所在服务器

## 调度


邮件报表使用crontab来调度，其中有个重要脚本`run_by_mail_cmd.sh`，每天0点执行，23:50分停止，该脚本的任务是拉取代码和解析报表负责人发给<data-report@abc.com>的邮件，用来手动运行脚本，所以要保证该脚本正在运行，才可以支持自动拉取代码和报表负责人手动运行脚本，该脚本每天运行情况都会放在`log/YYYY-MM-DD.log`文件里

crontab已经设置，为

```
0 0 * * * ~/projects/bi_mail/run_by_mail_cmd.sh
```

该脚本的运行日志在`log/%Y-%m-%d_%H%M%S.log`里，即以脚本启动时间为文件名，如`log/2018-10-19_000001.log`  
如果该脚本挂掉，或者卡死，需要先把该脚本的进程杀死，然后再执行

```
ps aux | grep run_by_mail_cmd.py | grep python #找到所有进程
kill -9 进程id #杀死进程
nohup ~/projects/bi_mail/run_by_mail_cmd.sh & #启动进程
```


### 具体某个报表调度任务crontab设置如下

```
40 0 * * * ~/projects/bi_mail/run.sh 货架明细
0 15 * * * ~/projects/bi_mail/run.sh '门店应解款(门店提醒)'
0 7 * * * ~/projects/bi_mail/run.sh 营销日报 'to=ada.li@abc.com'
```

第一个表示每天0点40分跑报表<货架明细>，第二个表示每天15点跑报表<门店应解款(门店提醒)>，如果有特殊符号，需要在前后加单引号

crontab的语法可以参考<https://crontab.guru/>

### 在服务器运行某个报表，如

```
~/projects/bi_mail/run.sh '营销日报'
~/projects/bi_mail/run.sh '营销日报' 'pt=20180301'
~/projects/bi_mail/run.sh '营销日报' 'pt=20180301;to=ada.li@abc.com,amy.zhang@abc.com'
```

报表的运行日志存在报表文件夹的log文件夹里，如<营销日报>的运行日志放在<营销日报/log>文件夹下  

### 强制终止某个报表的运行

```
ps aux | grep send_report.py | grep 营销日报  # 找到报表对应的进程id
kill -9 进程id # 杀死该进程
```

## 常见报错

1\. json.decoder.JSONDecodeError

cfg配置json不合法，请把cfg内容复制到<https://jsonlint.com/>，看哪里错了

2\. Exception: NoData Error

无数据报错，默认是任何一个查询语句返回条数为0的时候报错，通常是数据没有准备好，
如果需要更改默认行为，参考README中`no_data_handler`配置

3\. odps.errors.ODPSError 

Odps SQL报错，请看报错日志最后一行具体错误

4\. odps.errors.NoSuchTable

Odps报错，表不存在，具体哪个表请看日志最后一行，注意所有的表名都要写库名

5\. odps.errors.ODPSError: 504: {
       "ErrorCode":"GatewayTimeout",
       "ErrorMessage":"504 Gateway Timeout"
}

odps报错，阿里云odps服务器异常，重跑报表即可


6\. KeyError: 'bdp'

不认识`${bdp.system.bizdate}`，请用`{pt}`代替

7\. Exception: wait for <table_name> too long (361 minutes)

该表配了依赖关系，等待6小时还未准备好，因此报错，请看这个表当天的调度请看，把该表昨日的数据准备好后，重跑报表即可

8\. pymysql.err.OperationalError: (1142, "SELECT command denied to user 'p\_ada'")

MySQL报错，p_ada无SELECT权限，需要添加表的读权限

9\. pymysql.err.InternalError: (1046, 'No database selected')

MySQL报错，表名前面没有带库名

10\. smtplib.SMTPAuthenticationError: (421, b'4.3.2 Service not active)

outlook服务器未运行，重跑报表即可

11\. smtplib.SMTPAuthenticationError: (451, b'4.7.0 Temporary server error. Please try again later)

outlook服务器报错，重跑报表即可

12\. smtplib.SMTPServerDisconnected: Server not connected

outlook服务器报错，无法连接到服务器，重跑报表即可

13\. oss2.exceptions.ServerError

阿里云oss服务器问题，重跑报表即可

14\. ./send_report.sh 已杀死

进程卡死，可能是网络问题，如连接数据库太久没反应、网络不好导致下载数据花费时间太长、邮箱登不上outlook服务器，也有可能是被管理员强制终止。  

解决办法：重跑报表即可
