select city_name `城市`,
       operator `销售人员`,
       user_realname `方案申请人`,
       user_name `方案申请人id`,
       sso_status `方案申请人在职`,
       scheme_create_date `方案创建时间`,
       corp_name `客户名`,
       machine_name `货架名称`,
       serial_number `货架编号`,
       machine_status `货架状态`,
       settle_date `入驻时间`,
       online_date `货架上线时间`
from ada_machine_release_detail
where pt = '20170915'
;
