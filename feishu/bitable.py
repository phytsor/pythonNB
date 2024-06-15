import requests
import json

doc_token = "Di1Pb8ZDNaHdfUsSmupcWzoXnqe"
doc_table_id = "tbl6TzXNi6wtAnfP"


def get_tenant_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps(
        {
            "app_id": "cli_a6e0e9028f28500b",
            "app_secret": "VdB9UsdUX9D7T5euSKNVtcmrLbSzzgtf",
        }
    )

    headers = {"Content-Type": "application/json"}

    response = requests.request("POST", url, headers=headers, data=payload)
    token = response.json()["tenant_access_token"]
    return token


def get_table_data(size=20):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{doc_token}/tables/{doc_table_id}/records/search?page_size={size}"
    payload = json.dumps({})

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_tenant_access_token()}",
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return json.dumps(response.json())


def add_one_record(data_dict):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{doc_token}/tables/{doc_table_id}/records"
    payload = json.dumps(data_dict)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_tenant_access_token()}",
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)


def get_datas(size=200):
    resp = json.loads(get_table_data(size))

    datas = {}
    for item in resp["data"]["items"]:
        id_text = item["fields"]["ID"][0]["text"].strip()
        weight = item["fields"]["重量（mg）"]
        datas[id_text] = round(weight, 4)
    return datas
