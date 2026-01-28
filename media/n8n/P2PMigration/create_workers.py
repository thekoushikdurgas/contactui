import json
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Read Worker 1 as template
with open('Worker 1.json', 'r', encoding='utf-8') as f:
    template = json.load(f)

# Create workers 2-10
for worker_num in range(2, 11):
    # Deep copy the template
    worker_data = json.loads(json.dumps(template))
    
    # Update workflow-level properties
    worker_data['name'] = f'Worker {worker_num}'
    worker_data['versionId'] = f'worker-{worker_num}-v1'
    worker_data['id'] = f'p2p-worker-{worker_num}'
    
    # Update all node IDs
    for node in worker_data['nodes']:
        # Replace 001 with worker number padded to 3 digits
        node['id'] = node['id'].replace('001', f'{worker_num:03d}')
    
    # Write the file
    filename = f'Worker {worker_num}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(worker_data, f, indent=2, ensure_ascii=False)
    
    print(f'Created {filename}')

print('All workers created successfully!')

