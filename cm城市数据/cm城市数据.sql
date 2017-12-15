select day_id,aa.machine_id,serial_number,customer_id,city,corp_name,
coalesce(order_num,0) as order_num,coalesce(order_amount,0) as order_amount from 
(select a.day_id,coalesce(a.id,b.machine_id) as machine_id,a.serial_number,b.customer_id,c.city,corp_name from 
owo_ods.kylin__machine_release_his  a
full join
owo_ods.kylin__hj_rack_customermapping b 
on a.id=b.machine_id
left join owo_ods.kylin__address_cities c
on a.city_id=c.cityid
left join owo_ods.kylin_customer__ls_customer_customer d 
on b.customer_id=d.id
left join owo_ods.kylin__machine_device e
on a.machine_device_id=e.id
where a.release_status in (2,3) and day_id<=20171211 and day_id>=20171202 and c.city!='阿拉善盟'and type in(10,20))aa
left join 
(select 
substr(pay_complete_time,1,10)as pay_complete_time,
machine_id,count(view_id)as order_num,sum(actual_amount)as order_amount
from 
rack.dw_order 
where substr(pay_complete_time,1,10)<='{pt}'
and substr(pay_complete_time,1,10)>=substr(dateadd(to_date('{pt}','yyyy-mm-dd'),-6,'dd'),1,10)
and pay_status=64
group by substr(pay_complete_time,1,10),machine_id)bb
on aa.day_id=replace(bb.pay_complete_time,'-','') and aa.machine_id=bb.machine_id