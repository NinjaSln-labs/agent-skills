#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""{{TASK_ID}}：将 poll_command stdout 转为 task_loop 标准进度 JSON。"""
from __future__ import print_function
import json
import re
import sys

# TODO: 按任务修改
TOTAL = 1
PROGRESS_RE = re.compile(r'offset=(\d+)')


def main():
    raw = sys.stdin.read()
    # --- 模式 local_json / remote_fetch：stdin 为 JSON ---
    try:
        data = json.loads(raw.strip() or '{}')
    except ValueError:
        data = {'raw': raw}

    # TODO: 从 data 提取字段
    offset = 0
    errors = 0
    finished = False
    log_tail = []

    if 'prog' in data:
        try:
            prog = json.loads(data.get('prog') or '{}')
        except ValueError:
            prog = {}
        offset = int(prog.get('offset', 0))
        errors = int(prog.get('errors', 0))
        finished = bool(prog.get('finished'))
        log_tail = [ln for ln in (data.get('log') or '').splitlines() if ln.strip()]
    elif 'raw' in data:
        m = PROGRESS_RE.search(data['raw'])
        if m:
            offset = int(m.group(1))
        log_tail = [ln for ln in data['raw'].splitlines() if ln.strip()][-5:]

    pct = round(100.0 * offset / TOTAL, 2) if TOTAL else 0
    chat = 'offset=%d/%d (%.2f%%) errors=%d' % (offset, TOTAL, pct, errors)

    out = {
        'status': 'done' if finished else ('running' if offset else 'idle'),
        'finished': finished,
        'chat_line': chat,
        'metrics': {'offset': offset, 'total': TOTAL, 'pct': pct, 'errors': errors},
        'log_tail': log_tail,
    }
    if data.get('ts'):
        out['polled_at'] = data['ts']
    print(json.dumps(out))


if __name__ == '__main__':
    main()
