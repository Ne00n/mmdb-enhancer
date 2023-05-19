import geoip2.database, ipaddress, netaddr, glob, json, sys, os
from mmdb_writer import MMDBWriter

def getDB(operation="verification"):
    print(f"Please select db for {operation}")
    dbs = glob.glob("db/*.mmdb")
    for index, db in enumerate(dbs):
        print(f"[{index}] {db}")
    targetDB = input('Please enter number: ')
    for index, db in enumerate(dbs):
        if int(targetDB) == index: 
            return dbs[index]

def networkToSubs(subnet):
    sub, prefix = subnet.split("/")
    if int(prefix) > (int(scope) -1): return [subnet]
    network = netaddr.IPNetwork(subnet)
    return [str(sn) for sn in network.subnet(int(scope))]

verifyDB = getDB()
print(f"Selected {verifyDB}")
targetDB = getDB("modification")
print(f"Selected {targetDB}")
print("Please select scope")
print(f"[0] Dynamic (default)")
print(f"[23] /23")
print(f"[22] /22")
print(f"[21] /21")
print(f"[20] /20")
scope = input('Please enter number: ')

ips,sub = [],{}
print("Building Query list")
with open('asn.dat') as file:
    for line in file:
        if ";" in line: continue
        line = line.rstrip()
        prefix, asn = line.split("\t")
        if int(scope) == 0:
            ips.append(prefix.split("/")[0])
            sub[prefix.split("/")[0]] = prefix
        else:
            subs = networkToSubs(prefix)
            for subnet in subs: 
                ip = subnet.split("/")[0]
                ips.append(ip)
                sub[ip] = subnet

def resolve(ip):
    try:    
        target = readers[targetDB].city(ip)
    except:
        target = False
    try:
        verify = readers[verifyDB].city(ip)
    except:
        verify = False
    return target,verify

readers = {verifyDB:geoip2.database.Reader(verifyDB),targetDB:geoip2.database.Reader(targetDB)}
results,stats = {"match":0,"correction":0,"fail":0,"unable":0,"scope":0},{}
export = {}
print("Enhancing...")
for ip in ips:
    target,verify = resolve(ip)
    if target and not f"{round(target.location.latitude,2)},{round(target.location.longitude,2)}" in export: export[f"{round(target.location.latitude,2)},{round(target.location.longitude,2)}"] = []
    if verify and not f"{round(verify.location.latitude,2)},{round(verify.location.longitude,2)}" in export: export[f"{round(verify.location.latitude,2)},{round(verify.location.longitude,2)}"] = []
    if target and verify:
        if not target.continent.code in ["OC","AN"]:
            if target.continent.code == verify.continent.code:
                results["match"] += 1
                export[f"{round(target.location.latitude,2)},{round(target.location.longitude,2)}"].append(sub[ip])
            elif verify.location.accuracy_radius and verify.location.accuracy_radius < 150:
                if not target.continent.code in stats: stats[target.continent.code] = 0
                stats[target.continent.code] +=1
                results["correction"] += 1
                print(f"Corrected {target.continent.code} to {verify.continent.code} ({ip}, {verify.location.accuracy_radius})")
                export[f"{round(verify.location.latitude,2)},{round(verify.location.longitude,2)}"].append(sub[ip])
            else:
                export[f"{round(target.location.latitude,2)},{round(target.location.longitude,2)}"].append(sub[ip])
                results["scope"] += 1
        else:
            export[f"{round(target.location.latitude,2)},{round(target.location.longitude,2)}"].append(sub[ip])
            results["scope"] += 1
    elif target and verify is False:
        export[f"{round(target.location.latitude,2)},{round(target.location.longitude,2)}"].append(sub[ip])
        results["unable"] += 1
    elif verify and target is False:
        export[f"{round(verify.location.latitude,2)},{round(verify.location.longitude,2)}"].append(sub[ip])
        results["match"] += 1
    else:
        if ipaddress.ip_address(ip).is_global:
            print(f"Failed to resolve {ip}")
            results["fail"] += 1

print("Building enhanced.mmdb")
writer = MMDBWriter(4, 'GeoIP2-City', languages=['EN'], description="enhanced.mmdb")
for location,subnets in export.items():
    location = location.split(",")
    writer.insert_network(netaddr.IPSet(subnets), {'location':{"latitude":float(location[0]),"longitude":float(location[1])}})
print("Writing enhanced.mmdb")
writer.to_db_file('enhanced.mmdb')
print(results)
print(stats)