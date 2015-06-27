import os, mmap, re, struct

class Tile(object):
    """Represents an image tile found in a bundle file"""

    def __init__(self, row, column, position, path):
        """Constructor requires 4 parameters:

        row:      The row in which the tile will be displayed.
        column:   The column in which the tile will be displayed.
        position: The position of the first byte representing the image
                  in the bundle file.
        path:     The path to the bun.dle file
        """
        self.row = row
        self.column = column
        self.position = position
        self.path = path.replace('.bundlx','.bundle')

    def image(self):
        """Reads the bundle file starting at the tile's intended
        position, return an image (only PNG at the moment) if found.
        """

        try:
            file = open(self.path, "r+b")
        #except FileNotFoundError as e:
        #    raise e
        except (IOError, OSError) as e:
            raise e
        except Exception as e:
            raise e

        mm = mmap.mmap(file.fileno(), 0)

        png_header_string = "\211PNG\r\n\032\n"

        begin_read = mm.find(png_header_string, self.position)

        if begin_read > self.position + 5:
            #raise Exception("Image does not exist")
            return
        elif begin_read < self.position:
            #raise Exception("Image does not exist")
            return

        size = struct.unpack('i',mm[self.position:self.position+4])[0]

        image = mm[begin_read:begin_read + size]

        mm.close()
        return image

class Bundle(object):
    """Represents a bundle file."""

    def __init__(self, path):
        """Constructor requires only one parameters, the
        file path to the bundle, which should include the
        file name.

        The class extracts integer row and column values
        from the given name. An exception is raised if a
        non-standard name is provided.

        Standard naming convention is 'R' + the hex value
        for the first row + 'C' + the hex value for the
        first column.

        ex: R0480C0380
        """
        self.path   = path
        self.name   = self._parse_name(path)
        self.level  = self._parse_level(self.path)
        self.row    = self._parse_row(self.name)
        self.column = self._parse_col(self.name)
        self.tiles  = self._parse_tiles(self.path)

    def _parse_name(self, path):
        match = re.search('(R)[a-fA-F0-9]+(?=.bundl)', path)
        if match:
            return match.group(0)
        else:
            raise Exception("Bad path: %s, could not "
                            "determine tile level." % path)

    def _parse_level(self, path):
        """Returns substring like 'L00', or 'L01', if it exists
        in the given path. Raises an exception if not found."""
        match = re.search('L[0-9]{2}', path)
        if match:
            return match.group(0)
        #else:
        #    raise Exception("Bad path: %s, could not"
        #                    "determine tile level." % path)

    def _parse_row(self, name):
        """Returns an integer from a given bundle name representing
        the first row contained in the bundle.

        ex: R0480C0380 -> 1152
        """
        row_match = re.search('(?<=R)(.*)(?=C)', self.name)

        if not row_match:
            raise Exception('Not a bundle file')

        row_hex = row_match.group(0)
        row_int = int(row_hex, 16)

        return row_int

    def _parse_col(self, name):
        """Returns an integer from a given bundle name representing
        the first column contained in the bundle.

        ex: R0480C0380 -> 896
        """
        col_match = re.search('[^C]+$', self.name)

        if not col_match:
            raise Exception('Not a bundle file')

        col_hex = col_match.group(0)
        col_int = int(col_hex, 16)

        return col_int

    def _parse_tiles(self, file_path):
        """Returns a list of decimal values stored in a .bundlx (bundle
        index) file that represent the locations of images stored in the
        corresponding .bundle file.

        The values are stored in 5 byte chunks using little endian representation
        to store large numbers.  Each .bundlx file is exactly the same size; the
        position of each chunk in the .bundlx indicates the row and column position
        of the particular map tile image in the overall scheme.  These values
        should be added to the top left origin row and column found in the bundle
        file name.

        Each chunk contains at least two bytes.  The first byte represents the row,
        the second represents the column.  However, only 'blank' chunks represent
        the row and column!  Non blank chunks use all 5 byts to represent the
        postition of the image in the .bundle file.

        It is up to the developer to determine what to do with the bogus values
        found in the 'blank' chunks.
        """
        try:
            file = open(file_path, "r+b")
        #except FileNotFoundError as e:
        #    raise e
        except (IOError, OSError) as e:
            raise e
        except Exception as e:
            raise e

        mm = mmap.mmap(file.fileno(), 0)

        chunk_bytes = []
        tiles = []

        # first row is the 60th in
        # the column, don't understand why
        row_count = 60
        col_count = 0

        for i in range(len(mm)):

            byte = mm[i]
            base16 = byte.encode('hex')
            base10 = int(base16, 16)

            chunk_bytes.append(base10)

            if i % 5 == 0:
                if not i == 0:
                    # decimal value is store using
                    # little endian representation
                    stored_value  = chunk_bytes[0] * 1
                    stored_value += chunk_bytes[1] * 256
                    stored_value += chunk_bytes[2] * 65536
                    stored_value += chunk_bytes[3] * 16777216
                    stored_value += chunk_bytes[4] * 4294967296

                    # i don't think i have this right, we'll see
                    row = (row_count / 4) + self.row
                    col = (col_count / 2) + self.column

                    tiles.append(Tile(row, col, stored_value, self.path))

                    chunk_bytes = []
                    # this doesn't really need to happen, but
                    # just for good measure, set value to zero
                    stored_value = 0

                    row_count += 1
                    if row_count > 255:
                        row_count = 0
                        col_count += 1

        mm.close()

        return tiles

    def get_image(self, row, column):
        """Returns the image, if it exists, for the given row, and column."""

        if type(row) is str:
            row = int(row)

        if not type(row) is int:
            raise TypeError("Tile row must be a string or an int")

        if type(column) is str:
            column = int(column)

        if not type(column) is int:
            raise TypeError("Tile column must be a string or an int")


        if row < 0 or column < 0:
            raise ValueError("Tile row and column must "
                             "be greater than zero.")

        for tile in self.tiles:
            if tile.row == row and tile.column == column:
                try:
                    return tile.image()
                except Exception as e:
                    raise e
        return False

