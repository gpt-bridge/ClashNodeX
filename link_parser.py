# -*- coding: utf-8 -*-
"""
link_parser.py (v2.0 Comprehensive)
Supports:
- vless://
- vmess://
- trojan://
- ss://
- hysteria2:// / hy2://
- tuic://
- http(s):// subscription URLs (auto-fetches and extracts all nodes)
- Raw YAML proxy text
"""

import os
import base64
import json
import urllib.parse
import urllib.request
import re
import yaml
from typing import List, Optional, Tuple, Dict, Any


def safe_base64_decode(s: str) -> str:
    """Safely decode base64 strings with urlsafe and padding tolerance."""
    s = s.strip().replace("\r", "").replace("\n", "").replace(" ", "")
    rem = len(s) % 4
    if rem > 0:
        s += "=" * (4 - rem)
    try:
        return base64.b64decode(s).decode("utf-8", errors="ignore")
    except Exception:
        try:
            return base64.urlsafe_b64decode(s).decode("utf-8", errors="ignore")
        except Exception:
            return ""


def parse_single_link(link: str) -> Optional[Dict[str, Any]]:
    """Parse a single proxy link string into a Clash/Mihomo compatible proxy dict."""
    link = link.strip()
    if not link:
        return None

    try:
        lower = link.lower()
        if lower.startswith("vless://"):
            return _parse_vless(link)
        elif lower.startswith("vmess://"):
            return _parse_vmess(link)
        elif lower.startswith("trojan://"):
            return _parse_trojan(link)
        elif lower.startswith("ss://"):
            return _parse_ss(link)
        elif lower.startswith("hysteria2://") or lower.startswith("hy2://"):
            return _parse_hysteria2(link)
        elif lower.startswith("tuic://"):
            return _parse_tuic(link)
    except Exception as e:
        print(f"[link_parser] Error parsing link {link[:40]}...: {e}")
        return None

    return None


def _parse_vless(link: str) -> Optional[Dict[str, Any]]:
    parsed = urllib.parse.urlsplit(link)
    netloc = parsed.netloc
    if "@" not in netloc:
        return None

    uuid, host_port = netloc.split("@", 1)
    if ":" in host_port:
        host, port_str = host_port.split(":", 1)
        port = int(port_str.split("/")[0])
    else:
        host = host_port.split("/")[0]
        port = 443

    params = dict(urllib.parse.parse_qsl(parsed.query))
    name = urllib.parse.unquote(parsed.fragment) if parsed.fragment else f"VLESS-{host}:{port}"

    proxy: Dict[str, Any] = {
        "name": name,
        "type": "vless",
        "server": host,
        "port": port,
        "uuid": uuid,
        "udp": True,
    }

    flow = params.get("flow")
    if flow:
        proxy["flow"] = flow

    security = params.get("security", "").lower()
    if security == "reality":
        proxy["tls"] = True
        reality_opts: Dict[str, Any] = {}
        if "pbk" in params:
            reality_opts["public-key"] = params["pbk"]
        if "sid" in params:
            reality_opts["short-id"] = params["sid"]
        proxy["reality-opts"] = reality_opts
        if "sni" in params:
            proxy["servername"] = params["sni"]
        proxy["client-fingerprint"] = params.get("fp") or "chrome"
    elif security == "tls":
        proxy["tls"] = True
        if "sni" in params:
            proxy["servername"] = params["sni"]
        proxy["client-fingerprint"] = params.get("fp") or "chrome"
        if params.get("allowInsecure") == "1":
            proxy["skip-cert-verify"] = True

    net_type = params.get("type", "tcp").lower()
    if net_type == "ws":
        proxy["network"] = "ws"
        ws_opts: Dict[str, Any] = {}
        if "path" in params:
            ws_opts["path"] = urllib.parse.unquote(params["path"])
        if "host" in params:
            ws_opts["headers"] = {"Host": params["host"]}
        proxy["ws-opts"] = ws_opts
    elif net_type == "grpc":
        proxy["network"] = "grpc"
        grpc_opts: Dict[str, Any] = {}
        if "serviceName" in params:
            grpc_opts["grpc-service-name"] = urllib.parse.unquote(params["serviceName"])
        proxy["grpc-opts"] = grpc_opts

    return proxy


