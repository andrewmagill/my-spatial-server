import mmap

bundle_file_path = r"files/R0480C0380.bundle"

with open(bundle_file_path, "r+b") as f:
    # memory-map the file, size 0 means whole file
    mm = mmap.mmap(f.fileno(), 0)

    png_header_string = "\211PNG\r\n\032\n"
    png_end_string = "IEND"

    begin_read = 0
    end_read = 0

    count = 0

    # try not to fill up hd
    while count < 2000:

        begin_png = mm.find(png_header_string, begin_read)

        if begin_png < 0:
            break

        begin_read = begin_png

        end_png = mm.find(png_end_string, begin_read)
        if end_png < 0:
            break

        end_read = end_png + len(png_end_string)

        count += 1
        output_file = open("tile_%i.png" % count, 'wb')
        output_file.write(mm[begin_read:end_read])
        output_file.close()

        begin_read = end_read

    # close the map
    mm.close()
