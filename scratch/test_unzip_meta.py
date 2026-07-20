import requests
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

r = requests.get('https://www.prydwen.gg/zenless/shiyu-defense', headers=headers)
html = r.text

payloads = []
for match in re.finditer(r'self\.__next_f\.push\(\[\d+,\s*"(.*?)"\]\)', html):
    payloads.append(match.group(1))
    
combined = "".join(payloads).replace('\\\\', '\\')
unescaped = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), combined)
unescaped = unescaped.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")

idx = unescaped.find('"teams":{')
if idx != -1:
    start_pos = idx + len('"teams":')
    bracket_count = 0
    end_pos = start_pos
    for i in range(start_pos, len(unescaped)):
        if unescaped[i] == '{':
            bracket_count += 1
        elif unescaped[i] == '}':
            bracket_count -= 1
            if bracket_count == 0:
                end_pos = i + 1
                break
    teams_obj = json.loads(unescaped[start_pos:end_pos])
    print("all teams count:", len(teams_obj.get("all", [])))
    print("top 3 all teams:")
    for team in teams_obj.get("all", [])[:3]:
        print(team)
