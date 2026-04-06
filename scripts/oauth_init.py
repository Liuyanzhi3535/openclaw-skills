"""
一次性執行：在本機完成 Google OAuth2 授權，產生 google_token.json
之後把 token 上傳到 K3s PVC。

執行前需要：
1. 至 Google Cloud Console 建立 OAuth2 Desktop App 憑證
2. 下載 client_secret.json 放在此腳本同目錄
3. pip install google-auth-oauthlib
"""

import os

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CLIENT_SECRET_FILE = os.path.join(os.path.dirname(__file__), "client_secret.json")
OUTPUT_TOKEN = os.path.join(os.path.dirname(__file__), "google_token.json")


def main():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(OUTPUT_TOKEN, "w") as f:
        f.write(creds.to_json())

    print(f"Token 已儲存至：{OUTPUT_TOKEN}")
    print()
    print("接下來執行以下指令將 token 上傳至 K3s PVC：")
    print()
    print("  # 取得 Pod 名稱")
    print("  export KUBECONFIG=/etc/rancher/k3s/k3s.yaml")
    jsonpath = "'{.items[0].metadata.name}'"
    print(
        f"  POD=$(kubectl get pod -n openclaw"
        f" -l app.kubernetes.io/name=openclaw-helm"
        f" -o jsonpath={jsonpath})"
    )
    print()
    print("  # 上傳 token 至 PVC")
    dest = "/home/node/.openclaw/credentials/google_token.json"
    print(f"  kubectl cp {OUTPUT_TOKEN} openclaw/$POD:{dest} -c main")


if __name__ == "__main__":
    main()
