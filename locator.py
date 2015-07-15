import os, sys, re, usaddress, logging, mappings
from osgeo import ogr, osr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class USFields(object):
    AddressNumber             = 'AddressNumber'
    AddressNumberSuffix       = 'AddressNumberSuffix'
    StreetNamePreDirectional  = 'StreetNamePreDirectional'
    StreetNamePreType         = 'StreetNamePreType'
    StreetName                = 'StreetName'
    StreetNamePostDirectional = 'StreetNamePostDirectional'
    StreetNamePostType        = 'StreetNamePostType'

class ATXFields(object):
    address     = 'address'
    address_fr  = 'address_fr'
    prefix_dir  = 'prefix_dir'
    prefix_typ  = 'prefix_typ'
    street_nam  = 'street_nam'
    suffix_dir  = 'suffix_dir'
    street_typ  = 'street_typ'
    segment_id  = 'segment_id'
    parent_pla  = 'parent_pla'
    place_id    = 'place_id'
    full_stree  = 'full_stree'

class Messages(object):
    str_req = "String required"
    list_req = "List required"
    dict_req = "Dictionary required"
    bad_results = "Parser results are not valid"
    bad_string = "Invalid search string"
    bad_query = "Query did not return any results"

STREET_ADDRESS = "Street Address"

field_map = {
    USFields.AddressNumber             : ATXFields.address,
    USFields.AddressNumberSuffix       : ATXFields.address_fr,
    USFields.StreetNamePreDirectional  : ATXFields.prefix_dir,
    USFields.StreetNamePreType         : ATXFields.prefix_typ,
    USFields.StreetName                : ATXFields.street_nam,
    USFields.StreetNamePostDirectional : ATXFields.suffix_dir,
    USFields.StreetNamePostType        : ATXFields.street_typ,
}

ADDRESS_FILE_PATH = r"shapefiles/address_point/address_point.shp"

OGR_SHP_DRIVER = 'ESRI Shapefile'

EPSG_2277 = 2277

ADDRESS_OVER_UNDER = 20

def _sanitize(user_input):
    """strip unwated characters from user input
    """
    if not type(user_input) is str:
        raise TypeError(Messages.str_req)

    # I'm sure this could be done better
    clean = re.sub(r"[;\(\)\[\]\<\>=:*\%\$\`\?]", "", user_input)
    return clean

def _pre_hack(address_string):
    """find and replace some stuff, hopefully won't be necessary
    after training
    """
    if not type(address_string) is str:
        raise TypeError(Messages.str_req)

    address_string = address_string.upper()
    words = address_string.split(' ')
    for word in words:
        if word in mappings.STREET_PRE_TYPE_TRANS.keys():
            address_string = address_string.replace(word, mappings.STREET_PRE_TYPE_TRANS[word])
        if word in mappings.STREET_POST_TYPE_TRANS.keys():
            address_string = address_string.replace(word, mappings.STREET_POST_TYPE_TRANS[word])
        if word in mappings.POST_DIR_TRANS.keys():
            address_string = address_string.replace(word, mappings.POST_DIR_TRANS[word])

    return address_string

def _translate_to_atx(address_parts):
    """takes usfields tuple and returns atx dict
    """
    if not len(address_parts) == 2:
        raise Exception(Messages.bad_results)

    result_type = address_parts[1]

    if not result_type == STREET_ADDRESS:
        raise Exception(Messages.bad_string)

    ordered_dict = address_parts[0]
    atx_address_parts = {}

    for key, value in ordered_dict.items():
        try:
            atx_field = field_map[key]
            atx_address_parts[atx_field] = value
        except:
            logger.info("No ATX map for USAddress field: %s" % key)

    return atx_address_parts

def _post_hack(atx_address_parts):
    """put parts in the right place, like street type in
    post-type rather than post-direction field. hopefully
    won't be necessary after training
    """

    print atx_address_parts

    try:
        if atx_address_parts[ATXFields.street_nam] == '1/2':
            name = atx_address_parts[ATXFields.prefix_dir]
            atx_address_parts[ATXFields.street_nam] = name
            del atx_address_parts[ATXFields.prefix_dir]
    except Exception as e:
        logging.debug(e.message)

    return atx_address_parts

def _parse(address_string):
    """parses address string into atx address parts,
    returns list
    """
    if not type(address_string) is str:
        raise TypeError(Messages.str_req)

    address_string = _sanitize(address_string)
    address_string = _pre_hack(address_string)
    address_parts = usaddress.tag(address_string)
    address_parts = _translate_to_atx(address_parts)
    address_parts = _post_hack(address_parts)
    return address_parts

