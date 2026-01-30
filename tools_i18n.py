import os
import re
import struct

# --- 1. POT Generator ---

def extract_strings(scan_dir):
    """Simple regex based extractor for _('...') and _("...") strings."""
    # Matches _("text") or _('text')
    pattern = re.compile(r'_\s*\((?P<quote>["\'])(?P<string>.*?)(?P=quote)\)')
    str_list = set()
    
    # Dirs to exclude
    exclude_dirs = {'.git', '.venv', 'venv', 'env', '__pycache__', 'build', 'dist', 'locales', '.idea', '.vscode'}
    
    for root, dirs, files in os.walk(scan_dir):
        # Modify dirs in-place to skip excluded ones
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith(".py") and file != "tools_i18n.py":
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        matches = pattern.findall(content)
                        for _, s in matches:
                            str_list.add(s)
                except Exception as e:
                    print(f"Skipping {path}: {e}")
                    
    return sorted(list(str_list))

def write_pot(strings, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# PDF Converter Translation Template\n")
        f.write("# Copyright (C) 2026 Technology Entertainment Studio\n")
        f.write('msgid ""\n')
        f.write('msgstr ""\n')
        f.write('"Content-Type: text/plain; charset=UTF-8\\n"\n')
        f.write('"Content-Transfer-Encoding: 8bit\\n"\n\n')
        
        for s in strings:
            # Escape newlines and quotes if needed (basic handling)
            clean_s = s.replace('\n', '\\n').replace('"', '\\"')
            f.write(f'msgid "{clean_s}"\n')
            f.write('msgstr ""\n\n')
    print(f"Generated {output_file} with {len(strings)} strings.")

# --- 2. MO Compiler (Simple) ---

def msgfmt(po_file, mo_file):
    """Compiles a PO file into an MO file."""
    messages = {}
    
    # Improved PO parser
    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    current_msgid = None
    current_msgstr = None
    in_msgid = False
    in_msgstr = False
    
    # Temporary buffer for multiline
    buffer_id = []
    buffer_str = []
    
    def flush_entry():
        nonlocal current_msgid, current_msgstr
        if buffer_id:
            mid = "".join(buffer_id)
            mstr = "".join(buffer_str)
            if mid == "" or mstr: # Allow empty msgid (header) and empty msgstr (untranslated)
                 messages[mid] = mstr
        buffer_id.clear()
        buffer_str.clear()

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        if line.startswith('msgid "'):
            # New entry starts, flush previous
            flush_entry()
            
            in_msgid = True
            in_msgstr = False
            # Extract content: msgid "content" -> content
            content = line[7:-1]
            buffer_id.append(content)
            
        elif line.startswith('msgstr "'):
            in_msgid = False
            in_msgstr = True
            content = line[8:-1]
            buffer_str.append(content)
            
        elif line.startswith('"'):
            # Continuation
            content = line[1:-1]
            if in_msgid:
                buffer_id.append(content)
            elif in_msgstr:
                buffer_str.append(content)
    
    # Flush last entry
    flush_entry()
    
    # Process escapes
    final_messages = {}
    for k, v in messages.items():
        k_clean = k.replace('\\n', '\n').replace('\\"', '"').replace('\\t', '\t')
        v_clean = v.replace('\\n', '\n').replace('\\"', '"').replace('\\t', '\t')
        final_messages[k_clean] = v_clean
        
    messages = final_messages
    
    # Ensure Header exists if not parsed correctly? 
    # Usually header is msgid "" msgstr "Content-Type..."
    # The loop should catch it now.
    
    # ... Write binary ...
    keys = sorted(messages.keys())
    offsets = []
    ids = b''
    strs = b''
    
    for k in keys:
        v = messages[k]
        # ids
        keys_offset = len(ids)
        ids += k.encode('utf-8') + b'\0'
        
        # strs
        # strs_offset = len(strs) # calculated later
        strs += v.encode('utf-8') + b'\0'
    
    with open(mo_file, 'wb') as f:
        # Magic
        f.write(struct.pack('<I', 0x950412de))
        # Revision
        f.write(struct.pack('<I', 0))
        # Count
        f.write(struct.pack('<I', len(keys)))
        
        # Offsets table loc (header size 28 bytes)
        k_table_offset = 28
        v_table_offset = 28 + (len(keys) * 8)
        
        f.write(struct.pack('<I', k_table_offset))
        f.write(struct.pack('<I', v_table_offset))
        f.write(struct.pack('<I', 0)) # Hash table (unsused)
        f.write(struct.pack('<I', 0)) # Hash table loc
        
        # Key Table
        ids_start = 28 + (len(keys) * 16) # Header + (Count * (2 ints for K + 2 ints for V)) WRONG
        # The structure is:
        # Header (28 bytes)
        # Offset Table O (8 bytes * N) -> points to IDs
        # Offset Table T (8 bytes * N) -> points to STRs
        # IDs data
        # STRs data
        
        o_table_size = len(keys) * 8
        ids_start_offset = 28 + o_table_size + o_table_size
        
        current_id_offset = ids_start_offset
        for k in keys:
            l = len(k.encode('utf-8')) # +1 for null included in encoding? No, manually added
            f.write(struct.pack('<II', l, current_id_offset))
            current_id_offset += l + 1
            
        # Value Table
        strs_start_offset = current_id_offset
        current_str_offset = strs_start_offset
        
        for k in keys:
            v = messages[k]
            l = len(v.encode('utf-8'))
            f.write(struct.pack('<II', l, current_str_offset))
            current_str_offset += l + 1
            
        # Data
        f.write(ids)
        f.write(strs)
        
    print(f"Compiled {po_file} -> {mo_file}")

if __name__ == "__main__":
    # Generate POT
    extract_strings(".") # Current dir
    if os.path.exists("locales"):
        write_pot(extract_strings("."), "locales/messages.pot")
    
    # Compile example VI if exists
    vi_po = "locales/vi/LC_MESSAGES/messages.po"
    vi_mo = "locales/vi/LC_MESSAGES/messages.mo"
    if os.path.exists(vi_po):
        msgfmt(vi_po, vi_mo)
