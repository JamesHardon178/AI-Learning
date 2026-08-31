"""
Merge split GGUF files using the official gguf package's GGUFReader/GGUFWriter.
Handles scalars, strings, and arrays correctly.
"""
import sys
import os
import numpy as np
from gguf import GGUFReader, GGUFWriter, GGUFValueType, GGMLQuantizationType

SPLIT_DIR = r'D:\Desktop\AI-Learning\04_RAG_KnowledgeBase\backend\.tmp_models'
PATH1 = os.path.join(SPLIT_DIR, 'qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf')
PATH2 = os.path.join(SPLIT_DIR, 'qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf')
OUTPUT = os.path.join(SPLIT_DIR, 'qwen2.5-7b-instruct-q4_k_m-merged.gguf')

print("Reading split files...", flush=True)
r1 = GGUFReader(PATH1)
r2 = GGUFReader(PATH2)
print(f"  Split 1: {len(r1.tensors)} tensors", flush=True)
print(f"  Split 2: {len(r2.tensors)} tensors", flush=True)
total_tensors = len(r1.tensors) + len(r2.tensors)
print(f"  Total: {total_tensors} tensors", flush=True)

def extract_scalar(field):
    """Extract a scalar value from a ReaderField."""
    idx = field.data[-1]
    return field.parts[idx][0]

def extract_string(field):
    """Extract a string value from a ReaderField."""
    idx = field.data[-1]
    return bytes(field.parts[idx].tolist()).decode('utf-8', errors='replace')

def extract_array(field):
    """Extract an array (list) from a ReaderField."""
    elem_type = field.types[1] if len(field.types) > 1 else None
    result = []
    for i, idx in enumerate(field.data):
        p = field.parts[idx]
        if elem_type == GGUFValueType.STRING:
            result.append(bytes(p.tolist()).decode('utf-8', errors='replace'))
        else:
            result.append(int(p[0]) if p.dtype.kind in ('i', 'u') else float(p[0]))
        if i % 20000 == 0 and i > 0:
            print(f"    ... {i} elements extracted", flush=True)
    return result

# Get architecture
arch = extract_string(r1.fields['general.architecture'])
print(f"Architecture: {arch}", flush=True)

# Create writer with temp file support for large data
print("Creating GGUFWriter...", flush=True)
writer = GGUFWriter(OUTPUT, arch=arch, use_temp_file=True)

# Copy all non-split KV metadata from split 0
print("Copying KV metadata...", flush=True)
scalar_adders = {
    GGUFValueType.UINT8: writer.add_uint8,
    GGUFValueType.INT8: writer.add_int8,
    GGUFValueType.UINT16: writer.add_uint16,
    GGUFValueType.INT16: writer.add_int16,
    GGUFValueType.UINT32: writer.add_uint32,
    GGUFValueType.INT32: writer.add_int32,
    GGUFValueType.UINT64: writer.add_uint64,
    GGUFValueType.INT64: writer.add_int64,
    GGUFValueType.FLOAT32: writer.add_float32,
    GGUFValueType.FLOAT64: writer.add_float64,
    GGUFValueType.BOOL: writer.add_bool,
}

for key in sorted(r1.fields.keys()):
    if key.startswith('split.'):
        print(f"  Skipping split field: {key}", flush=True)
        continue
    if key in ('GGUF.tensor_count', 'GGUF.kv_count', 'GGUF.version'):
        continue  # Writer handles these internally

    field = r1.fields[key]
    vtype = field.types[0]

    try:
        if vtype == GGUFValueType.STRING:
            val = extract_string(field)
            writer.add_string(key, val)
            if len(val) < 60:
                print(f"  {key} = {val!r}", flush=True)
            else:
                print(f"  {key} = {val[:60]!r}... ({len(val)} chars)", flush=True)
        elif vtype == GGUFValueType.ARRAY:
            print(f"  {key} (array, {len(field.data)} elements, elem_type={field.types[1]})", flush=True)
            arr = extract_array(field)
            writer.add_array(key, arr)
        elif vtype in scalar_adders:
            val = int(extract_scalar(field)) if field.types[0] not in (GGUFValueType.FLOAT32, GGUFValueType.FLOAT64) else float(extract_scalar(field))
            scalar_adders[vtype](key, val)
            print(f"  {key} = {val}", flush=True)
        else:
            print(f"  WARNING: Unsupported type {vtype} for key {key}", flush=True)
    except Exception as e:
        print(f"  ERROR adding {key}: {e}", flush=True)

# Add all tensors from both splits
print(f"\nAdding {len(r1.tensors)} tensors from split 1...", flush=True)
for i, t in enumerate(r1.tensors):
    if i % 50 == 0:
        print(f"  [{i}/{len(r1.tensors)}] {t.name}...", flush=True)
    # t.data is a numpy view (uint8, raw quantized bytes, byte shape like (152064, 2016))
    # t.tensor_type is the GGMLQuantizationType enum
    # Don't pass raw_shape - let writer use t.data.shape (byte shape) and convert via raw_dtype
    writer.add_tensor(t.name, t.data, raw_dtype=t.tensor_type)

print(f"Adding {len(r2.tensors)} tensors from split 2...", flush=True)
for i, t in enumerate(r2.tensors):
    if i % 20 == 0:
        print(f"  [{i}/{len(r2.tensors)}] {t.name}...", flush=True)
    writer.add_tensor(t.name, t.data, raw_dtype=t.tensor_type)

# Write to file
print("\nWriting header...", flush=True)
writer.write_header_to_file()
print("Writing KV data...", flush=True)
writer.write_kv_data_to_file()
print(f"Writing {total_tensors} tensors ({4.3:.1f}GB data, this takes a few minutes)...", flush=True)
writer.write_tensors_to_file(progress=True)
print("Closing writer...", flush=True)
writer.close()

# Verify
out_size = os.path.getsize(OUTPUT)
print(f"\n=== DONE ===", flush=True)
print(f"Output: {OUTPUT}", flush=True)
print(f"Size: {out_size:,} bytes ({out_size/1024**3:.2f} GB)", flush=True)
