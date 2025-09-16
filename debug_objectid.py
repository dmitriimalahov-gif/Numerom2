#!/usr/bin/env python3
import requests
import json

# Get auth token
auth_response = requests.post('https://numerology-fix.preview.emergentagent.com/api/auth/login', json={
    'email': 'dmitrii.malahov@gmail.com',
    'password': '756bvy67H'
})

if auth_response.status_code == 200:
    token = auth_response.json()['access_token']
    
    # Test admin lessons
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get('https://numerology-fix.preview.emergentagent.com/api/admin/lessons', headers=headers)
    
    if response.status_code == 200:
        content = response.text
        print("Raw response length:", len(content))
        
        # Find all _id occurrences
        import re
        matches = list(re.finditer(r'"_id"[^,}]*', content))
        print(f"Found {len(matches)} _id occurrences")
        
        for i, match in enumerate(matches[:5]):  # Show first 5
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            context = content[start:end]
            print(f"\nMatch {i+1}:")
            print(f"Context: ...{context}...")
            
        # Also check the parsed JSON
        try:
            data = response.json()
            print(f"\nParsed JSON has {len(data)} lessons")
            
            def find_id_fields(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key == '_id':
                            print(f"Found _id at path: {path}.{key} = {value}")
                        else:
                            find_id_fields(value, f"{path}.{key}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        find_id_fields(item, f"{path}[{i}]")
            
            find_id_fields(data, "root")
            
        except Exception as e:
            print(f"Error parsing JSON: {e}")
    else:
        print(f"Error getting lessons: {response.status_code}")
else:
    print(f"Auth failed: {auth_response.status_code}")