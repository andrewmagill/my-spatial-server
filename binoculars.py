import mmap, struct

bundle_file_path = r"files/R0480C0380.bundle"

with open(bundle_file_path, "r+b") as f:
    # memory-map the file, size 0 means whole file
    mm = mmap.mmap(f.fileno(), 0)

    png_header_string = "\211PNG\r\n\032\n"
    begin_read = 0
    count = 0

    # try not to fill up hd
    while count < 2000:

        begin_read = mm.find(png_header_string, begin_read)

        if begin_read < 0:
            break

        size = struct.unpack('i',mm[begin_read - 4:begin_read])[0]
        end_read = begin_read + size

        count += 1
        output_file = open("tile_%i.png" % count, 'wb')
        output_file.write(mm[begin_read:end_read])
        output_file.close()

        begin_read = end_read

    # close the map
    mm.close()
