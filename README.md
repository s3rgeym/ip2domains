# ip2domains

Scans IP addresses and finds domains

Installation:

```bash
pip install ip2domains
```

Usage:

```bash
# help
ip2domains -h

# scan all internet
echo "0.0.0.0/0" | ip2domains -vvv

# output list unique domains
ip2domains | jq -r '.domains[]' | sort | uniq
```
