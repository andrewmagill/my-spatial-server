STREET_PRE_DIR_TRANS = {"NORTH" : "N",
                        "SOUTH" : "S",
                        "EAST"  : "E",
                        "WEST"  : "W"}

STREET_PRE_TYPES = ["US", "IH", "SH", "CR", "FM", "RR"]

STREET_PRE_TYPE_TRANS = {"INTERSTATE"    : "IH",
                        "STATE HIGHWAY" : "SH",
                        "US ROUTE"      : "US",
                        "US ROAD"       : "US",
                        "ROUTE"         : "US",
                        "FARM ROAD"     : "FM",
                        "RANCH ROAD"    : "RR",
                        "FARM TO MARKET": "FM",
                        "COUNTY RD"     : "CR"}

STREET_PRE_TYPE_TROUBLE = {"FARM"  : "FM", "RANCH"  : "RR",
                           "STATE" : "SH", "COUNTY" : "CR"}

STREET_POST_TYPES = ["RD", "DR", "ST", "BLVD", "LN", "TRL", "CIR", "CT",
                     "WAY", "HWY", "HIGHWAY", "RUN"]

STREET_POST_TYPE_TRANS = {"ROAD"      : "RD",
                          "DRIVE"     : "DR",
                          "STREET"    : "ST",
                          "BOULEVARD" : "BLVD",
                          "LANE"      : "LN",
                          "TRAIL"     : "TRL",
                          "CIRCLE"    : "CIR",
                          "HIGHWAY"   : "HWY",
                          "COURT"     : "CT"}

POST_DIRECTIONS = ["NB", "SB", "EB", "WB"]

POST_DIR_TRANS = {"NORTHBOUND"   : "NB", "SOUTHBOUND"  : "SB",
                  "EASTBOUND"    : "EB", "WESTBOUND"   : "WB",
                   "NORTH BOUND" : "NB", "SOUTH BOUND" : "SB",
                   "EAST BOUND"  : "EB", "WEST BOUND"  : "WB",
                   "NORTH-BOUND" : "NB", "SOUTH-BOUND" : "SB",
                   "EAST-BOUND"  : "EB", "WEST-BOUND"  : "WB"}