def _parse_vmess(link: str) -> Optional[Dict[str, Any]]:
    payload = link[8:].strip()
    raw = safe_base64_decode(payload)
    if not raw:
        return None
    data = json.loads(raw)

    server = data.get("add", "")
    port = int(data.get("port", 443))
    name = data.get("ps") or f"VMess-{server}:{port}"

    proxy: Dict[str, Any] = {
        "name": name,
        "type": "vmess",
        "server": server,
        "port": port,
        "uuid": str(data.get("id", "")),
        "alterId": int(data.get("aid", 0)),
        "cipher": data.get("scy", "auto") or "auto",
        "udp": True,
    }

    tls_val = str(data.get("tls", "")).lower()
    if tls_val in ("tls", "1", "true"):
        proxy["tls"] = True
        if data.get("sni"):
            proxy["servername"] = data.get("sni")
        proxy["client-fingerprint"] = data.get("fp") or "chrome"

    net_type = str(data.get("net", "tcp")).lower()
    if net_type == "ws":
        proxy["network"] = "ws"
        ws_opts: Dict[str, Any] = {}
        if data.get("path"):
            ws_opts["path"] = data.get("path")
        if data.get("host"):
            ws_opts["headers"] = {"Host": data.get("host")}
        proxy["ws-opts"] = ws_opts
    elif net_type == "grpc":
        proxy["network"] = "grpc"
        if data.get("path"):
            proxy["grpc-opts"] = {"grpc-service-name": data.get("path")}

    return proxy


def _parse_trojan(link: str) -> Optional[Dict[str, Any]]:
    parsed = urllib.parse.urlsplit(link)
    password = parsed.username or (parsed.netloc.split("@")[0] if "@" in parsed.netloc else "")
    host_port = parsed.netloc.split("@")[-1]
    if ":" in host_port:
        host, port_str = host_port.split(":", 1)
        port = int(port_str.split("/")[0])
    else:
        host = host_port.split("/")[0]
        port = 443

    params = dict(urllib.parse.parse_qsl(parsed.query))
    name = urllib.parse.unquote(parsed.fragment) if parsed.fragment else f"Trojan-{host}:{port}"

    proxy: Dict[str, Any] = {
        "name": name,
        "type": "trojan",
        "server": host,
        "port": port,
        "password": password,
        "udp": True,
        "skip-cert-verify": False,
    }
    if "sni" in params:
        proxy["sni"] = params["sni"]
    proxy["client-fingerprint"] = params.get("fp") or "chrome"
    if params.get("allowInsecure") == "1":
        proxy["skip-cert-verify"] = True

    net_type = params.get("type", "").lower()
    if net_type == "ws":
        proxy["network"] = "ws"
        ws_opts: Dict[str, Any] = {}
        if "path" in params:
            ws_opts["path"] = urllib.parse.unquote(params["path"])
        if "host" in params:
            ws_opts["headers"] = {"Host": params["host"]}
        proxy["ws-opts"] = ws_opts
    elif net_type == "grpc":
        proxy["network"] = "grpc"
        if "serviceName" in params:
            proxy["grpc-opts"] = {"grpc-service-name": urllib.parse.unquote(params["serviceName"])}

    return proxy


def _parse_ss(link: str) -> Optional[Dict[str, Any]]:
    parsed = urllib.parse.urlsplit(link)
    name = urllib.parse.unquote(parsed.fragment) if parsed.fragment else "Shadowsocks"
    netloc = parsed.netloc

    if "@" in netloc:
        userinfo, host_port = netloc.split("@", 1)
        decoded_userinfo = safe_base64_decode(userinfo)
        if ":" in decoded_userinfo:
            cipher, password = decoded_userinfo.split(":", 1)
        else:
            cipher, password = "aes-256-gcm", decoded_userinfo
        if ":" in host_port:
            host, port_str = host_port.split(":", 1)
            port = int(port_str.split("/")[0])
        else:
            host, port = host_port.split("/")[0], 8388
    else:
        decoded = safe_base64_decode(netloc)
        if "@" in decoded:
            userinfo, host_port = decoded.split("@", 1)
            if ":" in userinfo:
                cipher, password = userinfo.split(":", 1)
            else:
                cipher, password = "aes-256-gcm", userinfo
            if ":" in host_port:
                host, port_str = host_port.split(":", 1)
                port = int(port_str.split("/")[0])
            else:
                host, port = host_port.split("/")[0], 8388
        else:
            return None

    return {
        "name": name,
        "type": "ss",
        "server": host,
        "port": port,
        "cipher": cipher,
        "password": password,
        "udp": True,
    }


