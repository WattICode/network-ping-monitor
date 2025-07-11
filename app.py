from flask import Flask, render_template, request, jsonify
import subprocess
import re
import yaml
import concurrent.futures
import time
import platform
import os

app = Flask(__name__)

def load_config():
    """Load host configuration from YAML file"""
    config_path = os.path.join(os.path.dirname(__file__), 'hosts.yaml')
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        # Return sample config if file doesn't exist
        return {
            'groups': {
                'office_floor_1': [
                    {'ip': '192.168.1.10', 'name': 'Reception Desk'},
                    {'ip': '192.168.1.11', 'name': 'Conference Room A'}
                ],
                'office_floor_2': [
                    {'ip': '192.168.1.20', 'name': 'HR Office'},
                    {'ip': '192.168.1.21', 'name': 'IT Support'}
                ]
            }
        }

def normalize_host_entry(host_entry):
    """
    Normalize host entry to support both old (string) and new (dict) formats
    Returns tuple: (ip, name)
    """
    if isinstance(host_entry, str):
        # Old format: just IP address
        return host_entry, host_entry
    elif isinstance(host_entry, dict):
        # New format: {ip: "x.x.x.x", name: "Friendly Name"}
        ip = host_entry.get('ip', '')
        name = host_entry.get('name', ip)
        return ip, name
    else:
        # Fallback
        return str(host_entry), str(host_entry)

def ping_host(host, name=None, count=4, timeout=5):
    """
    Ping a single host and return results
    """
    if name is None:
        name = host
    
    # Determine ping command based on OS
    if platform.system().lower() == 'windows':
        cmd = ['ping', '-n', str(count), '-w', str(timeout * 1000), host]
    else:
        cmd = ['ping', '-c', str(count), '-W', str(timeout), host]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
        
        if result.returncode == 0:
            parsed_result = parse_ping_output(result.stdout, host)
            parsed_result['name'] = name
            return parsed_result
        else:
            return {
                'host': host,
                'name': name,
                'status': 'unreachable',
                'packet_loss': 100,
                'avg_latency': 0,
                'min_latency': 0,
                'max_latency': 0,
                'quality': 'poor',
                'error': 'Host unreachable'
            }
    except subprocess.TimeoutExpired:
        return {
            'host': host,
            'name': name,
            'status': 'timeout',
            'packet_loss': 100,
            'avg_latency': 0,
            'min_latency': 0,
            'max_latency': 0,
            'quality': 'poor',
            'error': 'Ping timeout'
        }
    except Exception as e:
        return {
            'host': host,
            'name': name,
            'status': 'error',
            'packet_loss': 100,
            'avg_latency': 0,
            'min_latency': 0,
            'max_latency': 0,
            'quality': 'poor',
            'error': str(e)
        }

def parse_ping_output(output, host):
    """
    Parse ping command output to extract statistics
    """
    try:
        # Extract packet loss percentage
        loss_match = re.search(r'(\d+(?:\.\d+)?)%.*loss', output)
        packet_loss = float(loss_match.group(1)) if loss_match else 0
        
        # Extract latency statistics (works for both Linux and Windows)
        # Linux format: "min/avg/max/mdev = 1.234/5.678/9.012/1.234 ms"
        # Windows format: "Minimum = 1ms, Maximum = 9ms, Average = 5ms"
        
        if platform.system().lower() == 'windows':
            min_match = re.search(r'Minimum = (\d+)ms', output)
            max_match = re.search(r'Maximum = (\d+)ms', output)
            avg_match = re.search(r'Average = (\d+)ms', output)
            
            min_latency = float(min_match.group(1)) if min_match else 0
            max_latency = float(max_match.group(1)) if max_match else 0
            avg_latency = float(avg_match.group(1)) if avg_match else 0
        else:
            # Linux/Unix format
            stats_match = re.search(r'min/avg/max/(?:mdev|stddev) = ([\d.]+)/([\d.]+)/([\d.]+)', output)
            if stats_match:
                min_latency = float(stats_match.group(1))
                avg_latency = float(stats_match.group(2))
                max_latency = float(stats_match.group(3))
            else:
                min_latency = avg_latency = max_latency = 0
        
        # Determine connection quality based on packet loss
        if packet_loss == 0:
            quality = 'good'
        elif packet_loss <= 20:
            quality = 'fair'
        else:
            quality = 'poor'
        
        return {
            'host': host,
            'status': 'reachable',
            'packet_loss': packet_loss,
            'avg_latency': avg_latency,
            'min_latency': min_latency,
            'max_latency': max_latency,
            'quality': quality,
            'error': None
        }
    
    except Exception as e:
        return {
            'host': host,
            'status': 'error',
            'packet_loss': 100,
            'avg_latency': 0,
            'min_latency': 0,
            'max_latency': 0,
            'quality': 'poor',
            'error': f'Parse error: {str(e)}'
        }

def ping_hosts_concurrent(host_data_list, max_workers=10):
    """
    Ping multiple hosts concurrently
    host_data_list: list of tuples (ip, name, group)
    """
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all ping tasks
        future_to_host = {
            executor.submit(ping_host, ip, name): (ip, name, group) 
            for ip, name, group in host_data_list
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_host):
            ip, name, group = future_to_host[future]
            try:
                result = future.result()
                result['group'] = group
                results.append(result)
            except Exception as e:
                # Handle any exceptions that occurred during ping
                results.append({
                    'host': ip,
                    'name': name,
                    'group': group,
                    'status': 'error',
                    'packet_loss': 100,
                    'avg_latency': 0,
                    'min_latency': 0,
                    'max_latency': 0,
                    'quality': 'poor',
                    'error': f'Execution error: {str(e)}'
                })
    
    return results

@app.route('/')
def index():
    """Main page with group selection form"""
    config = load_config()
    groups = config.get('groups', {})
    
    # Calculate host counts for display
    group_info = {}
    for group_name, hosts in groups.items():
        group_info[group_name] = len(hosts)
    
    return render_template('index.html', groups=group_info)

@app.route('/ping', methods=['POST'])
def ping_selected_hosts():
    """Ping selected groups of hosts"""
    config = load_config()
    groups = config.get('groups', {})
    
    selected_groups = request.json.get('groups', [])
    
    # Collect all hosts from selected groups
    host_data_list = []  # List of tuples: (ip, name, group)
    
    if 'all' in selected_groups:
        # Include all hosts from all groups
        for group_name, hosts in groups.items():
            for host_entry in hosts:
                ip, name = normalize_host_entry(host_entry)
                host_data_list.append((ip, name, group_name))
    else:
        # Include only selected groups
        for group_name in selected_groups:
            if group_name in groups:
                for host_entry in groups[group_name]:
                    ip, name = normalize_host_entry(host_entry)
                    host_data_list.append((ip, name, group_name))
    
    if not host_data_list:
        return jsonify({'error': 'No hosts selected'}), 400
    
    # Ping all selected hosts
    start_time = time.time()
    results = ping_hosts_concurrent(host_data_list)
    end_time = time.time()
    
    # Sort results by group, then by name
    results.sort(key=lambda x: (x['group'], x['name']))
    
    return jsonify({
        'results': results,
        'total_time': round(end_time - start_time, 2),
        'total_hosts': len(results)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