class Level(object):
    # class level variables are going to pose a
    # problem when we have more than one cache.
    # todo: refactor Cache and Level to remove
    #       class level collections
    levels = {}
    bundles  = []

    def __init__(self):
        """Empty default constructor"""
        pass

    def append(self, bundle):
        """Appends a Bundle to it's level."""
        if not type(bundle) is Bundle:
            raise TypeError("Incorrect type, not a bundle object.")

        level = bundle.level

        if not level:
            #raise Exception("Bundle does not belong to a level")
            return

        if not Level.levels.has_key(level):
            Level.levels[level] = len(Level.bundles)

        index = Level.levels[level]

        if index >= len(Level.bundles):
            Level.bundles.append([bundle])
        else:
            Level.bundles[index].append(bundle)

    def __getitem__(self, key):
        """Returns a list of bundles, if present. Raises exception
        if level does not exist. Raises type error if index is not
        an int of str, raises value error if value is invalid.

        Valid string = 'L' + two digits, ex: 'L00', 'L01', ...
        Valid int = 0 to 99
        """
        if type(key) is int:
            if key < 0 or index > 99:
                raise ValueError('Level index must be between 0 and 99.')
            else:
                key = "L%02d" % key

        if type(key) is str:
            if not self.exists(key):
                raise Exception("Bundles do not exist for level %s" % key)
            else:
                index = Level.levels[key]
                if index <= len(Level.bundles):
                    return Level.bundles[index]
        else:
            raise TypeError("Index must be valid string or int.")

    def exists(self, key):
        """Returns True if level exists, False otherwise."""
        if Level.levels.has_key(key):
            index = Level.levels[key]
            if index <= len(Level.bundles):
                return True

        return False

    def get_tile(self, level, row, column):
        """Returns the tile, if it exists, for the given
        level, row, and column.
        """
        level = "L%02d" % level
        if not self.exists(level):
            raise Exception('Level %s does not exist in cache' % level)

        bundles = self.bundles[self.levels[level]]

        for bundle in bundles:

            if bundle.row > row:
                continue
            if bundle.column > column:
                continue

            if bundle.row > row - Cache.MAX_ROWS:
                if bundle.column > column - Cache.MAX_COLUMNS:
                    return bundle.get_image(row, column)

class Cache(object):
    """Represents the map cache, with scale levels
    populated by tile bundles.
    """
    MAX_ROWS    = 128
    MAX_COLUMNS = 128

    def __init__(self, root_path):
        """Constructs a Cache object given a valid root path.
        A valid path contains bundle and index files organized
        into levels ('L00', 'L01', ...), inside a folder named
        'Layers' or '_alllayers'.
        """
        self.levels = Level()
        self.root_path = root_path
        self._load_bundles(root_path)

    def _parse_level(self, path):
        """Returns substring like 'L00', or 'L01', if it exists
        in the given path.
        """
        match = re.search('L[0-9]{2}', path)
        if match:
            return match.group(0)

    def _is_cache_path(self, path):
        """Check root_path for 'Layers', '_alllayers',
        or some folder like 'L00'.  Returns boolean.
        """
        contents = os.listdir(path)
        if contents.count("Layers"):
            return True
        elif contents.count("layers"):
            return True
        elif contents.count("_alllayers"):
            return True

        for item in contents:
            if self._parse_level(item):
                return True

        return False

    def _load_bundles(self, root_path):
        """Searches root_path for bundlx files. Loads bundle
        and tile informatio."""
        if not os.path.isdir(root_path):
            raise Exception("Directory does not exist")

        if not self._is_cache_path(root_path):
            raise Exception("Directory does not appear \
                             to contain a map cache")

        for root, dirs, files in os.walk(root_path):

            for file in files:

                file_path = os.path.join(root, file)
                file_name, file_ext = os.path.splitext(file_path)

                if not file_ext.lower() == ".bundlx":
                    continue

                try:
                    bundle = Bundle(file_path)
                #except FileNotFoundError as e:
                #    raise e
                except (IOError, OSError) as e:
                    raise e
                except Exception as e:
                    raise e

                if not bundle:
                    return

                try:
                    self.levels.append(bundle)
                except TypeError as e:
                    raise e
                except ValueError as e:
                    raise e
                except Exception as e:
                    raise e

    def get_tile(self, level, row, column):
        """Returns the tile, if it exists, for the given
        level, row, and column.
        """
        return self.levels.get_tile(level, row, column)

def main():
    cache = Cache('files/')
    tile_image = cache.get_tile(0, 1177, 906)
    if tile_image:
        file = open('image.png','w+b')
        file.write(tile_image)
        file.close()

    #tile row: 1176, column: 906) L00 21696#
    #tile row: 1176, column: 906) L00 74943
    #tile row: 1176, column: 906) L00 115533
    #tile row: 1176, column: 906) L00 159953
    #tile row: 1177, column: 906) L00 170906
    #tile row: 1177, column: 906) L00 21716#

    #tile row: 1208, column: 906) L00 21184#
    #tile row: 1208, column: 906) L00 72895
    #tile row: 1208, column: 906) L00 99982
    #tile row: 1208, column: 906) L00 144439
    #tile row: 1209, column: 906) L00 168134
    #tile row: 1209, column: 906) L00 21204#

if __name__== "__main__":
    main()
