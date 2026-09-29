---
name: config-scan
description: >-
  Config scan: detect security misconfigurations in config files, Docker, and IaC. Use
  when reviewing configuration security for containers, Kubernetes, Terraform, or
  application settings.
slug: config-scan
version: 1.1.1
displayName: config-scan
---

# Config Scan

Security review of configuration files and infrastructure as code.

## Quick Start

```
/config-scan                      # Scan all config files
/config-scan --docker             # Docker files only
/config-scan --k8s                # Kubernetes manifests
/config-scan --terraform          # Terraform files
/config-scan --env                # Environment files
```

## What This Skill Detects

### Environment Files
- Secrets in `.env` files
- Insecure default values
- Missing required security variables

### Docker Security
- Running as root
- Exposed sensitive ports
- Insecure base images
- Missing security options

### Kubernetes Security
- Privileged containers
- Missing resource limits
- Insecure service accounts
- Network policy gaps

### Infrastructure as Code
- Overly permissive IAM policies
- Public S3 buckets
- Unencrypted storage
- Missing security groups

### Application Config
- Debug mode enabled
- Verbose error messages
- Insecure defaults

## Scan Categories

### Environment Files

**Files scanned**: `.env`, `.env.*`, `*.env`

| Issue | Severity | Description |
|-------|----------|-------------|
| Secrets in .env | HIGH | Credentials should use secrets manager |
| .env committed | CRITICAL | Should be in .gitignore |
| DEBUG=true | HIGH | Debug mode in production config |
| Weak secrets | MEDIUM | Short or simple values |

**Detection patterns**:
```
# Committed .env files
git ls-files | grep -E '\.env$|\.env\.'

# Secrets in env files
(PASSWORD|SECRET|KEY|TOKEN|CREDENTIAL)=.+

# Debug flags
DEBUG=(true|1|yes)
NODE_ENV=development
```

### Docker Security

**Files scanned**: `Dockerfile`, `docker-compose.yml`

| Issue | Severity | Description |
|-------|----------|-------------|
| USER root | HIGH | Container runs as root |
| COPY secrets | CRITICAL | Secrets copied into image |
| Latest tag | MEDIUM | Unpinned base image |
| Exposed ports | LOW | Wide port exposure |
| No healthcheck | LOW | Missing health monitoring |

**Detection patterns**:

```dockerfile
# Running as root (no USER directive)
FROM.*\n(?!.*USER)

# Copying secrets
COPY.*\.(pem|key|crt|env)
COPY.*secret
COPY.*password

# Unpinned images
FROM\s+\w+:latest
FROM\s+\w+\s*$

# Dangerous capabilities
--privileged
--cap-add
```

**docker-compose.yml issues**:

```yaml
# Privileged mode
privileged: true

# All capabilities
cap_add:
  - ALL

# Host network
network_mode: host

# Sensitive mounts
volumes:
  - /:/host
  - /var/run/docker.sock
```

### Kubernetes Security

**Files scanned**: `*.yaml`, `*.yml` (k8s manifests)

| Issue | Severity | Description |
|-------|----------|-------------|
| privileged: true | CRITICAL | Full host access |
| runAsRoot | HIGH | Container runs as root |
| No resource limits | MEDIUM | DoS risk |
| hostNetwork | HIGH | Pod uses host network |
| No securityContext | MEDIUM | Missing security settings |

**Detection patterns**:

```yaml
# Privileged containers
securityContext:
  privileged: true

# Running as root
securityContext:
  runAsUser: 0
runAsNonRoot: false

# Host access
hostNetwork: true
hostPID: true
hostIPC: true

# Dangerous volume mounts
volumes:
  - hostPath:
      path: /

# Missing limits
# (absence of resources.limits)

# Wildcard RBAC
rules:
  - apiGroups: ["*"]
    resources: ["*"]
    verbs: ["*"]
```

### Terraform/IaC

**Files scanned**: `*.tf`, `*.tfvars`

