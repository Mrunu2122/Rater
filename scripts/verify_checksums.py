import json
import hashlib
import os
import sys

def verify():
    manifest_path = os.path.join(os.path.dirname(__file__), "..", "data", "bundle", "MANIFEST.json")
    if not os.path.exists(manifest_path):
        manifest_path = os.path.join(os.path.dirname(__file__), "..", "MANIFEST.json")
    
    if not os.path.exists(manifest_path):
        print(f"Error: MANIFEST.json not found at {manifest_path}", file=sys.stderr)
        sys.exit(1)
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    base_dir = os.path.abspath(os.path.join(os.path.dirname(manifest_path), ".."))
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    all_ok = True
    print("=" * 60)
    print("VERIFYING SHA-256 CHECKSUMS FROM MANIFEST.JSON")
    print("=" * 60)
    
    for item in manifest.get("files", []):
        rel_path = item["path"]
        expected_sha = item["sha256"]
        expected_bytes = item["bytes"]
        
        # If checking bundle files, prioritize data/bundle/ so root project files (like updated README.md) don't collide
        candidates = [
            os.path.join(root_dir, "data", "bundle", rel_path.replace("/", os.sep)),
            os.path.join(root_dir, rel_path.replace("/", os.sep)),
            os.path.join(root_dir, "data", rel_path.replace("sample-policies", "samples").replace("/", os.sep))
        ]
        
        target_path = None
        for cand in candidates:
            if os.path.exists(cand):
                target_path = cand
                break
                
        if not target_path:
            print(f"MISSING: {rel_path}", file=sys.stderr)
            all_ok = False
            continue
            
        actual_bytes = os.path.getsize(target_path)
        hasher = hashlib.sha256()
        with open(target_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        actual_sha = hasher.hexdigest()
        
        if actual_bytes != expected_bytes or actual_sha != expected_sha:
            print(f"FAIL: {rel_path} (bytes: {actual_bytes} vs {expected_bytes}, sha: {actual_sha} vs {expected_sha})", file=sys.stderr)
            all_ok = False
        else:
            print(f"OK:   {rel_path:<60} [{actual_bytes} bytes]")
            
    print("=" * 60)
    if all_ok:
        print("ALL BUNDLE FILES VERIFIED SUCCESSFULLY.")
    else:
        print("VERIFICATION FAILED FOR ONE OR MORE FILES.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    verify()
