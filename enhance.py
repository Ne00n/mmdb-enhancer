from netaddr import IPNetwork, IPSet
from mmdb_writer import MMDBWriter
import geoip2.database, glob, sys

verifyDB = "db/geo.mmdb"
print(f"Using {verifyDB} for verfication")
print(f"Please select db for modification")
dbs = glob.glob("db/*.mmdb")
for index, db in enumerate(dbs):
    print(f"[{index}] {db}")
targetDB = input('Please enter number: ')
for index, db in enumerate(dbs):
    if int(targetDB) == index: 
        targetDB = dbs[index]
        break

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

readers = {verifyDB:geoip2.database.Reader(verifyDB),targetDB:geoip2.database.Reader(targetDB)}
results = {"match":0,"correction":0,"fail":0}
export = {}
for ip in ips:
    try:
        target = readers[targetDB].city(ip)
        verify = readers[verifyDB].city(ip)
        if target.continent.code in ["EU","NA","AS"]:
            if not f"{target.location.latitude},{target.location.longitude}" in export: export[f"{target.location.latitude},{target.location.longitude}"] = []
            if not f"{verify.location.latitude},{verify.location.longitude}" in export: export[f"{verify.location.latitude},{verify.location.longitude}"] = []
            if target.continent.code == verify.continent.code:
                results["match"] += 1
                export[f"{target.location.latitude},{target.location.longitude}"].append(sub[ip])
            else:
                results["correction"] += 1
                export[f"{verify.location.latitude},{verify.location.longitude}"].append(sub[ip])
    except Exception as e:
        results["fail"] += 1
        print(e)
        continue

writer = MMDBWriter(4, 'GeoIP2-City', languages=['EN'], description="Mah own .mmdb")
for location,subnets in export.items():
    location = location.split(",")
    writer.insert_network(IPSet(subnets), {'location':{"latitude":float(location[0]),"longitude":float(location[1])}})
writer.to_db_file('enhance.mmdb')
print(results)