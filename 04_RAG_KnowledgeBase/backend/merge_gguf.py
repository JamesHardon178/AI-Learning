# -*- coding: utf-8 -*-
"""将 GGUF 分片文件（llama.cpp split 格式）真正合并为单一 GGUF 文件。
原理：
  - split 0 文件包含完整 KV 元数据 + 属于 split0 的张量信息
  - split 1+ 文件包含 split.* KV + 各自分片的张量信息
  - 合并 = 重写头部（去掉 split.* KV，追加所有分片的 tensor_info，修正 offset）+ 顺序拼接各分片数据区
"""
import struct
import shutil
import sys

ALIGN = 32

def align32(n):
    return (n + ALIGN - 1) & ~(ALIGN - 1)

def read_string(fh):
    slen = struct.unpack('<Q', fh.read(8))[0]
    return fh.read(slen).decode('utf-8')

def read_value(fh, vtype):
    """返回 (展示值, 跳过标记)。类型码见 GGUF 规范。"""
    if vtype == 0:   # uint8
        return struct.unpack('<B', fh.read(1))[0]
    if vtype == 1:   # int8
        return struct.unpack('<b', fh.read(1))[0]
    if vtype == 2:   # uint16
        return struct.unpack('<H', fh.read(2))[0]
    if vtype == 3:   # int16
        return struct.unpack('<h', fh.read(2))[0]
    if vtype == 4:   # uint32
        return struct.unpack('<I', fh.read(4))[0]
    if vtype == 5:   # int32
        return struct.unpack('<i', fh.read(4))[0]
    if vtype == 6:   # float32
        return struct.unpack('<f', fh.read(4))[0]
    if vtype == 7:   # bool
        return struct.unpack('<?', fh.read(1))[0]
    if vtype == 8:   # string
        slen = struct.unpack('<Q', fh.read(8))[0]
        return fh.read(slen).decode('utf-8')
    if vtype == 9:   # array
        atype = struct.unpack('<I', fh.read(4))[0]
        alen = struct.unpack('<Q', fh.read(8))[0]
        items = []
        for _ in range(alen):
            items.append(read_value(fh, atype))
        return items
    if vtype == 10:  # uint64
        return struct.unpack('<Q', fh.read(8))[0]
    if vtype == 11:  # int64
        return struct.unpack('<q', fh.read(8))[0]
    if vtype == 12:  # float64
        return struct.unpack('<d', fh.read(8))[0]
    raise ValueError(f'未知 KV 值类型 {vtype}')

def write_value(fh, vtype, val):
    if vtype == 0:
        fh.write(struct.pack('<B', val))
    elif vtype == 1:
        fh.write(struct.pack('<b', val))
    elif vtype == 2:
        fh.write(struct.pack('<H', val))
    elif vtype == 3:
        fh.write(struct.pack('<h', val))
    elif vtype == 4:
        fh.write(struct.pack('<I', val))
    elif vtype == 5:
        fh.write(struct.pack('<i', val))
    elif vtype == 6:
        fh.write(struct.pack('<f', val))
    elif vtype == 7:
        fh.write(struct.pack('<?', val))
    elif vtype == 8:
        b = val.encode('utf-8')
        fh.write(struct.pack('<Q', len(b)))
        fh.write(b)
    elif vtype == 9:
        atype, items = val[0], val[1]
        fh.write(struct.pack('<I', atype))
        fh.write(struct.pack('<Q', len(items)))
        for it in items:
            write_value(fh, atype, it)
    elif vtype == 10:
        fh.write(struct.pack('<Q', val))
    elif vtype == 11:
        fh.write(struct.pack('<q', val))
    elif vtype == 12:
        fh.write(struct.pack('<d', val))
    else:
        raise ValueError(f'未知 KV 值类型 {vtype}')

def parse_header(path):
    """解析 GGUF 文件头部，返回 (version, kvs, tensors, aligned_header_size, file_size)。"""
    with open(path, 'rb') as fh:
        magic = fh.read(4)
        if magic != b'GGUF':
            raise ValueError(f'{path} 不是 GGUF 文件: {magic}')
        version = struct.unpack('<I', fh.read(4))[0]
        n_tensors, n_kv = struct.unpack('<QQ', fh.read(16))
        kvs = []
        for i in range(n_kv):
            key = read_string(fh)
            vtype = struct.unpack('<I', fh.read(4))[0]
            if n_kv <= 40:
                print(f'  KV[{i}] {key[:40]} type={vtype}', flush=True)
            val = read_value(fh, vtype)
            kvs.append((key, vtype, val))
        print(f'  KV 解析完成，位置: {fh.tell()}', flush=True)
        peek = fh.read(8)
        print(f'  下一个8字节: {peek.hex()} -> slen={struct.unpack("<Q", peek)[0]}', flush=True)
        fh.seek(-8, 1)
        tensors = []
        for _ in range(n_tensors):
            name = read_string(fh)
            n_dims = struct.unpack('<I', fh.read(4))[0]
            dims = struct.unpack(f'<{n_dims}Q', fh.read(8 * n_dims))
            ttype = struct.unpack('<I', fh.read(4))[0]
            offset = struct.unpack('<Q', fh.read(8))[0]
            size = struct.unpack('<Q', fh.read(8))[0]
            tensors.append({'name': name, 'dims': dims, 'type': ttype,
                            'offset': offset, 'size': size})
        raw_end = fh.tell()
        aligned = align32(raw_end)
        fh.seek(0, 2)
        fsize = fh.tell()
    # 校验：最后一个张量是否落在数据区内
    for t in tensors[-3:]:
        if t['offset'] + t['size'] > fsize:
            print(f'  [警告] tensor {t["name"]} 越界: offset={t["offset"]} size={t["size"]} filesize={fsize}', file=sys.stderr)
    return version, kvs, tensors, aligned, fsize

