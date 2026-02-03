import json

file_path = "bigkinds_detailed_result.json"
max_len = 0
max_item = None
total_items = 0

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        total_items = len(data)
        for i, item in enumerate(data):
            content = item.get('DETAIL', '')
            content_len = len(content)
            if content_len > max_len:
                max_len = content_len
                max_item = i
except Exception as e:
    print(f"Error reading or processing file: {e}")

print(f"Total number of items: {total_items}")
print(f"Maximum content length found: {max_len} characters")
if max_item is not None:
    print(f"Item with max length is at index: {max_item}")

# A rough approximation: 1 token ~= 4 characters
print(f"Approximate max tokens in a single document: {max_len / 4}")
