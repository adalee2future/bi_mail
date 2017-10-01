
# coding: utf-8

# In[76]:

from odps import ODPS
import os
import pandas as pd
import time

workspace = 'kylin'
project_id = 'machine_release_detail'
sql_filename = '%s.sel.sql' % project_id
odps = ODPS(os.environ['access_id'], os.environ['access_key'], 'kylin')
odps.get_project()


# In[80]:

with open(sql_filename) as f:
    sql_text = f.read()
print(sql_text)

sql_res = odps.run_sql(sql_text)

time.sleep(10)


# In[81]:

with sql_res.open_reader() as reader:
    sql_res_dataframe = reader.to_pandas()
    
sql_res_dataframe.head()


# In[82]:

sql_res_dataframe.to_excel("%s.xlsx" % project_id, index=False)
print("data frame writen.")


# In[ ]:



