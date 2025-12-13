# Ansible Roles for Proxmox Integration

This directory contains Ansible roles for managing LXC containers and QEMU VMs on Proxmox VE.

## Available Roles

### proxmox-common

Common setup and verification tasks for Proxmox VE integration.

**Features:**
- Installs required Python libraries (proxmoxer, requests)
- Verifies Proxmox API connectivity
- Checks node status and storage availability
- Provides common variables for other roles

**Variables:**
- `proxmox_api_host` - Proxmox API host
- `proxmox_api_port` - API port (default: 8006)
- `proxmox_api_user` - API user (default: root@pam)
- `proxmox_api_token_id` - Token ID
- `proxmox_api_token_secret` - Token secret
- `proxmox_node` - Proxmox node name

**Usage:**
```yaml
- hosts: proxmox_cluster
  roles:
    - role: proxmox-common
```

### lxc-container

Creates and manages LXC containers on Proxmox VE.

**Features:**
- Creates unprivileged LXC containers
- Configures network (DHCP or static IP)
- Starts containers automatically
- Detects container IP address
- Waits for SSH connectivity

**Variables:**
- `lxc_vmid` - Container VM ID (default: 100)
- `lxc_hostname` - Container hostname
- `lxc_ostemplate` - LXC template to use
- `lxc_memory` - Memory in MB (default: 2048)
- `lxc_cores` - CPU cores (default: 2)
- `lxc_disk_size` - Disk size in GB (default: 20)
- `lxc_net0_ip` - IP configuration (default: dhcp)
- `lxc_unprivileged` - Use unprivileged container (default: yes)

**Usage:**
```yaml
- hosts: proxmox_cluster
  roles:
    - role: proxmox-common
    - role: lxc-container
      vars:
        lxc_vmid: 100
        lxc_hostname: app-container
        lxc_memory: 4096
        lxc_cores: 4
```

### qemu-vm

Creates and manages QEMU/KVM virtual machines on Proxmox VE.

**Features:**
- Creates QEMU VMs with customizable resources
- Supports cloud-init configuration
- Configures networking and storage
- Starts VMs automatically
- Retrieves VM status

**Variables:**
- `qemu_vmid` - VM ID (default: 200)
- `qemu_name` - VM name
- `qemu_memory` - Memory in MB (default: 4096)
- `qemu_cores` - CPU cores (default: 4)
- `qemu_disk_size` - Disk size (default: 32G)
- `qemu_cloudinit` - Enable cloud-init (default: no)
- `qemu_ciuser` - Cloud-init username
- `qemu_ipconfig0` - IP configuration (default: ip=dhcp)

**Usage:**
```yaml
- hosts: proxmox_cluster
  roles:
    - role: proxmox-common
    - role: qemu-vm
      vars:
        qemu_vmid: 200
        qemu_name: app-vm
        qemu_memory: 8192
        qemu_cores: 8
        qemu_cloudinit: yes
```

## Dependencies

All roles require the `community.general` Ansible collection:

```bash
ansible-galaxy collection install community.general
```

Python dependencies:
```bash
pip install proxmoxer requests
```

## Role Structure

Each role follows the standard Ansible role structure:

```
role-name/
├── defaults/
│   └── main.yml      # Default variables
├── tasks/
│   └── main.yml      # Main task list
├── handlers/
│   └── main.yml      # Handlers (if any)
├── templates/
│   └── *.j2          # Jinja2 templates (if any)
└── meta/
    └── main.yml      # Role metadata and dependencies
```

## Testing

To test roles in a development environment:

```bash
# Syntax check
ansible-playbook --syntax-check playbooks/deploy-lxc.yml

# Dry run
ansible-playbook playbooks/deploy-lxc.yml --check

# Run with verbosity
ansible-playbook playbooks/deploy-lxc.yml -vvv
```

## Security Considerations

1. **API Tokens**: Always use API tokens instead of passwords
2. **Unprivileged Containers**: Default to unprivileged LXC containers
3. **Network Isolation**: Configure appropriate network segregation
4. **Resource Limits**: Set appropriate CPU and memory limits
5. **Backup Strategy**: Implement regular backup procedures

## Support

For issues or questions:
- Check the [Proxmox Integration Guide](../../docs/PROXMOX_INTEGRATION.md)
- Review [LXC QEMU VM Cost Benefit Analysis](../../LXC_QEMU_VM_COST_BENEFIT_ANALYSIS.md)
- Open an issue in the project repository

## License

MIT License - See LICENSE file for details
