import requests
import string
import json
import config
import dns.resolver

def verify_domain(domain):
    try:
        resolver = dns.resolver.Resolver()
        resolver.lifetime = 10
        answer = resolver.resolve(domain, 'CNAME')
        for rdata in answer:
            cname = str(rdata.target)
            if config.verification_cname in cname:
                return True
        return False
    except Exception as e:
        print(e)
        return False

url = "https://api.neoprotect.net/v2"
headers = {"Authorization": f"Bearer {config.api_key}"}

def get_shields_ids():
    LIST = []
    get_shields_ids = requests.get(f"{url}/gameshields", headers=headers).text
    for i in json.loads(get_shields_ids):
        LIST.append(i["id"])
    return LIST

def create_backend_group(serverId: str, name: str, loadBalanceType: str, proxyProtocol: bool, bedrock: bool, region: str):
    if loadBalanceType.strip().lower() == "random":
        loadBalanceType = "RANDOM"
    if region.strip().lower() == "japan":
        regionId = 5
    payload = {
        "name": name,
        "loadBalanceType": loadBalanceType,
        "proxyProtocol": proxyProtocol,
        "bedrock": bedrock,
        "regionId": regionId
    }
    create_backend_group = requests.post(f"{url}/gameshields/{serverId}/backendGroups", headers=headers, json=payload)
    return create_backend_group.text, create_backend_group.status_code
    
    # group_id 호출법: print(json.loads(create_backend_group(get_shields_ids()[0], "mc-sv", "Random", False, False, "Japan")[0])["id"])

def get_backends(serverId: str):
    get_backends = requests.get(f"{url}/gameshields/{serverId}/backendGroups", headers=headers).text
    return get_backends

def create_backend(serverId: str, groupId: str, host: str, port: int):
    payload = {
        "host": host,
        "port": port
    }
    create_backend = requests.post(f"{url}/gameshields/{serverId}/backendGroups/{groupId}/backends", headers=headers, json=payload)
    return create_backend.status_code

def delete_backend_group(serverId: str, groupId: str):
    delete_backend_group = requests.delete(f"{url}/gameshields/{serverId}/backendGroups/{groupId}", headers=headers)
    return delete_backend_group.status_code

def create_domain(serverId: str, domain: str):
    payload = {
        "domain": domain
    }
    create_domain = requests.post(f"{url}/gameshields/domains/{serverId}", headers=headers, json=payload)
    return create_domain.status_code

def set_backend_to_domain(domain, groupId):
    set_backend_to_domain = requests.post(f"{url}/gameshields/domains/{domain}/backendGroups/{groupId}", headers=headers)
    return set_backend_to_domain.status_code

def delete_domain(domain):
    delete_domain = requests.delete(f"{url}/gameshields/domains/{domain}", headers=headers)
    return delete_domain.status_code

# 백엔드 서버 하나 만드는 코드: print(create_backend(get_shields_ids()[0], json.loads(create_backend_group(get_shields_ids()[0], "mc-sv", "Random", False, False, "Japan")[0])["id"], "dedicated.alcl.cloud", 10012))

# groupId = json.loads(create_backend_group(get_shields_ids()[0], "j-network", "Random", False, False, "Japan")[0])
# print(create_backend(get_shields_ids()[0], groupId["id"], "14.33.45.212", 25565))
# print(create_domain(get_shields_ids()[0], "j-network.mc-sv.kr"))
# print(set_backend_to_domain("j-network.mc-sv.kr", groupId["id"]))

# print(get_backends(get_shields_ids()[0]))
# delete_backend_group(get_shields_ids()[0], "bca4f7de-a1f0-495d-880a-1575a44484c8")
# delete_domain("mc-sv.nrx.kr")
