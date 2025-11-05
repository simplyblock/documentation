#!/usr/bin/env bash

PRIVATE_IP_RANGES=(
  "10.0.0.0/8"
  "172.16.0.0/12"
  "192.168.0.0/16"
)

UNSET_TRANSIENT_HOSTNAMECTL="localhost"
UNSET_TRANSIENT_HOSTNAME="localhost.localdomain"
UNSET_HOSTNAMECTL="(unset)"

echo_red() {
  echo -e "\033[01;31m$*\033[00m"
}
echo_green() {
  echo -e "\033[01;32m$*\033[00m"
}
echo_yellow() {
  echo -e "\033[01;33m$*\033[00m"
}
echo_bold() {
  echo -e "\033[0;1m$*\033[00m"
}

ensure_command() {
  echo -n "Checking ${1}... "
  cmd="$(command -v "${1}")"
  if ! [[ "${cmd}" ]]; then
    echo_red "not found, stopping."
    exit 1
  fi
  export "$(echo "$1" | ${AWK_EXEC} '{print toupper($0)}')_EXEC=${cmd}"
  echo_green "${1^^_EXEC}."
}

compare_version() {
  # Return exit code table
  # 0: equal
  # 1: gt
  # 2: lt
  if [[ "$1" == "$2" ]]; then
    return 0
  fi
  local IFS=.
  local i val1=($1) val2=($2)
  # fill empty fields in val1 with zeros
  for ((i = ${#val1[@]}; i < ${#val2[@]}; i++)); do
    val1[i]=0
  done
  for ((i=0; i<${#val1[@]}; i++)); do
    if ((10#${val1[i]:=0} > 10#${val2[i]:=0})); then
      return 1
    fi
    if ((10#${val1[i]} < 10#${val2[i]})); then
      return 2
    fi
  done
  return 0
}

check_nvme_multipath() {
  # Return exit code table
  # 0: Multipathing available and enabled
  # 1: Multipathing available but disabled
  # 2: Multipathing not available
  echo -n "Checking for NVMe over Fabrics Multipathing: "
  if ! [ -f /sys/module/nvme_core/parameters/multipath ]; then
    echo_red "Not available (probably disabled in Kernel configuration."
    return 2
  fi

  local enabled="$(cat /sys/module/nvme_core/parameters/multipath)"
  if [[ "${enabled}" == "Y" ]]; then
    echo_green "Enabled."
    return 0
  fi
  echo_yellow "Disabled (should be enabled for high-availability clusters)."
  return 1
}

check_sysctl() {
  local result=$(${SYSCTL_EXEC} -n $1)
  if ! [[ ${result} = "$2" ]]; then
    echo_red $3
    return 1
  fi
  echo_green "ok."
  return 0
}

ensure_ipv6_disabled() {
  echo -n "Checking IPv6 (all) is disabled: "
  check_sysctl "net.ipv6.conf.all.disable_ipv6" 1 "IPv6 enabled - please run <sysctl -w net.ipv6.conf.all.disable_ipv6=1>"
  echo -n "Checking IPv6 (default) is disabled: "
  check_sysctl "net.ipv6.conf.default.disable_ipv6" 1 "IPv6 enabled - please run <sysctl -w net.ipv6.conf.default.disable_ipv6=1>"
}

calc_cidr_netmask() {
  echo "$1" | ${AWK_EXEC} -F. '{split($0, octets); for (i in octets) {mask += 8 - log(2**8 - octets[i])/log(2);} print "/" mask}'
}

calc_network() {
  local temp="${IFS}"
  IFS=.
  read -r i1 i2 i3 i4 <<< "$1"
  read -r m1 m2 m3 m4 <<< "$2"
  IFS="${temp}"
  echo "$(printf "%d.%d.%d.%d" "$((i1 & m1))" "$((i2 & m2))" "$((i3 & m3))" "$((i4 & m4))")$(calc_cidr_netmask $2)"
}

get_netif_ip() {
  $IP_EXEC address show $1 | grep inet | grep brd | awk '{print $2; print $4;}'
}

find_phy_net_ifs() {
  local virtual_interfaces=($(ls /sys/devices/virtual/net/))
  local all_interfaces=($(ls /sys/class/net/))

  declare -A temp
  for element in "${virtual_interfaces[@]}" "${all_interfaces[@]}"; do
    ((temp[${element}]++))
  done
  for element in "${!temp[@]}"; do
    if (( ${temp[${element}]} > 1 )); then
      unset "temp[${element}]"
    fi
  done

  local diff=(${!temp[@]})    # retrieve the keys as values
  echo "${diff[@]}"
}

check_private_network() {
  local network; network="$(get_netif_ip $1)"
  if [ $? -eq 0 ]; then
    return 0
  fi
  for priv_net in "${PRIVATE_IP_RANGES[@]}"; do
    ipv4_network_check "${network}" "${priv_net}"
    if [ $? -eq 0 ]; then
      echo "${network}"
      return 0
    fi
  done
  return 1
}

ensure_phy_net_ifs() {
  echo -n "Searching network interface: "
  PHY_NETWORK_IFS=$(find_phy_net_ifs)
  if ! [[ ${PHY_NETWORK_IFS} ]]; then
    echo_red "no usable network interface found."
    return 1
  fi
  echo_green "${PHY_NETWORK_IFS}."

  for netif in "${PHY_NETWORK_IFS[@]}"; do
    echo -n "Checking IP configuration for ${netif}: "
    local network=$(check_private_network ${netif})
    if ! [[ "${network}" ]]; then
      echo_green "skipped - no private network."
    else
      echo_green "ok - ${network}."
    fi
  done
  return 0
}

ipv4_decode() {
  for i; do
    echo "$i" | {
      IFS=./
      read a b c d e
      test -z "${e}" && e=32
      echo -n "$((a<<24|b<<16|c<<8|d)) $((-1<<(32-e))) "
    }
  done
}

ipv4_network_check() {
  # Returns 0 when ip is in range and 1 if not
  ipv4_decode "$1" "$2" | {
    read addr1 mask1 addr2 mask2
    if (((addr1&mask2) == (addr2&mask2) && mask1 >= mask2)); then
      return 0
    else
      return 1
    fi
  }
}

find_python() {
  python=$(command -v python)
  if ! [[ ${python} ]]; then
    python=$(command -v python3)
  fi
  echo ${python}
}

find_pip() {
  pip=$(command -v pip)
  if ! [[ ${pip} ]]; then
    pip=$(command -v pip3)
  fi
  echo ${pip}
}

ensure_python() {
  echo -n "Checking Python: "
  check_python
  if [ $? ]; then
    check_python_version
  fi

  echo -n "Checking pip: "
  check_pip
  if [ $? ]; then
    check_pip_version
  fi
}

check_python() {
  PYTHON_EXEC=$(find_python)
  if ! [[ ${PYTHON_EXEC} ]]; then
    echo_red "not found."
    return 1
  fi
  return 0
}

check_pip() {
  PIP_EXEC=$(find_pip)
  if ! [[ ${PIP_EXEC} ]]; then
    echo_red "not found."
    return 1
  fi
  return 0
}

check_python_version() {
  python_version=$(${PYTHON_EXEC} -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
  compare_version ${MIN_PYTHON_VERSION} ${python_version}
  if [ $? -eq 1 ]; then
    echo_red "minimum required ${MIN_PYTHON_VERSION}, found ${python_version}."
    return 1
  fi
  echo_green "${python_version} (${PYTHON_EXEC})."
  return 0
}

check_pip_version() {
  PIP_EXEC=$(command -v pip)
  local version=$(${PYTHON_EXEC} -c 'import pip;print(pip.__version__)')
  compare_version ${MIN_PIP_VERSION} ${version}
  if [ $? -eq 1 ]; then
    echo_red "minimum required ${MIN_PIP_VERSION}, found ${version}."
    return 1
  fi
  echo_green "${version} (${PIP_EXEC})."
  return 0
}

ensure_docker() {
  echo -n "Checking Docker: "
  DOCKER_EXEC=$(command -v docker)
  if ! [[ ${DOCKER_EXEC} ]]; then
    echo_red "not found."
    return 1
  fi

  local version=$(${DOCKER_EXEC} --version | ${AWK_EXEC} '{sub(/,.*/, ""); print $3}')
  compare_version ${MIN_DOCKER_VERSION} ${version}
  if [ $? -eq 1 ]; then
    echo_red "minimum required ${MIN_DOCKER_VERSION}, found ${version}."
    return 1
  fi
  echo_green "${version}."
  return 0
}

ensure_sbcli() {
  echo -n "Checking ${SBCLI_RELEASE_NAME}: "
  local version=$(${PIP_EXEC} show ${SBCLI_RELEASE_NAME} 2>/dev/null | ${GREP_EXEC} Version | ${AWK_EXEC} '{print $2}')
  if ! [[ ${version} ]]; then
    echo_red "${SBCLI_RELEASE_NAME} not installed."
    return 1
  fi

  compare ${MIN_SBCLI_VERSION} ${version}
  if [ $? -eq 1 ]; then
    echo_red "minimum required ${MIN_SBCLI_VERSION}, found ${version}."
    return 1
  fi

  local latest_sbcli_version=$(${PIP_EXEC} index versions ${SBCLI_RELEASE_NAME} 2>/dev/null | ${GREP_EXEC} LATEST: | ${AWK_EXEC} '{print $2}')
  compare ${version} ${latest_sbcli_version}
  if [ $? -eq 1 ]; then
    echo_yellow "not latest version ${latest_sbcli_version}, installed ${version}."
    return 1
  fi

  echo_green ${version};
  return 0
}

ensure_os() {
  echo -n "Checking operating system: "
  os=$(uname)
  case "${os}" in
    Linux)
      echo_green "ok."
      return 0
      ;;
    *)
      echo_red "unsupported OS: ${os} - stopping."
      exit 1
      ;;
  esac
}

ensure_arch() {
  echo -n "Checking system architecture: "
  arch=$(uname -m)
  case "${arch}" in
    x86_64|amd64)
      echo_green "ok."
      return 0
      ;;
    *)
      echo_red "unsupported architecture ${arch}."
      return 1
      ;;
  esac
}

ensure_distro() {
  echo -n "Checking Linux distribution: "

  declare -A family=(
    [debian]="debian"
    [ubuntu]="debian"
    [redhatenterpriseserver]="redhat"
    [centos]="redhat"
    [redhatenterprise]="redhat"
    [rocky]="redhat"
    [alma]="redhat"
  )

  if command -v lsb_release &>/dev/null; then
    lsb_dist="$(lsb_release -i -s)"
    distro_name="${lsb_dist,,}"
    distro_version="$(

    )"
  elif [ -e /etc/redhat-release ]; then
    file_dist=$(${SED_EXEC} 's/ release [0-9].*$//; s/ linux$//i; s/ linux //ig; s/ //g' /etc/redhat-release)
    distro_name="${file_dist,,}"
    distro_version=$(${SED_EXEC} 's/^.* release \([0-9][0-9.]*\).*$/\1/' /etc/redhat-release)
  elif [ -e /etc/lsb-release ]; then
    distro_name="$(source /etc/lsb-release ; echo ${DISTRIB_ID,,})"
    distro_version="$(source /etc/lsb-release ; echo ${DISTRIB_RELEASE})"
  elif [ -e /etc/debian_version ]; then
    distro_name="debian"
    distro_version="$(cat /etc/debian_version)"
  elif [ -e /etc/os-release ] || [ -e /usr/lib/os-release ]; then
    distro_name="$(source /usr/lib/os-release; source /etc/os-release ; echo $ID)"
    distro_version="$(source /usr/lib/os-release; source /etc/os-release ; echo $VERSION_ID)"
  fi

  distro_family="${family[${distro_name}]}"
  if ! [[ ${distro_name} == "ubuntu" ]]; then
    distro_version="${distro_version%%.*}"
  fi

  if ! [[ ${distro_family} == "redhat" ]]; then
    echo_red "unsupported distribution family: ${distro_family}"
    return 1
  fi
  echo_green "${distro_name} ${distro_version}."
  return 0
}

ensure_nvme_tcp() {
  echo -n "Checking NVMe/TCP module: "
  module_loaded=$(lsmod | ${AWK_EXEC} '{print $1}' | ${GREP_EXEC} nvme_tcp)
  if ! [[ ${module_loaded} ]]; then
    echo_red "not loaded."
  else
    echo_green "loaded."
  fi

  echo -n "Checking NVMe/TCP module autoload: "

  if [ -f /etc/modules ]; then
    check_module=$(cat /etc/modules | ${GREP_EXEC} nvme-tcp)
    if [[ ${check_modukle} ]]; then
      module_persisted="/etc/modules"
    fi
  fi
  if ! [[ ${module_persisted} ]]; then
    if [ -d /etc/modules-load.d ]; then
      for file in /etc/modules-load.d/*; do
        if [[ "${file}" == "/etc/modules-load.d/*" ]]; then
          continue
        fi
        check_module=$(cat ${file} | ${GREP_EXEC} nvme-tcp)
        if [[ ${check_module} ]]; then
          module_persisted="${file}"
          break
        fi
      done
    fi
  fi

  if ! [[ ${module_persisted} ]]; then
    echo_red "not persisted - please enable autoloading for module nvme-tcp"
  else
    echo_green "ok - loaded via ${module_persisted}"
  fi
}

ensure_disk_space() {
  echo -n "Searching boot device: "
  boot_device=$(lsblk -e 7 -o path,mountpoint | ${GREP_EXEC} /$ | ${AWK_EXEC} '{print $1}')
  echo_green "${boot_device}."

  echo -n "Checking free disk space: "
  free_space=$(lsblk -e 7 -o fsavail,mountpoint | ${GREP_EXEC} /$ | ${AWK_EXEC} '{print $1}')
  free_space=$(numfmt --from=iec ${free_space})
  if [ ${free_space} -lt ${MIN_DISK_SPACE} ]; then
    human_disk_req="$(echo ${MIN_DISK_SPACE} | ${AWK_EXEC} '{print $1/1024/1024/1024}')"
    echo_red "not enough free, requires min ${human_disk_req} GB."
    return 1
  fi
  echo_green "ok."
  return 0
}

check_port_open() {
  # Returns multiple rows if found
  # 0. Target (ACCEPT | DROP | RETURN | Chain name)
  # 1. Protocol (all | tcp | udp)
  # 2. Source
  # 3. Destination
  # 4. Protocol
  # 5. Port
  echo -n "Checking port(s) $1/$2: "

  local port="$1"
  if [[ "${port}" == *-* ]]; then
    bounds=($(echo "${port}" | ${AWK_EXEC} '{gsub(/-/,"\n"); print;}'))
    #ports[${bounds[0]}]="${OPEN_PORTS[${port}]}"
    #ports[${bounds[1]}]="${OPEN_PORTS[${port}]}"
    port="${bounds[0]}"
    echo -n "(only checking ${port})... "
  fi

  local table_entry=($(${IPTABLES_EXEC} -4 -nL 2>/dev/null | ${GREP_EXEC} ACCEPT | ${GREP_EXEC} -E "${port}$" | ${GREP_EXEC} $2 | ${AWK_EXEC} '{print $1; print $2; print $4; print $5; print $6; sub(/.*:/, ""); print}'))
  if ! [[ $table_entry ]]; then
    if [[ $3 == "accept" ]]; then
      echo_yellow "warning - open but without IP or IP-range restriction!"
      return
    fi
    echo_red "closed."
    return
  fi
  if [[ "${table_entry[3]}" == '0.0.0.0/0\n' ]]; then
    echo_yellow "warning - open but without IP or IP-range restriction!"
  else
    echo_green "ok."
  fi
}

ensure_ports() {
  echo -n "Checking default Policy: "
  local default_policy=$(${IPTABLES_EXEC} -4 --list 2>/dev/null | ${GREP_EXEC} "Chain INPUT" | ${GREP_EXEC} ACCEPT)
  if ! [[ ${default_policy} ]]; then
    default_policy="drop"
    echo_green "ok - drop."
  else
    default_policy="accept"
    echo_yellow "warning - accept."
  fi

  local sortedPorts=($(printf '%s\n' "${!OPEN_PORTS[@]}" | ${SED_EXEC} -r -e 's/^ *//' -e '/^$/d' | sort -n))
  for port in "${sortedPorts[@]}"; do
    proto=${OPEN_PORTS[${port}]}
    case "${proto}" in
      "tcp")
        tcp=1
        udp=0
        ;;
      "udp")
        tcp=0
        udp=1
        ;;
      *)
        tcp=1
        udp=1
        ;;
    esac

    if [ ${tcp} -eq 1 ]; then
      check_port_open "${port}" "tcp" "${default_policy}"
    fi

    if [ ${udp} -eq 1 ]; then
      check_port_open "${port}" "udp" "${default_policy}"
    fi
  done
}

find_nvme_devices() {
  echo "Checking NVMe candidates... "
  local nvme_candidates=($(${LSPCI_EXEC} -Dnn | grep -i '\[0108\]' | awk '{print $1}'))
  local has_at_least_one_disk=0
  for pci_addr in "${nvme_candidates[@]}"; do
    echo -n " - Testing NVMe at ${pci_addr}..."
    local is_nvme_avail="$(find /sys/bus/pci/devices/${pci_addr}/ -maxdepth 1 -mindepth 1 -type d -name nvme)"
    if [[ "${is_nvme_avail}" ]]; then
      local nvme_dev_name; nvme_dev_name="$(find /sys/bus/pci/devices/${pci_addr}/nvme/ -maxdepth 1 -mindepth 1 -type d)"
      nvme_dev_name="$(basename ${nvme_dev_name})"
      local nvme_namespaces=($(find /sys/bus/pci/devices/${pci_addr}/nvme/${nvme_dev_name}/ -maxdepth 1 -mindepth 1 | grep -e "${nvme_dev_name}n[1-9][0-9]*"))
      echo "" # force line break for individual tests
      for namespace_path in "${nvme_namespaces[@]}"; do
        local namespace="$(echo ${namespace_path} | ${AWK_EXEC} -F"/" '{print $NF}')"
        echo -n "   - Testing /dev/${namespace}... "
        local has_partitions="$(find "${namespace_path}" -type d -name ${nvme_dev_name}n1p1)"
        if [[ "${has_partitions}" != "" ]]; then
          echo_red "unavailable (has partitions)."
        else
          echo_green "available."
          has_at_least_one_disk=1
        fi
      done
    else
      echo_red "unavailable (not handled by NVMe driver)"
    fi
  done

  if [ ${has_at_least_one_disk} -eq 0 ]; then
    echo_red " - No available NVMe found. A reboot may help. Disks for simplyblock cannot have partitions on them."
  fi
}

ensure_numa() {
  echo -n "Checking NUMA availability... "
  local numa_unavailable; numa_unavailable="$(dmesg | ${GREP_EXEC} -i numa | ${GREP_EXEC} 'No NUMA')"
  if [[ "${numa_unavailable}" ]]; then
    echo_green "not available."
    return
  fi

  local numa_nodes; numa_nodes=($(${LSCPU_EXEC} | ${GREP_EXEC} 'NUMA node(s)' | ${AWK_EXEC} '{print $3}'))
  if [ ${#numa_nodes[@]} -gt 1 ]; then
    echo_yellow "warning: multiple numa nodes found (${numa_nodes[@]}), ensure correct configuration"
    return
  fi
  echo_green "only one node found"
}

ensure_huge_pages() {
  echo -n "Checking huge pages... "
  local huge_pages_total="$(cat /proc/meminfo | ${GREP_EXEC} HugePages_Total | ${AWK_EXEC} '{print $2}')"
  local huge_pages_free="$(cat /proc/meminfo | ${GREP_EXEC} HugePages_Free | ${AWK_EXEC} '{print $2}')"

  if [ "${huge_pages_total}" -eq 0 ]; then
    echo_red "not configured."
  else
    if [ "${huge_pages_free}" -lt 4000 ]; then
      echo_yellow "warning: only ${huge_pages_free} are available, may not be enough."
    else
      echo_green "potentially enough huge pages available (${huge_pages_free}/${huge_pages_total})."
    fi
  fi
}

ensure_hostname() {
  echo -n "Checking hostname... "
  local hostname_ctl="$(command -v hostnamectl)"
  if [[ "${hostname_ctl}" ]]; then
    local hostname="$(${hostname_ctl} | ${GREP_EXEC} 'Static hostname' | ${AWK_EXEC} '{print $3}')"
    local transient="$(${hostname_ctl} | ${GREP_EXEC} 'Transient hostname' | ${AWK_EXEC} '{print $3}')"
    if [[ "${hostname}" == "${UNSET_HOSTNAMECTL}" ]]; then
      if [[ "${transient}" == "${UNSET_TRANSIENT_HOSTNAMECTL}" ]]; then
        echo_red "No hostname set. Please set an unique hostname."
        return
      fi

      echo_yellow "Transient one set (probably through DNS). We recommend setting a static hostname."
      return
    fi

    echo_green "Hostname set: ${hostname}"
  else
    local hostname="$(cat /etc/hostname)"
    local transient="$(hostname)"
    if [[ "${hostname}" == "" ]]; then
      if [[ "${transient}" == "${UNSET_TRANSIENT_HOSTNAME}" ]]; then
        echo_red "No hostname set. Please set an unique hostname."
        return
      fi

      echo_yellow "Transient one set (probably through DNS). We recommend setting a static hostname."
      return
    fi

    echo_green "Hostname set: ${hostname}"
  fi
}
