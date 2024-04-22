#!/usr/bin/env python3.6.3
import UsrIntel.R1
import pandas as pd

class little_obj:
    def __init__(self,x):
        self.my_str = "I am a little obj number "+str(x)+"\n"

class my_obj:
        def __init__(self, x, y):
            self.x, self.y = x, y
            self.list = ['abc','efg']
            self.uri = {"TID" : "TID_0", "LID" :"LID_0" , "PID" : "PID_0"}
            self.objects = [little_obj(1) , little_obj("2a")]

        #Add your objects that you wish to prase into the csv here
        def is_one_of_my_objects(self,obj):
            return isinstance(obj,little_obj)
        def my_dict(self):
            my_dict_a ={}
            for d in self.__dict__:
                var_val = getattr(self,d)
                #the value is a list of or dict of objects

                if (type(var_val) is dict or type(var_val) is list) and self.is_one_of_my_objects((next(iter(var_val)))):
                        for o in range(0,len(var_val)):
                            key_str = d+"_"+str(o)
                            my_dict_a[key_str] = var_val[o].__dict__
                else:
                    my_dict_a[d] = var_val

            return my_dict_a



my_objs = {"one" : my_obj(1,2) , "two" : my_obj(3,4), "three" : my_obj(5,6)}
# fill dataframe with one row per object, one attribute per column
#Dump all values into a df
df = pd.DataFrame([t.my_dict() for t in my_objs.values()])

print("First df")
print(df)

#clean the data up
df["TID"] = ""
df["LID"] = ""
df["PID"] = ""

for i in range(len(df)):
    uri = df.loc[i].uri
    df.at[i,"TID"] = uri["TID"]
    df.at[i,"LID"] = uri["LID"]
    df.at[i,"PID"] = uri["PID"]



df.drop('uri',axis='columns', inplace=True)

print("after cleanup")
print(df)
df.to_csv("my_df.csv")