| Issue | Severity | Description |
|-------|----------|-------------|
| Public S3 bucket | CRITICAL | Data exposure |
| * in IAM policy | HIGH | Overly permissive |
| No encryption | HIGH | Data at rest unencrypted |
| 0.0.0.0/0 ingress | HIGH | Open to internet |
| Hardcoded secrets | CRITICAL | Credentials in TF |

**Detection patterns**:

```hcl
# Public S3
acl = "public-read"
acl = "public-read-write"

# Overly permissive IAM
"Action": "*"
"Resource": "*"
"Principal": "*"

# Open security groups
cidr_blocks = ["0.0.0.0/0"]
ingress {
  from_port = 0
  to_port   = 65535

# Missing encryption
encrypted = false
# (or absence of encryption settings)

# Hardcoded secrets
password = "..."
secret_key = "..."
```

### Application Config

**Files scanned**: `config/*.json`, `*.config.js`, `application.yml`

| Issue | Severity | Description |
|-------|----------|-------------|
| DEBUG=true | HIGH | Debug in production |
| Verbose errors | MEDIUM | Stack traces exposed |
| CORS * | HIGH | All origins allowed |
| No HTTPS | MEDIUM | Unencrypted transport |

**Detection patterns**:

```javascript
// Debug mode
debug: true,
DEBUG: true,
NODE_ENV: 'development'

// Verbose errors
showStackTrace: true
detailedErrors: true

// CORS
origin: '*'
origin: true
Access-Control-Allow-Origin: *

// Session security
secure: false  // cookies
httpOnly: false
sameSite: 'none'
```

## Output Format

```
CONFIG SCAN RESULTS
===================

Files scanned: 23
Issues found: 15

CRITICAL (2)
------------
[!] Dockerfile:1 - Running as root
    No USER directive found
    Fix: Add "USER node" or similar non-root user

[!] terraform/s3.tf:12 - Public S3 bucket
    acl = "public-read"
    Fix: Remove public ACL, use bucket policies

HIGH (5)
--------
[H] docker-compose.yml:15 - Privileged container
    privileged: true
    Fix: Remove privileged flag, use specific capabilities

[H] k8s/deployment.yaml:34 - Missing resource limits
    No CPU/memory limits defined
    Fix: Add resources.limits section

...

MEDIUM (8)
----------
...
```

## Configuration

### Ignore Rules

Create `.config-scan-ignore`:

```yaml
# Ignore specific files
files:
  - "docker-compose.dev.yml"
  - "terraform/modules/test/**"

# Ignore specific rules
rules:
  - id: "docker-root-user"
    files: ["Dockerfile.dev"]
    reason: "Development only"

  - id: "k8s-no-limits"
    reason: "Handled by LimitRange"
```

### Scan Profiles

```yaml
# .config-scan.yaml
profile: production  # or: development, strict

# Custom thresholds
thresholds:
  fail_on: high
  warn_on: medium

# Specific scanners
scanners:
  docker: true
  kubernetes: true
  terraform: true
  env_files: true
  app_config: true
```

## Best Practices Checked

### Docker
- [ ] Non-root user specified
- [ ] Base image pinned to digest
- [ ] No secrets in build
- [ ] Multi-stage build used
- [ ] Health check defined
- [ ] Read-only root filesystem

### Kubernetes
- [ ] Non-root security context
- [ ] Resource limits defined
- [ ] Network policies in place
- [ ] No privileged containers
- [ ] Service accounts scoped
- [ ] Secrets encrypted at rest

### Terraform
- [ ] State file encrypted
- [ ] No hardcoded secrets
- [ ] Least privilege IAM
- [ ] Encryption enabled
- [ ] Logging enabled
- [ ] No public access by default

## Remediation Examples

### Docker: Run as Non-Root
```dockerfile
# Before
FROM node:18

# After
FROM node:18
RUN groupadd -r app && useradd -r -g app app
USER app
```