def _parse_hysteria2(link: str) -> Optional[Dict[str, Any]]:
    """
    Parse hysteria2:// or hy2:// links:
    hysteria2://password@host:port/?sni=xxx&insecure=1#name
    """
    # Normalize hy2:// to hysteria2://
    clean_link = link
    if clean_link.lower().startswith("hy2://"):
        clean_link = "hysteria2://" + clean_link[6:]

    parsed = urllib.parse.urlsplit(clean_link)
    password = parsed.username or (parsed.netloc.split("@")[0] if "@" in parsed.netloc else "")
    host_port = parsed.netloc.split("@")[-1]
    
    if ":" in host_port:
        host, port_str = host_port.split(":", 1)
        # In case of mport=... or slash
        port = int(port_str.split("/")[0].split("?")[0])
    else:
        host = host_port.split("/")[0]
        port = 443

    params = dict(urllib.parse.parse_qsl(parsed.query))
    name = urllib.parse.unquote(parsed.fragment) if parsed.fragment else f"Hysteria2-{host}:{port}"

    proxy: Dict[str, Any] = {
        "name": name,
        "type": "hysteria2",
        "server": host,
        "port": port,
        "password": password,
        "udp": True,
    }

    sni = params.get("sni")
    if sni:
        proxy["sni"] = sni
    
    insecure = params.get("insecure", "").lower()
    if insecure in ("1", "true"):
        proxy["skip-cert-verify"] = True
    else:
        proxy["skip-cert-verify"] = False

    obfs = params.get("obfs")
    if obfs:
        proxy["obfs"] = obfs
        if "obfs-password" in params:
            proxy["obfs-password"] = params["obfs-password"]

    return proxy


def _parse_tuic(link: str) -> Optional[Dict[str, Any]]:
    """Parse tuic://uuid:password@host:port?sni=...#name."""
    parsed = urllib.parse.urlsplit(link)
    userinfo = parsed.netloc.split("@")[0] if "@" in parsed.netloc else ""
    host_port = parsed.netloc.split("@")[-1]
    if ":" in host_port:
        host, port_str = host_port.split(":", 1)
        port = int(port_str.split("/")[0])
    else:
        host = host_port.split("/")[0]
        port = 443

    if ":" in userinfo:
        uuid, password = userinfo.split(":", 1)
    else:
        uuid, password = userinfo, ""

    params = dict(urllib.parse.parse_qsl(parsed.query))
    name = urllib.parse.unquote(parsed.fragment) if parsed.fragment else f"TUIC-{host}:{port}"

    proxy: Dict[str, Any] = {
        "name": name,
        "type": "tuic",
        "server": host,
        "port": port,
        "uuid": uuid,
        "password": password,
        "udp": True,
        "congestion-controller": params.get("congestion_control", "bbr"),
    }
    if "sni" in params:
        proxy["sni"] = params["sni"]
    if params.get("allow_insecure") in ("1", "true"):
        proxy["skip-cert-verify"] = True
    return proxy


