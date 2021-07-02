import netaddr
import sys
import pandas as pd, json, time
import csv, zipfile, os
from zipfile import ZipFile
from io import TextIOWrapper
import geopandas
import matplotlib.pyplot as plt
import re

df = pd.read_csv("ip2location.csv")
global row
row = 0

def main():
    if len(sys.argv) < 2:
        print("usage: main.py <command> args...")
    elif sys.argv[1] == "ip_check":
        ips = sys.argv[2:]
        ip_check(ips)
    elif sys.argv[1] == "sample":
        in_zip = sys.argv[2]
        out_zip = sys.argv[3]
        stride = sys.argv[4]
        t = time.time()
        sample(in_zip, out_zip, stride)
        print(time.time()-t)
    elif sys.argv[1] == "world":
        in_zip = sys.argv[2]
        name = sys.argv[3]
        world(in_zip, name)
    elif sys.argv[1] == "phone":
        in_zip = sys.argv[2]
        phone(in_zip)
    else:
        print("unknown command: "+sys.argv[1])
        
#This part check the ip and sort based on the IP range and determine the location
def ip_check(ip):
    global row
    list_ip = []
    length = len(df)
    
    a = df[["low", "high"]]
    b = a.values

    for i in ip:
        dict_d = {}
        int_ip = int(netaddr.IPAddress(i))
        dict_d["ip"] = i
        dict_d["int_ip"] = int_ip
        time_1 = time.time()
        find = 0
        while(find < length):
            if(row >= length):
                row = 0
            else:
                if b[row][0] <= int_ip and b[row][1] >= int_ip:
                    find = length
                    dict_d["region"] = df.iloc[row]["region"]
                elif b[row][0] >= int_ip:
                    row -= 1
                elif b[row][1] <= int_ip:
                    row += 1
        time_2 = time.time()
        dict_d["ms"] = 1000*(time_2 - time_1)
        list_ip.append(dict_d)
    print(json.dumps(list_ip, indent=1, separators=(',', ':')))
    
    result = []
    for j in list_ip:
        result.append(j["region"])
    return result
    
def sample(in_zip, out_zip, stride):
    with ZipFile(in_zip) as zf:
        with zf.open(in_zip.replace(".zip", ".csv")) as f:
            with open(out_zip.replace(".zip", ".csv"), "w") as f_2:
                reader = csv.reader(TextIOWrapper(f))
                writer_2 = csv.writer(f_2)
                for index, row in enumerate(reader):
                    if (index - 1) % int(stride) == 0 or index == 0:
                        writer_2.writerow(row)
    
            df = pd.read_csv(out_zip.replace(".zip", ".csv"))
            df["sort"] = df['ip'].replace('[a-zA-Z]','0', regex = True) 
            df["sort"] = df["sort"].map(lambda x: int(netaddr.IPAddress(x)))
            df.sort_values(by=["sort", "time"] , ascending=True, inplace = True)
            
            df["region"] = ip_check(df['ip'].replace('[a-zA-Z]','0', regex = True) .tolist())
            del df["sort"]
            
            df.to_csv(out_zip.replace(".zip", ".csv"), index = False)
            with ZipFile(out_zip, "w") as zf_2:
                zf_2.write(out_zip.replace(".zip", ".csv"))

                
def world(in_zip, name):
    world_df = geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres'))
    world_df = world_df[world_df["continent"] != "Antarctica"]
    
    with ZipFile(in_zip) as zf:
        with zf.open(in_zip.replace(".zip", ".csv")) as f:
            df = pd.read_csv(f)
            df["sort"] = df['ip'].replace('[a-zA-Z]','0', regex = True) 
            df["sort"] = df["sort"].map(lambda x: int(netaddr.IPAddress(x)))
            df.sort_values(by=["sort", "time"] , ascending=True, inplace = True)           
            list_region = ip_check(df['ip'].replace('[a-zA-Z]','0', regex = True) .tolist())
            
            list_count = []
            for row in range(len(world_df)):
                list_count.append(list_region.count(world_df.iloc[row]["name"]))
                
            world_df["count"] = list_count

            world_df.plot(figsize=(12, 9), column = "count")
            plt.savefig(fname= name)
    
def phone(in_zip):
    s = ""
    with ZipFile(in_zip) as zf:
        for info in zf.infolist():
            with zf.open(info.filename, 'r') as f:
                #f = TextIOWrapper(f)
                #paths.append(f.read())
                s = "".join((s, str(f.read())))
             
    r = r"(\(?(\d{3})\)?[-\. ]*(\d{3})[-. ](\d{4}))"
    results = re.findall(r,s)
    list_add = []
    for word in results:
        if word[0] not in list_add:
            print(word[0])
            list_add.append(word[0])
  

if __name__ == '__main__':
     main()