import requests
from urllib.parse import urlparse


#############
# Variables # 
#############
headers_base = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

get_page_url_tpl = "https://{domain}.notion.site/api/v3/getPublicPageDataForDomain"
load_url = "https://www.notion.so/api/v3/loadPageChunk"
sync_url = "https://www.notion.so/api/v3/syncRecordValuesMain"

def format_id(uid: str) -> str:
    uid = uid.replace("-", "")
    if len(uid) != 32:
        return uid

    return f"{uid[0:8]}-{uid[8:12]}-{uid[12:16]}-{uid[16:20]}-{uid[20:32]}"

def parse_notion_url(url: str):
    parsed = urlparse(url)
    domain = parsed.netloc.split(".")[0]
    slug = parsed.path.strip("/")
    return domain, slug

def get_page_id(domain, slug):
    url = get_page_url_tpl.format(domain=domain)

    headers = {
        **headers_base,
        "Origin": f"https://{domain}.notion.site/{slug}",
        "Referer": f"https://{domain}.notion.site/{slug}"
    }

    payload = {
        "type": "block-space",
        "name": "page",
        "slug": "",
        "spaceDomain": domain,
        "requestedOnPublicDomain": True,
        "requestedOnExternalDomain": False,
        "requestedOnAlternateDomain": False,
        "embedded": False,
        "showMoveTo": False,
        "saveParent": False,
        "shouldDuplicate": False,
        "projectManagementLaunch": False,
        "configureOpenInDesktopApp": False,
        "mobileData": {"isPush": False},
        "demoWorkspaceMode": False
    }

    r = requests.post(url, json=payload, headers=headers)


    if r.status_code != 200:
        print("Erreur:", r.status_code, r.text)
        return None

    return r.json().get("pageId")


def load_page(page_id):
    payload = {
        "pageId": page_id,
        "limit": 100,
        "cursor": {"stack": []},
        "chunkNumber": 0,
        "verticalColumns": False
    }

    r = requests.post(load_url, json=payload, headers=headers_base)

    if r.status_code != 200:
        print("Erreur loadPageChunk:", r.status_code, r.text)
        return None

    return r.json()


def extract_user_ids(obj):
    user_ids = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "user_id":
                user_ids.append(v)
            user_ids.extend(extract_user_ids(v))

    elif isinstance(obj, list):
        for i in obj:
            user_ids.extend(extract_user_ids(i))

    return user_ids


print(" _______          __  .__             .__        __   ")
print(" \\      \\   _____/  |_|__| ____  _____|__| _____/  |_ ")
print(" /   |   \\ /  _ \\   __\\  |/  _ \\/  ___/  |/    \\   __\\")
print("/    |    (  <_> )  | |  (  <_> )___\\ |  |   |  \\  |  ")
print("\\____|__  /\\____/|__| |__|\\____/____  >__|___|  /__|  ")
print("        \\/                          \\/        \\/      ")
inp = input("Enter Notion URL or Page ID: ").strip()

#############
# Cas 1 URL #
#############
if inp.startswith("http"):
    print("[+] URL Submitted, parsing...")
    domain, slug = parse_notion_url(inp)

    print("[+] Page ID Extraction ... ")

    page_id = get_page_id(domain, slug)

############
# Cas 2 ID #
############
else:
    print("[-] Page ID Extraction ... ")
    page_id = format_id(inp)


if not page_id:
    print("Impossible de récupérer page_id")
    exit()

print("[+] Page ID Extracted :", page_id)

data = load_page(page_id)

if not data:
    exit()


print("[-] User ID Extraction ... ")
user_ids = list(set(extract_user_ids(data)))

print("[+] User IDs found:", user_ids)


print("[-] Requesting Notion's API for Users information ...")
sync_payload = {
    "requests": [
        {
            "pointer": {
                "table": "notion_user",
                "id": uid
            },
            "version": -1
        }
        for uid in user_ids
    ]
}

sync_resp = requests.post(sync_url, json=sync_payload, headers=headers_base)

if sync_resp.status_code == 200:
    data = sync_resp.json()

    users = data.get("recordMap", {}).get("notion_user", {})

    print("[+] Users found:\n")

    for uid, user_data in users.items():
        value = user_data.get("value", {}).get("value", {})

        user_id = value.get("id")
        name = value.get("name")
        email = value.get("email")

        print(f"- ID: {user_id}")
        print(f"  Name: {name}")
        print(f"  Email: {email}\n")

else:
    print(f"[ERROR] Batch -> {sync_resp.status_code}")
    print(sync_resp.text)
