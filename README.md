# mmdb-enhancer
mmdb-enhancer

![data mining](https://thumbs.gfycat.com/HopefulNarrowJuliabutterfly-size_restricted.gif)


## Prepare<br />
```
pip3 install pyasn netaddr
pip install -U git+https://github.com/Ne00n/MaxMind-DB-Writer-python
pyasn_util_download.py --latest && pyasn_util_convert.py --single rib.202* asn.dat
```
## Howto<br />
1. Grab geo.mmdb from yammdb
```
cd db
wget https://yammdb.serv.app/geo.mmdb 
```

2. Grab any .mmdb you want to enhance.
```
wget .....
```

3. Enhance
```
python3 enhance.py
```