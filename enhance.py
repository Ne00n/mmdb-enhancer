from netaddr import IPNetwork, IPSet
from mmdb_writer import MMDBWriter
import geoip2.database, glob, sys

def getDB(operation="verification"):
    print(f"Please select db for {operation}")
    dbs = glob.glob("db/*.mmdb")
    for index, db in enumerate(dbs):
        print(f"[{index}] {db}")
    targetDB = input('Please enter number: ')
    for index, db in enumerate(dbs):
        if int(targetDB) == index: 
            return dbs[index]

verifyDB = getDB()
print(f"Selected {verifyDB}")
targetDB = getDB("modification")
print(f"Selected {targetDB}")

ips = []
sub = {}
print("Building IP list")
with open('asn.dat') as file:
    for line in file:
        if ";" in line: continue
        line = line.rstrip()
        subnet, asn = line.split("\t")
        ips.append(subnet.split("/")[0])
        sub[subnet.split("/")[0]] = subnet

def resolve(ip):
    try:    
        target = readers[targetDB].city(ip)
    except:
        return False,False
    try:
        verify = readers[verifyDB].city(ip)
    except:
        return target,False
    return target,verify

readers = {verifyDB:geoip2.database.Reader(verifyDB),targetDB:geoip2.database.Reader(targetDB)}
results,stats = {"match":0,"correction":0,"fail":0,"unable":0,"scope":0},{}
export = {}
print("Enhancing...")
for ip in ips:
    target,verify = resolve(ip)
    if target and not f"{target.location.latitude},{target.location.longitude}" in export: export[f"{target.location.latitude},{target.location.longitude}"] = []
    if verify and not f"{verify.location.latitude},{verify.location.longitude}" in export: export[f"{verify.location.latitude},{verify.location.longitude}"] = []
    if target and verify:
        if target.continent.code in ["EU","NA","AS"]:
            if target.continent.code == verify.continent.code:
                results["match"] += 1
                export[f"{target.location.latitude},{target.location.longitude}"].append(sub[ip])
            else:
                if not target.continent.code in stats: stats[target.continent.code] = 0
                stats[target.continent.code] +=1
                results["correction"] += 1
                export[f"{verify.location.latitude},{verify.location.longitude}"].append(sub[ip])
        else:
            export[f"{target.location.latitude},{target.location.longitude}"].append(sub[ip])
            results["scope"] += 1
    elif target and verify is False:
        export[f"{target.location.latitude},{target.location.longitude}"].append(sub[ip])
        results["unable"] += 1
    else:
        results["fail"] += 1

writer = MMDBWriter(4, 'GeoIP2-City', languages=['EN'], description="enhanced.mmdb")
for location,subnets in export.items():
    location = location.split(",")
    writer.insert_network(IPSet(subnets), {'location':{"latitude":float(location[0]),"longitude":float(location[1])}})
print("Writing enhanced.mmdb")
writer.to_db_file('enhanced.mmdb')
print(results)
print(stats)