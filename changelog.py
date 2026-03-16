#!/usr/bin/env python3
"""changelog - Generate changelog from git conventional commits."""
import subprocess, argparse, re, sys, time
from collections import defaultdict

TYPES = {
    'feat': '✨ Features', 'fix': '🐛 Bug Fixes', 'docs': '📚 Documentation',
    'style': '💎 Style', 'refactor': '♻️ Refactoring', 'perf': '⚡ Performance',
    'test': '✅ Tests', 'build': '📦 Build', 'ci': '🔧 CI',
    'chore': '🔨 Chores', 'revert': '⏪ Reverts',
}

def get_commits(since=None):
    cmd = ['git', 'log', '--format=%H|%s|%an|%ai']
    if since: cmd.append(f'{since}..HEAD')
    r = subprocess.run(cmd, capture_output=True, text=True)
    commits = []
    for line in r.stdout.strip().split('\n'):
        if not line: continue
        parts = line.split('|', 3)
        if len(parts) >= 4:
            commits.append({'hash': parts[0][:7], 'subject': parts[1], 'author': parts[2], 'date': parts[3][:10]})
    return commits

def parse_commit(subject):
    m = re.match(r'^(\w+)(?:\(([^)]+)\))?(!)?:\s*(.+)', subject)
    if m:
        return {'type': m.group(1), 'scope': m.group(2), 'breaking': bool(m.group(3)), 'desc': m.group(4)}
    return {'type': 'other', 'scope': None, 'breaking': False, 'desc': subject}

def main():
    p = argparse.ArgumentParser(description='Changelog generator')
    p.add_argument('--since', help='Generate since tag/commit')
    p.add_argument('--version', help='Version label')
    p.add_argument('-o', '--output', help='Output file')
    p.add_argument('--all', action='store_true', help='Include non-conventional commits')
    args = p.parse_args()

    commits = get_commits(args.since)
    if not commits: print("No commits found."); return

    grouped = defaultdict(list)
    breaking = []
    
    for c in commits:
        parsed = parse_commit(c['subject'])
        c.update(parsed)
        if parsed['breaking']: breaking.append(c)
        if parsed['type'] in TYPES or args.all:
            grouped[parsed['type']].append(c)

    version = args.version or time.strftime('%Y.%m.%d')
    lines = [f"# {version} ({time.strftime('%Y-%m-%d')})\n"]
    
    if breaking:
        lines.append("## ⚠️ Breaking Changes\n")
        for c in breaking:
            lines.append(f"- {c['desc']} ({c['hash']})")
        lines.append("")
    
    for type_key, label in TYPES.items():
        if type_key in grouped:
            lines.append(f"## {label}\n")
            for c in grouped[type_key]:
                scope = f"**{c['scope']}:** " if c['scope'] else ""
                lines.append(f"- {scope}{c['desc']} ({c['hash']})")
            lines.append("")
    
    if 'other' in grouped and args.all:
        lines.append("## Other\n")
        for c in grouped['other']:
            lines.append(f"- {c['desc']} ({c['hash']})")
        lines.append("")

    output = '\n'.join(lines)
    if args.output:
        with open(args.output, 'w') as f: f.write(output)
        print(f"Wrote changelog to {args.output}")
    else:
        print(output)

if __name__ == '__main__':
    main()