def fetch_subscription_url(url: str, timeout: int = 10) -> Tuple[List[Dict[str, Any]], str]:
    """
    Fetch a subscription URL (http/https), auto-detect format (Base64 list or Clash YAML),
    and extract all proxy dictionaries.
    Returns (list_of_proxies, message).
    """
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Clash.Meta/v1.19.29 (Windows NT 10.0; Win64; x64) ClashVerge/2.5.2"
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_bytes = resp.read()
    except Exception as e:
        return [], f"拉取订阅链接失败: {e}"

    # Try 1: Parse as YAML
    try:
        text = raw_bytes.decode("utf-8")
        data = yaml.safe_load(text)
        if isinstance(data, dict) and "proxies" in data and isinstance(data["proxies"], list):
            valid = [p for p in data["proxies"] if isinstance(p, dict) and "name" in p and "type" in p]
            if valid:
                return valid, f"成功从订阅解析出 {len(valid)} 个 Clash 节点！"
    except Exception:
        pass

    # Try 2: Parse as Base64 list of node links
    try:
        decoded = safe_base64_decode(raw_bytes.decode("utf-8", errors="ignore"))
        if decoded:
            proxies, _ = parse_batch_text(decoded)
            if proxies:
                return proxies, f"成功从订阅解密出 {len(proxies)} 个节点！"
    except Exception:
        pass

    # Try 3: Parse as plain-text node links
    try:
        text = raw_bytes.decode("utf-8", errors="ignore")
        proxies, _ = parse_batch_text(text)
        if proxies:
            return proxies, f"成功解析出 {len(proxies)} 个节点！"
    except Exception:
        pass

    return [], "未能从该链接识别出任何节点，请确认该 URL 是否为有效订阅。"


