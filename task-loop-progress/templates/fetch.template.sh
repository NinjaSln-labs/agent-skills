#!/bin/bash
# {{TASK_ID}} 远程进度拉取 — poll_command 调用
# 凭据：server-credentials；密码勿 echo 到日志
set -e
REMOTE_HOST="{{REMOTE_HOST}}"
REMOTE_USER="root"
PROGRESS_PATH="{{REMOTE_PROGRESS_JSON}}"
LOG_PATH="{{REMOTE_LOG}}"
# TODO: SSH 命令（国内直连 / 海外 ProxyJump / SOCKS5）

PROG=$(ssh "${REMOTE_USER}@${REMOTE_HOST}" "cat '${PROGRESS_PATH}'" 2>/dev/null || echo '{}')
LOG=$(ssh "${REMOTE_USER}@${REMOTE_HOST}" "tail -5 '${LOG_PATH}'" 2>/dev/null || true)
TS=$(date '+%Y-%m-%d %H:%M:%S')

python2 -c "
import json, sys
print json.dumps({
    'ts': sys.argv[1],
    'prog': sys.argv[2],
    'log': sys.argv[3],
})
" "$TS" "$PROG" "$LOG"
