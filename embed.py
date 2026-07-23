import zlib
import random
import hashlib

def paeth_predictor(a, b, c):
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    elif pb <= pc:
        return b
    else:
        return c

def unfilter_scanlines(data, width, height, bpp=3):
    stride = width * bpp
    result = bytearray()
    i = 0
    for f in range(height):
        filter_type = data[i]
        i += 1
        scanline = data[i:i+stride]
        i += stride
        recon = bytearray(scanline)
        if filter_type == 0:
            pass
        elif filter_type == 1:
            for x in range(bpp, stride):
                recon[x] = (recon[x] + recon[x - bpp]) & 0xFF
        elif filter_type == 2:
            prev = result[-stride:] if len(result) >= stride else bytearray(stride)
            for x in range(stride):
                recon[x] = (recon[x] + prev[x]) & 0xFF
        elif filter_type == 3:
            prev = result[-stride:] if len(result) >= stride else bytearray(stride)
            for x in range(stride):
                left = recon[x - bpp] if x >= bpp else 0
                up = prev[x]
                recon[x] = (recon[x] + ((left + up) >> 1)) & 0xFF
        elif filter_type == 4:
            prev = result[-stride:] if len(result) >= stride else bytearray(stride)
            for x in range(stride):
                left = recon[x - bpp] if x >= bpp else 0
                up = prev[x]
                up_left = prev[x - bpp] if x >= bpp else 0
                paeth = paeth_predictor(left, up, up_left)
                recon[x] = (recon[x] + paeth) & 0xFF
        else:
            raise ValueError(f"Unknown filter type: {filter_type}")
        result.extend(recon)
    return bytes(result)

def filter_scanlines(raw_data, width, height, bpp=3):
    stride = width * bpp
    filtered = bytearray()
    for y in range(height):
        scanline = raw_data[y*stride:(y+1)*stride]
        filtered.append(0)  # filter type 0 = None
        filtered.extend(scanline)
    return bytes(filtered)

def embed_file_in_raw_pixels(raw_pixels, file_bytes, password):

    seed = int(hashlib.sha256(password.encode()).hexdigest()[:16], 16)
    random.seed(seed)
    
    file_length = len(file_bytes)
    length_bytes = file_length.to_bytes(4, 'big')
    data_to_embed = length_bytes + file_bytes

    data_bits = ''.join(format(byte, '08b') for byte in data_to_embed)

    pixel_array = bytearray(raw_pixels)
    total_pixels = len(pixel_array)
    if len(data_bits) > total_pixels:
        raise ValueError("File too large to embed in image pixels.")

    all_indices = random.sample(range(total_pixels), total_pixels)
    indices = all_indices[:len(data_bits)]

    for i, bit in enumerate(data_bits):
        idx = indices[i]
        pixel_array[idx] = (pixel_array[idx] & ~1) | int(bit)

    return bytes(pixel_array)

def save_png(filename, width, height, raw_pixels):
    compressed = zlib.compress(filter_scanlines(raw_pixels, width, height, 3))
    with open(filename, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1A\n')

        ihdr_data = (
            width.to_bytes(4, 'big') +
            height.to_bytes(4, 'big') +
            b'\x08' +
            b'\x02' +
            b'\x00' +
            b'\x00' +
            b'\x00'
        )
        f.write(len(ihdr_data).to_bytes(4, 'big'))
        f.write(b'IHDR')
        f.write(ihdr_data)
        f.write(zlib.crc32(b'IHDR' + ihdr_data).to_bytes(4, 'big'))

        f.write(len(compressed).to_bytes(4, 'big'))
        f.write(b'IDAT')
        f.write(compressed)
        f.write(zlib.crc32(b'IDAT' + compressed).to_bytes(4, 'big'))

        f.write(b'\x00\x00\x00\x00IEND')
        f.write(b'\xae\x42\x60\x82')

def main():
    input_filename = ''
    output_filename = ''
    file_to_embed = ''
    password = ''

    with open(input_filename, 'rb') as f:
        f.read(8)

        width = None
        height = None
        idat_data = b''

        while True:
            length_bytes = f.read(4)
            if not length_bytes:
                break
            length = int.from_bytes(length_bytes, 'big')
            chunk_type = f.read(4)
            chunk_data = f.read(length)
            f.read(4)

            if chunk_type == b'IHDR':
                width = int.from_bytes(chunk_data[0:4], 'big')
                height = int.from_bytes(chunk_data[4:8], 'big')
            elif chunk_type == b'IDAT':
                idat_data += chunk_data

        if width is None or height is None:
            raise ValueError("No IHDR chunk found")

        decompressed = zlib.decompress(idat_data)
        raw_pixels = unfilter_scanlines(decompressed, width, height, 3)

    with open(file_to_embed, 'rb') as f:
        file_bytes = f.read()

    embedded_pixels = embed_file_in_raw_pixels(raw_pixels, file_bytes, password)
    save_png(output_filename, width, height, embedded_pixels)
    print("Embedding complete.")

if __name__ == '__main__':
    main()