### Kubernetes: Security Context
```yaml
# Before
containers:
  - name: app
    image: myapp

# After
containers:
  - name: app
    image: myapp
    securityContext:
      runAsNonRoot: true
      runAsUser: 1000
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
```

### Terraform: Private S3
```hcl
# Before
resource "aws_s3_bucket" "data" {
  acl = "public-read"
}

# After
resource "aws_s3_bucket" "data" {
  # No ACL (private by default)
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

## Worked Example

Precondition: repo root containing a `Dockerfile` with no `USER` directive, a committed `.env` with `API_KEY=realvalue`, and `terraform/s3.tf` with `acl = "public-read"`.

Ask the agent: "Run config-scan on this repo."

Output excerpt (same shape as the Output Format section above):

```
CONFIG SCAN RESULTS
===================
Files scanned: 3
Issues found: 3

CRITICAL (2)
------------
[!] .env:2 - Secret in committed env file
    API_KEY=****
    Fix: Move to a secrets manager; add .env to .gitignore

[!] terraform/s3.tf:12 - Public S3 bucket
    acl = "public-read"
    Fix: Remove public ACL, use bucket policies

HIGH (1)
--------
[H] Dockerfile:1 - Running as root
    No USER directive found
    Fix: Add "USER node" or similar non-root user
```

## Failure Exits and Boundaries

- No matching files: if the scanned tree contains none of `.env*`, `Dockerfile`, `docker-compose*.yml`, k8s manifests, `*.tf`, or app config, report "0 files scanned" and ask for the correct path — never scan a parent directory silently and never fabricate findings.
- Unreadable or malformed `.config-scan.yaml` / `.config-scan-ignore`: report the exact path and parse error, then continue with defaults and say so — do not silently drop ignore rules.
- `git` unavailable (committed-.env check needs `git ls-files`): state that this specific check was skipped and why; run the remaining file-based checks.
- Scanning is performed by the agent applying the detection patterns in this document; there is no bundled script. Any output claiming a tool ran is wrong.

## NOT for / Anti-patterns

- NOT for dependency vulnerabilities — if the target is `package-lock.json` / `requirements.txt`, that is `/dependency-scan`.
- NOT for source-code security review (SQLi, XSS in app code) — that is `/security-scan`.
- NOT for credential rotation or auto-fixing: report findings (truncate secret values to a short prefix); never edit files to "fix" them unless the user asks.
- Anti-pattern: scanning generated/vendor trees (`node_modules/`, `vendor/`, `dist/`) — exclude them; findings there are noise.
- Anti-pattern: treating dev-only files (`docker-compose.dev.yml`, `.env.example`) as production — check filename and profile before assigning severity.

## Wrong → Right (FAQ)

| Wrong | Right |
|---|---|
| Reporting `.env.example` placeholders as leaked secrets | Values like `changeme`/empty are not leaks; example files are MEDIUM at most |
| Printing full secret values in the report | Show file:line and key name only; truncate the value |
| Running once locally and calling CI covered | Run this skill via the agent in CI with `--fail-on` exit-code semantics (see CI/CD Integration) and re-run per PR |
| "Fixing" a finding by deleting the config file | Fix in place via the Remediation Examples section |

## CI/CD Integration

This skill is executed by an agent — a CI pipeline cannot run a slash command as a shell step. The working pattern:

- In CI, have the agent run this skill against the PR's changed config files (Docker/k8s/Terraform/env per `--docker`/`--k8s`/`--terraform`/`--env` scoping).
- Decide the CI step's exit code using the `--fail-on <level>` semantics: exit non-zero when any finding at or above the given severity is present (e.g. fail on `high` for general config, `critical` for the Docker/IaC checks).
- Concretely: the CI job invokes the coding agent with an instruction to run the config scan on the PR and to fail the step if findings at the chosen severity exist; the agent prints the report in the same Output Format as a local run.
- Re-run per PR — a one-time local scan does not keep CI covered.

## Related Skills

- `/security-scan` - Full security analysis
- `/secrets-scan` - Credential detection
- `/dependency-scan` - Package vulnerabilities
