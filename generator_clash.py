#!/usr/bin/env python3
"""
Generate a Clash-compatible subscription YAML from merged_subscription.txt
Supports: vmess://, trojan://, ss:// (basic)
"""
import base64
import json
from pathlib import Path
from urllib.parse import urlparse, unquote


def safe_b64_decode(s: str) -> bytes:
    s = s.strip()
    # add padding
    missing = len(s) % 4
    if missing:
        s += '=' * (4 - missing)
    return base64.urlsafe_b64decode(s)


def parse_vmess(uri: str):
    data_b64 = uri[len('vmess://'):]
    try:
        decoded = safe_b64_decode(data_b64).decode('utf-8')
        obj = json.loads(decoded)
    except Exception:
        return None
    name = obj.get('ps') or obj.get('name') or f"vmess@{obj.get('add','') }"
    proxy = {
        'name': name,
        'type': 'vmess',
        'server': obj.get('add'),
        'port': int(obj.get('port', 0) or 0),
        'uuid': obj.get('id') or obj.get('uuid'),
        'alterId': int(obj.get('aid', 0) or 0),
        'cipher': 'auto',
    }
    # network
    net = obj.get('net')
    if net:
        proxy['network'] = net
        if net == 'ws':
            path = obj.get('path') or obj.get('=path') or ''
            host = obj.get('host') or obj.get('sni') or ''
            if path:
                proxy['ws-path'] = path
            if host:
                proxy.setdefault('ws-headers', {})['Host'] = host
    # tls
    if obj.get('tls') in ('tls', '1', 'true'):
        proxy['tls'] = True
    return proxy


def parse_trojan(uri: str):
    # trojan://password@host:port?params#name
    try:
        p = urlparse(uri)
    except Exception:
        return None
    if p.scheme != 'trojan':
        return None
    name = unquote(p.fragment) if p.fragment else f"trojan@{p.hostname}"
    proxy = {
        'name': name,
        'type': 'trojan',
        'server': p.hostname,
        'port': int(p.port or 443),
        'password': p.username or p.password or '',
    }
    # sni in query
    if p.hostname:
        proxy['sni'] = p.hostname
    return proxy


def parse_ss(uri: str):
    # Basic support: ss://method:password@host:port#name or ss://base64(...) pattern
    body = uri[len('ss://'):]
    # if contains '@' it's the clear form
    if '@' in body:
        try:
            left, right = body.rsplit('@', 1)
            method, password = left.split(':', 1)
            hostport, *frag = right.split('#')
            host, port = hostport.split(':')
            name = unquote(frag[0]) if frag else f"ss@{host}"
            proxy = {
                'name': name,
                'type': 'ss',
                'server': host,
                'port': int(port),
                'cipher': method,
                'password': password,
            }
            return proxy
        except Exception:
            return None
    else:
        # base64 encoded part before optional #
        parts = body.split('#', 1)
        b64 = parts[0]
        name = unquote(parts[1]) if len(parts) > 1 else None
        try:
            decoded = safe_b64_decode(b64).decode('utf-8')
            # decoded is method:password@host:port
            left, right = decoded.split('@', 1)
            method, password = left.split(':', 1)
            host, port = right.split(':')
            proxy = {
                'name': name or f"ss@{host}",
                'type': 'ss',
                'server': host,
                'port': int(port),
                'cipher': method,
                'password': password,
            }
            return proxy
        except Exception:
            return None


def to_yaml_block(proxies):
    lines = []
    lines.append('proxies:')
    for p in proxies:
        lines.append(f"  - name: \"{p.get('name','') }\"")
        lines.append(f"    type: {p.get('type')}")
        lines.append(f"    server: {p.get('server','')}")
        lines.append(f"    port: {p.get('port',0)}")
        if p['type'] == 'vmess':
            if 'uuid' in p:
                lines.append(f"    uuid: {p.get('uuid')}")
            lines.append(f"    alterId: {p.get('alterId',0)}")
            if p.get('tls'):
                lines.append(f"    tls: true")
            if p.get('network'):
                lines.append(f"    network: {p.get('network')}")
            if p.get('ws-path'):
                lines.append(f"    ws-path: \"{p.get('ws-path')}\"")
            if p.get('ws-headers'):
                lines.append(f"    ws-headers:")
                for k, v in p.get('ws-headers', {}).items():
                    lines.append(f"      {k}: \"{v}\"")
        elif p['type'] == 'trojan':
            lines.append(f"    password: \"{p.get('password','')}\"")
            if p.get('sni'):
                lines.append(f"    sni: {p.get('sni')}")
        elif p['type'] == 'ss':
            lines.append(f"    cipher: {p.get('cipher','')}")
            lines.append(f"    password: \"{p.get('password','')}\"")
    # add a simple proxy-group and rules
    lines.append('')
    lines.append('proxy-groups:')
    group_names = [p.get('name','').replace('\"','') for p in proxies]
    lines.append('  - name: "Auto"')
    lines.append('    type: select')
    lines.append('    proxies:')
    for n in group_names:
        lines.append(f'      - "{n}"')
    lines.append('')
    lines.append('rules:')
    lines.append('  - MATCH,Auto')
    return '\n'.join(lines)


def main():
    src = Path('merged_subscription.txt')
    if not src.exists():
        print('merged_subscription.txt not found. Run aggregator first.')
        return 1
    lines = [l.strip() for l in src.read_text(encoding='utf-8').splitlines() if l.strip()]
    proxies = []
    unknown = []
    for l in lines:
        if l.startswith('vmess://'):
            p = parse_vmess(l)
            if p:
                proxies.append(p)
            else:
                unknown.append(l)
        elif l.startswith('trojan://'):
            p = parse_trojan(l)
            if p:
                proxies.append(p)
            else:
                unknown.append(l)
        elif l.startswith('ss://'):
            p = parse_ss(l)
            if p:
                proxies.append(p)
            else:
                unknown.append(l)
        else:
            unknown.append(l)

    out = Path('clash_subscription.yaml')
    out.write_text(to_yaml_block(proxies), encoding='utf-8')
    print(f'Wrote {len(proxies)} proxies to {out} (skipped {len(unknown)} unknown lines)')
    if unknown:
        Path('clash_unknown_lines.txt').write_text('\n'.join(unknown), encoding='utf-8')
        print('Wrote unknown lines to clash_unknown_lines.txt')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
