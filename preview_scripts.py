import json

with open("output/scripts/ad_scripts.json", encoding="utf-8") as f:
    d = json.load(f)

for s in d["scripts"]:
    print(f"\n{'='*60}")
    print(f"SCRIPT TYPE {s['type']} — {s['name']}")
    print(f"{'='*60}")
    print(f"VISUAL HOOK:  {s.get('visual_hook', '')}")
    print(f"HOOK EMOTION: {s.get('hook_emotion', '')}")
    print(f"CTA:          {s.get('cta', '')}")
    print(f"\nVOICEOVER (first 600 chars):")
    print(s.get("voiceover", "")[:600])
    print(f"\nSTORYBOARD SCENES: {len(s.get('storyboard', []))}")
    for scene in s.get("storyboard", [])[:2]:
        print(f"  Scene {scene.get('scene')}: [{scene.get('duration')}s] {scene.get('visual', '')[:80]}...")
