import urllib.request
import json
import sys

SESSION_FILE = r"C:\Users\nagas\Desktop\BTST\data\.kite_session"

def get_session_id():
    try:
        with open(SESSION_FILE, "r") as f:
            return f.read().strip()
    except Exception:
        return "kitemcp-6040a88e-3c42-4345-835e-101cf0904c6f"

def call_kite_tool(tool_name, arguments={}):
    session_id = get_session_id()
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "mcp-session-id": session_id
    }
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }).encode("utf-8")
    
    req = urllib.request.Request("https://mcp.kite.trade/mcp", data=payload, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        raw = resp.read().decode("utf-8")
        res_obj = json.loads(raw)
        if "result" in res_obj and "content" in res_obj["result"]:
            txt = res_obj["result"]["content"][0]["text"]
            try:
                return json.loads(txt)
            except Exception:
                return txt
        return res_obj
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        tool = sys.argv[1]
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
        print(json.dumps(call_kite_tool(tool, args), indent=2))