def main():
    f0 = 'qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf'
    f1 = 'qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf'
    out = 'qwen2.5-7b-instruct-q4_k_m-merged.gguf'

    print('解析分片 1 (split 0)...', flush=True)
    v0, kvs0, tensors0, aligned0, size0 = parse_header(f0)
    print(f'  version={v0}, KV={len(kvs0)}, tensors={len(tensors0)}, 数据区起始={aligned0}, 文件大小={size0}', flush=True)
    print('解析分片 2 (split 1)...', flush=True)
    v1, kvs1, tensors1, aligned1, size1 = parse_header(f1)
    print(f'  version={v1}, KV={len(kvs1)}, tensors={len(tensors1)}, 数据区起始={aligned1}, 文件大小={size1}', flush=True)

    if v0 != v1:
        raise ValueError(f'两个分片版本不一致: {v0} vs {v1}')

    # 去掉 split.* KV（split0 的 KV 保留全部非 split 键）
    kept_kvs = [(k, t, v) for k, t, v in kvs0 if not k.startswith('split.')]
    removed = len(kvs0) - len(kept_kvs)
    print(f'移除 split.* KV {removed} 个，保留 {len(kept_kvs)} 个', flush=True)

    all_tensors = tensors0 + tensors1
    print(f'合并后张量总数: {len(all_tensors)}', flush=True)

    # 计算新头部大小
    def header_size(kvs, tensors):
        size = 4 + 4 + 8 + 8  # magic + version + n_tensors + n_kv
        for k, t, v in kvs:
            size += 8 + len(k.encode('utf-8')) + 4  # key
            # 值的字节数（通过序列化到内存估算太慢，直接按类型算）
            size += value_size(t, v)
        for t in tensors:
            size += 8 + len(t['name'].encode('utf-8')) + 4 + 8 * len(t['dims']) + 4 + 8 + 8
        return size

    def value_size(vtype, val):
        if vtype in (0, 1, 7):
            return 1
        if vtype in (2, 3, 4, 5):
            return 4
        if vtype == 6:
            return 4
        if vtype == 8:
            return 8 + len(val.encode('utf-8'))
        if vtype == 9:
            atype, items = val[0], val[1]
            return 4 + 8 + sum(value_size(atype, it) for it in items)
        if vtype in (10, 11):
            return 8
        if vtype == 12:
            return 8
        raise ValueError(vtype)

    new_raw_size = header_size(kept_kvs, all_tensors)
    new_aligned = align32(new_raw_size)
    print(f'新头部: raw={new_raw_size}, 对齐后={new_aligned}', flush=True)

    split0_data_size = size0 - aligned0
    split1_data_size = size1 - aligned1
    print(f'分片数据区: split0={split0_data_size} bytes, split1={split1_data_size} bytes', flush=True)

    delta = aligned0 - new_aligned
    print(f'头部偏移修正 delta={delta}', flush=True)

    # 修正 offset
    for t in tensors0:
        t['offset'] -= delta
    for t in tensors1:
        t['offset'] = (t['offset'] - aligned1) + split0_data_size - delta

    # 写新文件
    print(f'写出合并文件 {out} ...', flush=True)
    with open(out, 'wb') as w, open(f0, 'rb') as r0, open(f1, 'rb') as r1:
        w.write(b'GGUF')
        w.write(struct.pack('<I', v0))
        w.write(struct.pack('<Q', len(all_tensors)))
        w.write(struct.pack('<Q', len(kept_kvs)))
        for k, t, v in kept_kvs:
            b = k.encode('utf-8')
            w.write(struct.pack('<Q', len(b)))
            w.write(b)
            w.write(struct.pack('<I', t))
            write_value(w, t, v)
        for t in all_tensors:
            nb = t['name'].encode('utf-8')
            w.write(struct.pack('<Q', len(nb)))
            w.write(nb)
            w.write(struct.pack('<I', len(t['dims'])))
            for d in t['dims']:
                w.write(struct.pack('<Q', d))
            w.write(struct.pack('<I', t['type']))
            w.write(struct.pack('<Q', t['offset']))
            w.write(struct.pack('<Q', t['size']))
        pad = new_aligned - w.tell()
        if pad > 0:
            w.write(b'\x00' * pad)
        # 拷贝数据区
        r0.seek(aligned0)
        shutil.copyfileobj(r0, w, 1024 * 1024)
        r1.seek(aligned1)
        shutil.copyfileobj(r1, w, 1024 * 1024)

    import os
    final_size = os.path.getsize(out)
    expect = new_aligned + split0_data_size + split1_data_size
    print(f'合并完成: {final_size} bytes (期望 {expect})', flush=True)
    if final_size != expect:
        raise ValueError('文件大小与预期不符！')
    print('校验通过 ✓', flush=True)

if __name__ == '__main__':
    main()
