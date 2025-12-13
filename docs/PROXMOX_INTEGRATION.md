# Proxmox Integration Guide

This guide provides comprehensive documentation for deploying the Enterprise CI/CD application to LXC containers and QEMU VMs through Proxmox VE.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture](#architecture)
4. [Setup](#setup)
5. [LXC Container Deployment](#lxc-container-deployment)
6. [QEMU VM Deployment](#qemu-vm-deployment)
7. [Hybrid Deployment](#hybrid-deployment)
8. [CI/CD Integration](#cicd-integration)
9. [Troubleshooting](#troubleshooting)

## Overview

The Proxmox integration extends the Enterprise CI/CD pipeline to support three deployment platforms:

- **Docker** - Lightweight application containers (existing)
- **LXC** - System containers for legacy applications and enhanced isolation
- **QEMU/KVM** - Full virtual machines for maximum isolation and non-Linux workloads

## Prerequisites

### Proxmox VE Setup

1. **Proxmox VE 8.0+** installed and configured
2. **API Token** created for automation (least privilege recommended):
   ```bash
   # Create automation user
   pveum user add ansible@pve
   
   # Create a custom role with only required permissions (example: VM/CT management)
   pveum role add CICDAutomation -privs "VM.Audit VM.PowerMgmt VM.Config VM.Console VM.Migrate VM.Clone VM.Snapshot VM.Backup Datastore.Allocate"
   
   # Assign the custom role to the automation user, scoped to required path
   pveum aclmod /vms -user ansible@pve -role CICDAutomation
   
   # Create API token (privilege separation enabled by default)
   pveum user token add ansible@pve ansible
   ```
   > **Security Note:**  
   > Do **not** use `--privsep=0` or assign the `Administrator` role unless absolutely necessary.  
   > Always use the principle of least privilege and scope the ACL to only the required resources.

3. **Network Configuration**:
   - Bridge `vmbr0` configured
   - IP addressing scheme planned
   - DHCP or static IP allocation configured

4. **Storage**:
   - `local` storage for VM/container disks
   - `local:vztmpl` for LXC templates

### Ansible Requirements

Install required Ansible collections:

```bash
ansible-galaxy collection install community.general
pip install proxmoxer requests
```

### Environment Variables

Set the following environment variables:

```bash
export PROXMOX_URL="https://proxmox.example.com:8006"
export PROXMOX_NODE="pve1"
export PROXMOX_USERNAME="ansible@pve"
export PROXMOX_TOKEN="ansible"
export PROXMOX_API_TOKEN="your-api-token-secret"
```

## Architecture

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Proxmox VE Cluster                           │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Node 1     │  │   Node 2     │  │   Node 3     │        │
│  │              │  │              │  │              │        │
│  │  Docker ✓    │  │  Docker ✓    │  │  Docker ✓    │        │
│  │  LXC ✓       │  │  LXC ✓       │  │  LXC ✓       │        │
│  │  QEMU VMs ✓  │  │  QEMU VMs ✓  │  │  QEMU VMs ✓  │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                 │
│  Unified Management via Ansible                                │
└─────────────────────────────────────────────────────────────────┘
```

### Use Case Mapping

| Workload Type | Recommended Platform | Reasoning |
|--------------|---------------------|-----------|
| Modern APIs | Docker | Fast, portable, best ecosystem |
| Legacy apps with systemd | LXC | Full OS environment, systemd support |
| High-security workloads | QEMU VM | Hardware-level isolation |
| Windows services | QEMU VM | Only option for Windows |
| Database servers | LXC or QEMU | Better isolation, performance |

## Setup

### 1. Configure Proxmox API Access

Edit inventory files to include your Proxmox cluster:

**ansible/inventories/prod/lxc-hosts.yml**:
```yaml
proxmox_cluster:
  hosts:
    pve1.example.com:
      ansible_host: 192.168.1.10
      proxmox_api_host: 192.168.1.10
      proxmox_node: pve1
  vars:
    proxmox_api_token_id: "ansible"
    proxmox_api_token_secret: "{{ lookup('env', 'PROXMOX_API_TOKEN') }}"
```

### 2. Download LXC Templates

```bash
pveam update
pveam download local ubuntu-22.04-standard_amd64.tar.zst
```

### 3. Verify Connectivity

```bash
ansible-playbook \
  -i ansible/inventories/prod/lxc-hosts.yml \
  ansible/playbooks/verify-proxmox.yml
```

## LXC Container Deployment

### Manual Deployment

Deploy an application to an LXC container:

```bash
ansible-playbook \
  -i ansible/inventories/prod/lxc-hosts.yml \
  ansible/playbooks/deploy-lxc.yml \
  -e "app_version=v1.0.0" \
  -e "environment=production" \
  -e "lxc_vmid=100" \
  -e "lxc_hostname=app-web-01"
```

### Container Configuration

Customize container resources in inventory:

```yaml
app_lxc_containers:
  hosts:
    app-web-lxc-01:
      lxc_vmid: 100
      lxc_hostname: app-web-01
      lxc_memory: 4096        # 4GB RAM
      lxc_cores: 4            # 4 CPU cores
      lxc_disk_size: "50"     # 50GB disk
      lxc_net0_ip: "192.168.1.100/24"
      lxc_net0_gw: "192.168.1.1"
```

### LXC Features

The deployment includes:

- ✅ Unprivileged containers (enhanced security)
- ✅ Systemd support for service management
- ✅ Automatic IP address detection (DHCP or static)
- ✅ SSH access configuration
- ✅ Application auto-start on boot

## QEMU VM Deployment

### Manual Deployment

Deploy an application to a QEMU VM:

```bash
ansible-playbook \
  -i ansible/inventories/prod/vm-hosts.yml \
  ansible/playbooks/deploy-vm.yml \
  -e "app_version=v1.0.0" \
  -e "environment=production" \
  -e "qemu_vmid=200" \
  -e "qemu_name=app-vm-01" \
  -e "docker_registry=registry.example.com"
```

### VM Configuration

Customize VM resources in inventory:

```yaml
app_qemu_vms:
  hosts:
    app-isolation-vm-01:
      qemu_vmid: 200
      qemu_name: app-isolation-01
      qemu_memory: 8192       # 8GB RAM
      qemu_cores: 8           # 8 CPU cores
      qemu_disk_size: "100G"  # 100GB disk
      qemu_cloudinit: yes     # Enable cloud-init
      qemu_ipconfig0: "ip=192.168.1.200/24,gw=192.168.1.1"
```

### Cloud-Init Support

For VMs with cloud-init:

```yaml
qemu_cloudinit: yes
qemu_ciuser: "admin"
qemu_cipassword: "secure-password"
qemu_sshkeys: "{{ lookup('file', '~/.ssh/id_rsa.pub') }}"
qemu_ipconfig0: "ip=dhcp"  # or "ip=192.168.1.200/24,gw=192.168.1.1"
```

## Hybrid Deployment

Deploy across multiple platforms simultaneously:

```bash
ansible-playbook \
  -i ansible/inventories/prod/hybrid-hosts.yml \
  ansible/playbooks/deploy-hybrid.yml \
  -e "app_version=v1.0.0" \
  -e "environment=production" \
  -e "deployment_targets=['docker', 'lxc', 'vm']"
```

This allows you to:

- Deploy the same application version across all platforms
- Run A/B tests between platforms
- Gradually migrate workloads from one platform to another

## CI/CD Integration

### GitLab CI

The `.gitlab-ci.yml` file includes stages for LXC and VM deployment:

```yaml
stages:
  - build
  - test
  - security
  - package
  - deploy-docker
  - deploy-lxc      # New
  - deploy-vm       # New
  - cleanup
```

**Trigger LXC deployment**:
```bash
# In GitLab CI/CD, manually trigger or push to appropriate branch
```

### GitHub Actions

The `.github/workflows/ci-cd.yml` includes jobs for LXC and VM deployment:

```yaml
jobs:
  deploy-lxc:
    name: Deploy to LXC
    # Automatically triggered on main branch or tags
    
  deploy-vm:
    name: Deploy to QEMU VM
    # Automatically triggered on main branch or tags
```

### Required Secrets

Configure the following secrets in your CI/CD platform:

**GitLab CI/CD Variables**:
- `PROXMOX_API_TOKEN` - API token secret
- `SSH_PRIVATE_KEY` - SSH key for host access

**GitHub Actions Secrets**:
- `PROXMOX_URL` - Proxmox API URL
- `PROXMOX_NODE` - Node name
- `PROXMOX_USERNAME` - API username
- `PROXMOX_TOKEN` - Token ID
- `PROXMOX_API_TOKEN` - Token secret
- `SSH_PRIVATE_KEY` - SSH key for host access

## Troubleshooting

### Common Issues

#### 1. API Authentication Failed

**Error**: `403 Forbidden` or `Permission denied`

**Solution**:
```bash
# Verify token permissions
pveum user token permissions list ansible@pve ansible

# Recreate token with privilege separation enabled (default)
pveum user token remove ansible@pve ansible
pveum user token add ansible@pve ansible
# Ensure the token's role has only the minimal required permissions for automation
```

#### 2. LXC Container Won't Start

**Error**: `container startup failed`

**Solution**:
```bash
# Check container configuration
pct config <vmid>

# View logs
journalctl -u pve-container@<vmid>

# Try starting manually
pct start <vmid>
```

#### 3. VM Cloud-Init Not Working

**Error**: VM starts but can't connect via SSH

**Solution**:
```bash
# Check cloud-init status in VM
qm guest exec <vmid> -- cloud-init status

# View cloud-init logs
qm guest exec <vmid> -- cat /var/log/cloud-init.log
```

#### 4. Network Connectivity Issues

**Error**: Can't reach container/VM from network

**Solution**:
```bash
# Verify bridge configuration
ip addr show vmbr0

# Check firewall rules
pve-firewall status

# Test from Proxmox host
ping <container-ip>
```

### Debug Mode

Enable verbose Ansible output:

```bash
ansible-playbook \
  -i ansible/inventories/prod/lxc-hosts.yml \
  ansible/playbooks/deploy-lxc.yml \
  -vvv
```

### Get Support

- **Proxmox Documentation**: https://pve.proxmox.com/wiki/Main_Page
- **Ansible Proxmox Module**: https://docs.ansible.com/ansible/latest/collections/community/general/proxmox_module.html
- **Project Issues**: https://github.com/your-org/enterprise-app/issues

## Best Practices

1. **Start with LXC** - Use LXC for most workloads unless you specifically need full VM isolation

2. **Use Unprivileged Containers** - Always use unprivileged LXC containers for better security

3. **Enable Cloud-Init** - Use cloud-init for QEMU VMs to automate initial configuration

4. **Monitor Resources** - Use Proxmox monitoring to track resource usage and optimize allocation

5. **Regular Backups** - Configure automated backups using Proxmox Backup Server

6. **Version Control** - Keep all Proxmox configurations in version control

7. **Test First** - Always test in staging before deploying to production

## Next Steps

1. Review the [LXC_QEMU_VM_COST_BENEFIT_ANALYSIS.md](../LXC_QEMU_VM_COST_BENEFIT_ANALYSIS.md) for detailed cost-benefit analysis

2. Plan your migration strategy following the phased approach

3. Set up monitoring and alerting for your Proxmox infrastructure

4. Train your team on Proxmox administration and troubleshooting

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-04  
**Maintainer**: DevOps Team
