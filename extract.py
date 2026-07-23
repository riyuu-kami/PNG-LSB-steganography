import random
import zlib
import hashlib
from embed import unfilter_scanlines

def read_png_signature(filename):
    with open(filename, 'rb') as png_file:
        signature = png_file.read(8)
        if signature != b'\x89PNG\r\n\x1A\n':
            raise ValueError("Not a valid PNG file")

def extract_png_info(filename):
    width, height = None, None
    idat_data = b''

    with open(filename, 'rb') as png_file:
        png_file.read(8)

        while True:
            length_bytes = png_file.read(4)
            if not length_bytes:
                break
            length = int.from_bytes(length_bytes, 'big')
            chunk_type = png_file.read(4)
            chunk_data = png_file.read(length)
            png_file.read(4) 
            if chunk_type == b'IHDR':
                width = int.from_bytes(chunk_data[0:4], 'big')
                height = int.from_bytes(chunk_data[4:8], 'big')
            elif chunk_type == b'IDAT':
                idat_data += chunk_data

    if width is None or height is None:
        raise ValueError("IHDR chunk not found or dimensions not available.")

    return width, height, idat_data

def decompress_idat_data(idat_data):
    return zlib.decompress(idat_data)

def extract_embedded_file(raw_pixels, password):
    # Hash the password to get the exact same seed used during embedding
    seed = int(hashlib.sha256(password.encode()).hexdigest()[:16], 16)
    random.seed(seed)
    total_pixels = len(raw_pixels)

    # FIX: Generate the identical full sequence of indices
    all_indices = random.sample(range(total_pixels), total_pixels)

    # extract length bits indices (the first 32 bits of the sequence)
    length_indices = all_indices[:32]
    length_bits = [str(raw_pixels[idx] & 1) for idx in length_indices]
    file_length = int(''.join(length_bits), 2)
    
    # extract bits for file bytes (skipping the first 32 used for length)
    data_indices = all_indices[32:32 + file_length * 8]
    data_bits = []
    for idx in data_indices:
        data_bits.append(str(raw_pixels[idx] & 1))

    # convert bits to bytes
    file_bytes = bytearray()
    for i in range(0, len(data_bits), 8):
        byte_bits = data_bits[i:i+8]
        if len(byte_bits) < 8:
            break
        file_bytes.append(int(''.join(byte_bits), 2))

    return bytes(file_bytes)


def main():
    input_filename = ''
    output_file = ''
    password = ''

    try:
        read_png_signature(input_filename)
        width, height, idat_chunks = extract_png_info(input_filename)
        decompressed_data = decompress_idat_data(idat_chunks)
        raw_pixels = unfilter_scanlines(decompressed_data, width, height, 3)

        extracted_file_bytes = extract_embedded_file(raw_pixels, password)

        with open(output_file, 'wb') as f:
            f.write(extracted_file_bytes)

        print(f"Extracted file saved as: {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
