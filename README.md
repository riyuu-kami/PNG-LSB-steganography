# steganography
This project enables embedding and extracting files within PNG images by manipulating the least significant bits of pixel data. It handles the PNG filtering methods used during compression { None, Sub, Up, Average, and Paeth filters } by implementing their corresponding unfiltering algorithms to accurately reconstruct raw pixel data. Additionally, it secures the hidden file by using a password-derived seed to randomly scatter the embedded bits across the image, ensuring extraction requires the correct key.

## References

[PNG Filters Specification](https://www.w3.org/TR/PNG-Filters.html)
