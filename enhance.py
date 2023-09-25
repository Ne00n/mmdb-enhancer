import geoip2.database, ipaddress, netaddr, glob, json, time, sys, os
from mmdb_writer import MMDBWriter
from geopy import distance

print("Loading config.json")
with open('config.json') as f: config = json.load(f)

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

def add(lat,long,resultType):
    export[f"{lat},{long}"].append(sub[ip])
    if not resultType in results: results[resultType] = 0
    results[resultType] += 1

def sta(statsType,value):
    if not value in stats[statsType]: stats[statsType][value] = 0
    stats[statsType][value] +=1

readers = {verifyDB:geoip2.database.Reader(verifyDB),targetDB:geoip2.database.Reader(targetDB)}
results,stats = {"fail":0},{"country":{},"continent":{}}
export = {}
print("Enhancing...")
for ip in ips:
    target,verify = resolve(ip)
    if verify:
        verifyLat,verifyLong = round(verify.location.latitude,2),round(verify.location.longitude,2)
        if not f"{verifyLat},{verifyLong}" in export: export[f"{verifyLat},{verifyLong}"] = []
    if target:
        targetLat,targetLong = round(target.location.latitude,2),round(target.location.longitude,2)
        if not f"{targetLat},{targetLong}" in export: export[f"{targetLat},{targetLong}"] = []
    if verify and target:
        if target.country.iso_code == verify.country.iso_code:
            add(targetLat,targetLong,"country")
            continue
        
        dis = distance.distance((verify.location.latitude,verify.location.longitude), (target.location.latitude,target.location.longitude)).km
        radius = verify.location.accuracy_radius
        if radius < 20: radius = (radius / 2) * 100
        if radius > 20: radius = (radius / 1.5) * 100
        if radius < 10: radius = 10
        print(f"Radius {radius} from latency {verify.location.accuracy_radius}")

        if dis <= radius:
            print(f"Distance: {dis}")
            print(f"Point is inside the {dis} km radius {ip} {target.country.iso_code} vs {verify.country.iso_code}")
            add(targetLat,targetLong,"distance")
        else:
            print(f"Distance: {dis}")
            print(f"Point is outside the {dis} km radius {ip} {target.country.iso_code} vs {verify.country.iso_code}")
            add(verifyLat,verifyLong,"correction")
    elif target and verify is False: add(targetLat,targetLong,"unable")
    elif verify and target is False: add(verifyLat,verifyLong,"match")
    elif ipaddress.ip_address(ip).is_global:
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
print(stats['continent'])
print(stats['country'])