def parse_batch_text(text: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Extract and parse multiple proxy links from multi-line text (e.g. from clipboard).
    Returns (success_proxies_list, failed_lines_list).
    """
    success: List[Dict[str, Any]] = []
    failed: List[str] = []

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # Check if the entire text is a single subscription URL
    if len(lines) == 1 and (lines[0].startswith("http://") or lines[0].startswith("https://")):
        sub_proxies, msg = fetch_subscription_url(lines[0])
        if sub_proxies:
            return sub_proxies, []
        else:
            return [], [lines[0]]

    for line in lines:
        lower = line.lower()
        if any(lower.startswith(p) for p in ("vless://", "vmess://", "trojan://", "ss://", "hysteria2://", "hy2://", "tuic://")):
            p = parse_single_link(line)
            if p:
                success.append(p)
            else:
                failed.append(line)
        elif lower.startswith("http://") or lower.startswith("https://"):
            # A line is a subscription URL
            sub_proxies, _ = fetch_subscription_url(line)
            if sub_proxies:
                success.extend(sub_proxies)
            else:
                failed.append(line)
        else:
            # Check if it might be a single YAML proxy snippet
            if ":" in line and any(k in line for k in ("name:", "type:", "server:")):
                try:
                    p = yaml.safe_load(line)
                    if isinstance(p, dict) and "name" in p and "type" in p:
                        success.append(p)
                        continue
                except Exception:
                    pass
            failed.append(line)
    return success, failed


def decode_qr_image(img_or_path) -> List[str]:
    """
    Decodes one or more QR codes from a PIL Image, filepath, or numpy image array using OpenCV.
    Returns a list of decoded string contents.
    """
    try:
        import cv2
        import numpy as np
        from PIL import Image

        if isinstance(img_or_path, str):
            if not os.path.isfile(img_or_path):
                return []
            pil_img = Image.open(img_or_path)
        elif hasattr(img_or_path, "convert"):
            pil_img = img_or_path
        else:
            return []

        rgb_img = pil_img.convert("RGB")
        cv_img = np.array(rgb_img)[:, :, ::-1]

        detector = cv2.QRCodeDetector()
        results: List[str] = []

        if hasattr(detector, "detectAndDecodeMulti"):
            retval, decoded_info, points, straight_qrcode = detector.detectAndDecodeMulti(cv_img)
            if retval and decoded_info:
                for text in decoded_info:
                    if text and text.strip():
                        results.append(text.strip())

        if not results:
            text, bbox, straight_qrcode = detector.detectAndDecode(cv_img)
            if text and text.strip():
                results.append(text.strip())

        return results
    except Exception as e:
        print(f"[link_parser] Error decoding QR code: {e}")
        return []


def parse_qr_image(img_or_path) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Decodes QR code from an image or file and parses any node links found.
    Returns (success_proxies_list, failed_lines_list).
    """
    texts = decode_qr_image(img_or_path)
    if not texts:
        return [], []

    all_proxies: List[Dict[str, Any]] = []
    failed: List[str] = []
    for t in texts:
        proxies, f = parse_batch_text(t)
        all_proxies.extend(proxies)
        failed.extend(f)

    return all_proxies, failed


# ---------------- Export and Sharing Functions ---------------- #

def export_proxy_to_link(proxy: Dict[str, Any]) -> str:
    """
    Serializes a Clash/Mihomo proxy dictionary into a standard shareable URI link
    (vless://, vmess://, trojan://, ss://, hysteria2://, tuic://).
    Returns empty string if unsupported.
    """
    if not isinstance(proxy, dict):
        return ""
    p_type = str(proxy.get("type", "")).lower().strip()
    name = str(proxy.get("name", "")).strip()
    server = str(proxy.get("server", "")).strip()
    port = proxy.get("port", 443)
    quoted_name = urllib.parse.quote(name)

    if p_type == "vless":
        uuid = str(proxy.get("uuid", "")).strip()
        params: Dict[str, str] = {}
        net = str(proxy.get("network", "tcp")).lower()
        params["type"] = net

        if proxy.get("reality-opts"):
            params["security"] = "reality"
            r_opts = proxy.get("reality-opts") or {}
            if "public-key" in r_opts:
                params["pbk"] = str(r_opts["public-key"])
            if "short-id" in r_opts:
                params["sid"] = str(r_opts["short-id"])
            sni = proxy.get("servername") or proxy.get("sni")
            if sni:
                params["sni"] = str(sni)
            if proxy.get("client-fingerprint"):
                params["fp"] = str(proxy["client-fingerprint"])
        elif proxy.get("tls"):
            params["security"] = "tls"
            sni = proxy.get("servername") or proxy.get("sni")
            if sni:
                params["sni"] = str(sni)
            if proxy.get("client-fingerprint"):
                params["fp"] = str(proxy["client-fingerprint"])
            if proxy.get("skip-cert-verify"):
                params["allowInsecure"] = "1"
        else:
            params["security"] = "none"

        if proxy.get("flow"):
            params["flow"] = str(proxy["flow"])

        if net == "ws":
            ws_opts = proxy.get("ws-opts") or {}
            if "path" in ws_opts:
                params["path"] = str(ws_opts["path"])
            if "headers" in ws_opts and isinstance(ws_opts["headers"], dict) and "Host" in ws_opts["headers"]:
                params["host"] = str(ws_opts["headers"]["Host"])
        elif net == "grpc":
            grpc_opts = proxy.get("grpc-opts") or {}
            if "grpc-service-name" in grpc_opts:
                params["serviceName"] = str(grpc_opts["grpc-service-name"])

        q_str = urllib.parse.urlencode(params)
        return f"vless://{uuid}@{server}:{port}?{q_str}#{quoted_name}"

    elif p_type == "vmess":
        v_data = {
            "v": "2",
            "ps": name,
            "add": server,
            "port": str(port),
            "id": str(proxy.get("uuid", "")),
            "aid": str(proxy.get("alterId", 0)),
            "scy": str(proxy.get("cipher", "auto")),
            "net": str(proxy.get("network", "tcp")),
            "type": "none",
            "host": "",
            "path": "",
            "tls": "tls" if proxy.get("tls") else "",
            "sni": str(proxy.get("servername") or proxy.get("sni") or ""),
        }
        if v_data["net"] == "ws":
            ws_opts = proxy.get("ws-opts") or {}
            v_data["path"] = str(ws_opts.get("path", ""))
            headers = ws_opts.get("headers") or {}
            if isinstance(headers, dict) and "Host" in headers:
                v_data["host"] = str(headers["Host"])
        elif v_data["net"] == "grpc":
            grpc_opts = proxy.get("grpc-opts") or {}
            v_data["path"] = str(grpc_opts.get("grpc-service-name", ""))

        raw_json = json.dumps(v_data, ensure_ascii=False)
        b64 = base64.b64encode(raw_json.encode("utf-8")).decode("utf-8")
        return f"vmess://{b64}"

    elif p_type == "trojan":
        password = str(proxy.get("password", ""))
        params = {}
        sni = proxy.get("sni") or proxy.get("servername")
        if sni:
            params["sni"] = str(sni)
        if proxy.get("skip-cert-verify"):
            params["allowInsecure"] = "1"
        if proxy.get("network"):
            params["type"] = str(proxy["network"])
        if params.get("type") == "ws":
            ws_opts = proxy.get("ws-opts") or {}
            if "path" in ws_opts:
                params["path"] = str(ws_opts["path"])
            if "headers" in ws_opts and isinstance(ws_opts["headers"], dict) and "Host" in ws_opts["headers"]:
                params["host"] = str(ws_opts["headers"]["Host"])
        elif params.get("type") == "grpc":
            grpc_opts = proxy.get("grpc-opts") or {}
            if "grpc-service-name" in grpc_opts:
                params["serviceName"] = str(grpc_opts["grpc-service-name"])
        q_str = f"?{urllib.parse.urlencode(params)}" if params else ""
        return f"trojan://{password}@{server}:{port}{q_str}#{quoted_name}"

    elif p_type == "ss":
        cipher = str(proxy.get("cipher", "aes-256-gcm"))
        password = str(proxy.get("password", ""))
        userinfo = base64.b64encode(f"{cipher}:{password}".encode("utf-8")).decode("utf-8")
        return f"ss://{userinfo}@{server}:{port}#{quoted_name}"

    elif p_type in ("hysteria2", "hy2"):
        password = str(proxy.get("password", ""))
        params = {}
        if proxy.get("sni"):
            params["sni"] = str(proxy["sni"])
        if proxy.get("skip-cert-verify"):
            params["insecure"] = "1"
        if proxy.get("obfs"):
            params["obfs"] = str(proxy["obfs"])
            if proxy.get("obfs-password"):
                params["obfs-password"] = str(proxy["obfs-password"])
        q_str = f"?{urllib.parse.urlencode(params)}" if params else ""
        return f"hysteria2://{password}@{server}:{port}/{q_str}#{quoted_name}"

    elif p_type == "tuic":
        uuid = str(proxy.get("uuid", ""))
        password = str(proxy.get("password", ""))
        params = {}
        if proxy.get("sni"):
            params["sni"] = str(proxy["sni"])
        if proxy.get("congestion-controller"):
            params["congestion_control"] = str(proxy["congestion-controller"])
        if proxy.get("skip-cert-verify"):
            params["allow_insecure"] = "1"
        q_str = f"?{urllib.parse.urlencode(params)}" if params else ""
        return f"tuic://{uuid}:{password}@{server}:{port}{q_str}#{quoted_name}"

    return ""


def export_proxies_to_links(proxies: List[Dict[str, Any]]) -> List[str]:
    """Converts a list of proxies to a list of shareable URI strings."""
    links = []
    for p in proxies:
        l = export_proxy_to_link(p)
        if l:
            links.append(l)
    return links


def export_proxies_to_subscription_base64(proxies: List[Dict[str, Any]]) -> str:
    """Exports proxies as a Base64-encoded subscription string."""
    links = export_proxies_to_links(proxies)
    if not links:
        return ""
    combined = "\n".join(links)
    return base64.b64encode(combined.encode("utf-8")).decode("utf-8")


def export_proxies_to_yaml_snippet(proxies: List[Dict[str, Any]]) -> str:
    """Exports proxies into a clean Clash/Mihomo YAML proxies configuration block."""
    try:
        clean_proxies = []
        for p in proxies:
            cp = {k: v for k, v in p.items() if not str(k).startswith("_")}
            clean_proxies.append(cp)
        return yaml.dump({"proxies": clean_proxies}, allow_unicode=True, sort_keys=False)
    except Exception as e:
        return f"# Error exporting YAML: {e}"


def generate_proxy_qr_image(data: str, box_size: int = 7, border: int = 2):
    """
    Generates a PIL Image of a QR code containing `data`.
    """
    try:
        import qrcode
        from PIL import Image

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        return img
    except Exception as e:
        print(f"[link_parser] Error generating QR code image: {e}")
        return None