def _construct_query(address_parts):
    """constructs sql query from address parts,
    returns string
    """
    if not type(address_parts) is dict:
        raise TypeError(Messages.dict_req)

    clause_list = []

    for key, value in address_parts.items():
        if key == ATXFields.address:
            value = int(value)
            low = value - ADDRESS_OVER_UNDER
            high = value + ADDRESS_OVER_UNDER
            clause_list.append("{0} > {1} AND {0} < {2}"
                                .format(key, low, high))
        elif key == ATXFields.street_nam:
            clause_list.append("{} LIKE '%{}%'".format(key, value))
        else:
            #clause_list.append("{} = '{}'".format(key, value))
            pass

    field_list = [field for field in dir(ATXFields) if not field.startswith('_')]

    query = ("SELECT OGR_GEOM_WKT, %s FROM address_point WHERE " %
             ', '.join(field_list))

    if len(clause_list) <= 0:
        raise Exception(Messages.bad_results)

    query += clause_list[0]

    for clause in clause_list[1:]:
        query += " and " + clause

    # doesn't work with semicolon
    # so don't do this: query += ";"

    return query

def _query_db(query):
    """executes sql query against data in shapefile
    """
    if not type(query) is str:
        raise TypeError("string required")

    if not os.path.exists(ADDRESS_FILE_PATH):
        raise Exception("Invalid path, shapefile does not exist")

    driver = ogr.GetDriverByName(OGR_SHP_DRIVER)
    data_source = driver.Open(ADDRESS_FILE_PATH, 0)

    layer = data_source.ExecuteSQL(query)

    if not layer:
        raise Exception(Messages.bad_query)

    address_candidates = []
    feature = layer.GetNextFeature()
    while feature:
        fields = {}
        for field_index in range(feature.GetFieldCount()):
            key = feature.GetFieldDefnRef(field_index).GetName()
            value = feature.GetFieldAsString(field_index)
            fields[key] = value
        address_candidates.append(fields)
        feature = layer.GetNextFeature()
    return address_candidates

def _score_candidates(candidates, address_parts):
    threshold_candidates = []
    for candidate in candidates:
        score = 0
        for key, value in address_parts.items():
            if key == ATXFields.address:
                candidate_value = int(candidate[key])
                preferred_value = int(address_parts[key])

                if candidate_value > preferred_value:
                    difference = candidate_value - preferred_value
                else:
                    difference = preferred_value - candidate_value

                score += ((ADDRESS_OVER_UNDER - difference) * (10/float(ADDRESS_OVER_UNDER)))

            elif address_parts[key] in candidate[ATXFields.full_stree]:
                score += 10

        max_score = len(address_parts)*10
        normalized_score = int(((float(score)/float(max_score)) * 100))
        candidate['score'] = normalized_score

        if normalized_score > 75:
            threshold_candidates.append(candidate)

    return threshold_candidates

def _reproject(features, epsg):
    # this may help
    # https://pcjericks.github.io/py-gdalogr-cookbook/projection.html
    return features

def _jsonify(address_candidates):
    """returns json string from list of address candidates
    """
    #if not type(address_candidates) is list:
    #    raise TypeError("list required")

    spatialReference = {"wkid": 102739,"latestWkid": 2277}
    candidates = []

    for candidate in address_candidates:

        fields = {}
        fields['address'] = candidate['full_stree']

        wkt = candidate['OGR_GEOM_WKT']
        point = ogr.CreateGeometryFromWkt(wkt)
        x = point.GetX()
        y = point.GetY()

        location = {}
        location['x'] = x
        location['y'] = y

        fields['location'] = location
        fields['score'] = candidate['score']

        attributes = {}

        fields['attributes'] = attributes

        candidates.append(fields)

    ordered_candidates = sorted(candidates, key=lambda t: t['score'], reverse=True)

    fortheweb = {'spatialReference' : spatialReference,
                 'candidates' : ordered_candidates}

    return repr(fortheweb).replace("\'","\"")

def locate(address_string, epsg=EPSG_2277):
    """returns json address candidates given address string
    """
    if not type(address_string) is str:
        raise TypeError(Messages.str_req)

    address_parts = _parse(address_string)
    query = _construct_query(address_parts)
    address_candidates = _query_db(query)
    scored_candidates = _score_candidates(address_candidates, address_parts)
    json_result = _jsonify(scored_candidates)

    #if not epsg == EPSG_2277:
    #    results = reproject(results, epsg)

    return json_result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(locate(sys.argv[1]))
    else:
        print(locate("2201 Barton Springs Rd"))
