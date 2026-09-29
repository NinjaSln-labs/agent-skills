# Secrets Scan 通用检测模式长表（Detection Patterns 全文）

> This appendix is extracted verbatim from `secrets-scan/SKILL.md`; the "Detection Patterns" section in the main text retains a pointer, and the content below is authoritative. The domestic provider pattern table (Aliyun/Tencent/DingTalk/WeChat) remains in the main text.

## Detection Patterns

### Cloud Provider Keys

```regex
# AWS
AKIA[0-9A-Z]{16}                           # Access Key ID
[A-Za-z0-9/+=]{40}                         # Secret Access Key (context needed)

# Azure
[a-zA-Z0-9+/=]{88}                         # Storage Account Key

# GCP
AIza[0-9A-Za-z_-]{35}                      # API Key
[0-9]+-[a-z0-9]{32}\.apps\.googleusercontent\.com  # OAuth Client
```

### Version Control Tokens

```regex
# GitHub
gh[pousr]_[A-Za-z0-9]{36,}                 # Personal/OAuth/User/Repo/App
github_pat_[A-Za-z0-9]{22}_[A-Za-z0-9]{59} # Fine-grained PAT

# GitLab
glpat-[A-Za-z0-9-_]{20,}                   # Personal Access Token

# Bitbucket
[a-zA-Z0-9]{24}                            # App Password (context needed)
```

### Payment & Finance

```regex
# Stripe
sk_live_[a-zA-Z0-9]{24,}                   # Secret Key
rk_live_[a-zA-Z0-9]{24,}                   # Restricted Key
pk_live_[a-zA-Z0-9]{24,}                   # Publishable Key

# Square
sq0[a-z]{3}-[A-Za-z0-9_-]{22,}            # Access Token

# PayPal
access_token\$[a-zA-Z0-9-_.]+             # OAuth Token
```

### Communication Services

```regex
# Slack
xox[bpas]-[0-9]{10,}-[a-zA-Z0-9]{24,}     # Bot/User/App Token

# Twilio
SK[a-f0-9]{32}                             # API Key SID
[a-f0-9]{32}                               # Auth Token (context)

# SendGrid
SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}  # API Key
```

### Database Connection Strings

```regex
# PostgreSQL/MySQL
(postgres|mysql|mariadb)://[^:]+:[^@]+@[^/]+/\w+

# MongoDB
mongodb(\+srv)?://[^:]+:[^@]+@

# Redis
redis://:[^@]+@
```

### Private Keys

```regex
-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----
-----BEGIN PGP PRIVATE KEY BLOCK-----
```

### JWT & Session

```regex
eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+   # JWT
```
