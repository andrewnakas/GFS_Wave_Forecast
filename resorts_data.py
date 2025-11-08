"""
Comprehensive list of popular ski resorts in the Northern Hemisphere.
Organized by region with key details for data scraping.
"""

NORTHERN_HEMISPHERE_RESORTS = [
    # === NORTH AMERICA - UNITED STATES ===
    # Colorado
    {
        "name": "Vail",
        "country": "USA",
        "region": "Colorado",
        "latitude": 39.6403,
        "longitude": -106.3742,
        "base_elevation_m": 2500,
        "summit_elevation_m": 3527,
        "vertical_drop_m": 1027,
        "website_url": "https://www.vail.com",
        "snow_report_url": "https://www.vail.com/the-mountain/mountain-conditions/snow-and-weather-report.aspx"
    },
    {
        "name": "Aspen Snowmass",
        "country": "USA",
        "region": "Colorado",
        "latitude": 39.2091,
        "longitude": -106.9461,
        "base_elevation_m": 2451,
        "summit_elevation_m": 3813,
        "vertical_drop_m": 1362,
        "website_url": "https://www.aspensnowmass.com",
        "snow_report_url": "https://www.aspensnowmass.com/our-mountains/snowmass/snow-report"
    },
    {
        "name": "Breckenridge",
        "country": "USA",
        "region": "Colorado",
        "latitude": 39.4817,
        "longitude": -106.0384,
        "base_elevation_m": 2926,
        "summit_elevation_m": 3914,
        "vertical_drop_m": 988,
        "website_url": "https://www.breckenridge.com",
        "snow_report_url": "https://www.breckenridge.com/the-mountain/mountain-conditions/snow-and-weather-report.aspx"
    },
    {
        "name": "Keystone",
        "country": "USA",
        "region": "Colorado",
        "latitude": 39.5792,
        "longitude": -105.9347,
        "base_elevation_m": 2835,
        "summit_elevation_m": 3782,
        "vertical_drop_m": 947,
        "website_url": "https://www.keystoneresort.com",
        "snow_report_url": "https://www.keystoneresort.com/the-mountain/mountain-conditions/snow-and-weather-report.aspx"
    },
    {
        "name": "Steamboat",
        "country": "USA",
        "region": "Colorado",
        "latitude": 40.4580,
        "longitude": -106.8050,
        "base_elevation_m": 2103,
        "summit_elevation_m": 3221,
        "vertical_drop_m": 1118,
        "website_url": "https://www.steamboat.com",
        "snow_report_url": "https://www.steamboat.com/the-mountain/mountain-report"
    },

    # Utah
    {
        "name": "Park City",
        "country": "USA",
        "region": "Utah",
        "latitude": 40.6514,
        "longitude": -111.5079,
        "base_elevation_m": 2103,
        "summit_elevation_m": 3048,
        "vertical_drop_m": 945,
        "website_url": "https://www.parkcitymountain.com",
        "snow_report_url": "https://www.parkcitymountain.com/the-mountain/mountain-conditions/snow-and-weather-report.aspx"
    },
    {
        "name": "Alta",
        "country": "USA",
        "region": "Utah",
        "latitude": 40.5885,
        "longitude": -111.6381,
        "base_elevation_m": 2600,
        "summit_elevation_m": 3216,
        "vertical_drop_m": 616,
        "website_url": "https://www.alta.com",
        "snow_report_url": "https://www.alta.com/conditions"
    },
    {
        "name": "Snowbird",
        "country": "USA",
        "region": "Utah",
        "latitude": 40.5830,
        "longitude": -111.6560,
        "base_elevation_m": 2365,
        "summit_elevation_m": 3353,
        "vertical_drop_m": 988,
        "website_url": "https://www.snowbird.com",
        "snow_report_url": "https://www.snowbird.com/mountain-report/"
    },
    {
        "name": "Deer Valley",
        "country": "USA",
        "region": "Utah",
        "latitude": 40.6374,
        "longitude": -111.4783,
        "base_elevation_m": 2195,
        "summit_elevation_m": 2917,
        "vertical_drop_m": 722,
        "website_url": "https://www.deervalley.com",
        "snow_report_url": "https://www.deervalley.com/explore-the-resort/about-deer-valley/mountain-and-snow-report"
    },

    # California
    {
        "name": "Mammoth Mountain",
        "country": "USA",
        "region": "California",
        "latitude": 37.6308,
        "longitude": -119.0326,
        "base_elevation_m": 2424,
        "summit_elevation_m": 3369,
        "vertical_drop_m": 945,
        "website_url": "https://www.mammothmountain.com",
        "snow_report_url": "https://www.mammothmountain.com/conditions-and-weather/snow-report"
    },
    {
        "name": "Palisades Tahoe",
        "country": "USA",
        "region": "California",
        "latitude": 39.1969,
        "longitude": -120.2357,
        "base_elevation_m": 1890,
        "summit_elevation_m": 2743,
        "vertical_drop_m": 853,
        "website_url": "https://www.palisadestahoe.com",
        "snow_report_url": "https://www.palisadestahoe.com/mountain-information/snow-report"
    },
    {
        "name": "Heavenly",
        "country": "USA",
        "region": "California/Nevada",
        "latitude": 38.9352,
        "longitude": -119.9394,
        "base_elevation_m": 2002,
        "summit_elevation_m": 3068,
        "vertical_drop_m": 1066,
        "website_url": "https://www.skiheavenly.com",
        "snow_report_url": "https://www.skiheavenly.com/the-mountain/mountain-conditions/snow-and-weather-report.aspx"
    },

    # Wyoming
    {
        "name": "Jackson Hole",
        "country": "USA",
        "region": "Wyoming",
        "latitude": 43.5875,
        "longitude": -110.8281,
        "base_elevation_m": 1924,
        "summit_elevation_m": 3185,
        "vertical_drop_m": 1261,
        "website_url": "https://www.jacksonhole.com",
        "snow_report_url": "https://www.jacksonhole.com/snow-report"
    },

    # Vermont
    {
        "name": "Stowe",
        "country": "USA",
        "region": "Vermont",
        "latitude": 44.5303,
        "longitude": -72.7817,
        "base_elevation_m": 383,
        "summit_elevation_m": 1339,
        "vertical_drop_m": 956,
        "website_url": "https://www.stowe.com",
        "snow_report_url": "https://www.stowe.com/the-mountain/mountain-conditions/snow-and-weather-report.aspx"
    },
    {
        "name": "Killington",
        "country": "USA",
        "region": "Vermont",
        "latitude": 43.6042,
        "longitude": -72.8223,
        "base_elevation_m": 594,
        "summit_elevation_m": 1293,
        "vertical_drop_m": 699,
        "website_url": "https://www.killington.com",
        "snow_report_url": "https://www.killington.com/the-mountain/mountain-conditions/snow-and-weather-report"
    },

    # === NORTH AMERICA - CANADA ===
    # British Columbia
    {
        "name": "Whistler Blackcomb",
        "country": "Canada",
        "region": "British Columbia",
        "latitude": 50.1163,
        "longitude": -122.9574,
        "base_elevation_m": 675,
        "summit_elevation_m": 2284,
        "vertical_drop_m": 1609,
        "website_url": "https://www.whistlerblackcomb.com",
        "snow_report_url": "https://www.whistlerblackcomb.com/the-mountain/mountain-conditions/snow-and-weather-report.aspx"
    },
    {
        "name": "Revelstoke",
        "country": "Canada",
        "region": "British Columbia",
        "latitude": 50.9981,
        "longitude": -118.1957,
        "base_elevation_m": 1698,
        "summit_elevation_m": 2225,
        "vertical_drop_m": 527,
        "website_url": "https://www.revelstokemountainresort.com",
        "snow_report_url": "https://www.revelstokemountainresort.com/mountain-info/snow-report"
    },
    {
        "name": "Big White",
        "country": "Canada",
        "region": "British Columbia",
        "latitude": 49.7253,
        "longitude": -118.9335,
        "base_elevation_m": 1508,
        "summit_elevation_m": 2319,
        "vertical_drop_m": 811,
        "website_url": "https://www.bigwhite.com",
        "snow_report_url": "https://www.bigwhite.com/snow"
    },

    # Alberta
    {
        "name": "Lake Louise",
        "country": "Canada",
        "region": "Alberta",
        "latitude": 51.4254,
        "longitude": -116.1773,
        "base_elevation_m": 1646,
        "summit_elevation_m": 2637,
        "vertical_drop_m": 991,
        "website_url": "https://www.skilouise.com",
        "snow_report_url": "https://www.skilouise.com/snow-conditions"
    },
    {
        "name": "Sunshine Village",
        "country": "Canada",
        "region": "Alberta",
        "latitude": 51.1125,
        "longitude": -115.7642,
        "base_elevation_m": 1660,
        "summit_elevation_m": 2730,
        "vertical_drop_m": 1070,
        "website_url": "https://www.skibanff.com",
        "snow_report_url": "https://www.skibanff.com/snow-report"
    },

    # Quebec
    {
        "name": "Tremblant",
        "country": "Canada",
        "region": "Quebec",
        "latitude": 46.2094,
        "longitude": -74.5883,
        "base_elevation_m": 265,
        "summit_elevation_m": 875,
        "vertical_drop_m": 610,
        "website_url": "https://www.tremblant.ca",
        "snow_report_url": "https://www.tremblant.ca/conditions"
    },

    # === EUROPE - FRANCE ===
    {
        "name": "Chamonix",
        "country": "France",
        "region": "Haute-Savoie",
        "latitude": 45.9237,
        "longitude": 6.8694,
        "base_elevation_m": 1035,
        "summit_elevation_m": 3842,
        "vertical_drop_m": 2807,
        "website_url": "https://www.chamonix.com",
        "snow_report_url": "https://www.chamonix.com/snow-report"
    },
    {
        "name": "Val d'Isère",
        "country": "France",
        "region": "Savoie",
        "latitude": 45.4486,
        "longitude": 6.9789,
        "base_elevation_m": 1550,
        "summit_elevation_m": 3456,
        "vertical_drop_m": 1906,
        "website_url": "https://www.valdisere.com",
        "snow_report_url": "https://www.valdisere.com/en/snow-report"
    },
    {
        "name": "Courchevel",
        "country": "France",
        "region": "Savoie",
        "latitude": 45.4167,
        "longitude": 6.6333,
        "base_elevation_m": 1300,
        "summit_elevation_m": 3230,
        "vertical_drop_m": 1930,
        "website_url": "https://www.courchevel.com",
        "snow_report_url": "https://www.courchevel.com/en/live/snow-report.html"
    },
    {
        "name": "Les Trois Vallées",
        "country": "France",
        "region": "Savoie",
        "latitude": 45.4300,
        "longitude": 6.5800,
        "base_elevation_m": 1300,
        "summit_elevation_m": 3230,
        "vertical_drop_m": 1930,
        "website_url": "https://www.les3vallees.com",
        "snow_report_url": "https://www.les3vallees.com/en/snow-report/"
    },

    # === EUROPE - SWITZERLAND ===
    {
        "name": "Zermatt",
        "country": "Switzerland",
        "region": "Valais",
        "latitude": 46.0207,
        "longitude": 7.7491,
        "base_elevation_m": 1620,
        "summit_elevation_m": 3883,
        "vertical_drop_m": 2263,
        "website_url": "https://www.zermatt.ch",
        "snow_report_url": "https://www.zermatt.ch/en/snow-report"
    },
    {
        "name": "Verbier",
        "country": "Switzerland",
        "region": "Valais",
        "latitude": 46.0964,
        "longitude": 7.2280,
        "base_elevation_m": 1500,
        "summit_elevation_m": 3330,
        "vertical_drop_m": 1830,
        "website_url": "https://www.verbier.ch",
        "snow_report_url": "https://www.verbier.ch/en/snow-report"
    },
    {
        "name": "St. Moritz",
        "country": "Switzerland",
        "region": "Graubünden",
        "latitude": 46.4983,
        "longitude": 9.8355,
        "base_elevation_m": 1856,
        "summit_elevation_m": 3057,
        "vertical_drop_m": 1201,
        "website_url": "https://www.stmoritz.com",
        "snow_report_url": "https://www.stmoritz.com/en/snow-report"
    },

    # === EUROPE - AUSTRIA ===
    {
        "name": "St. Anton",
        "country": "Austria",
        "region": "Tyrol",
        "latitude": 47.1279,
        "longitude": 10.2656,
        "base_elevation_m": 1304,
        "summit_elevation_m": 2811,
        "vertical_drop_m": 1507,
        "website_url": "https://www.stantonamarlberg.com",
        "snow_report_url": "https://www.stantonamarlberg.com/en/snow-weather"
    },
    {
        "name": "Ischgl",
        "country": "Austria",
        "region": "Tyrol",
        "latitude": 47.0120,
        "longitude": 10.2991,
        "base_elevation_m": 1400,
        "summit_elevation_m": 2872,
        "vertical_drop_m": 1472,
        "website_url": "https://www.ischgl.com",
        "snow_report_url": "https://www.ischgl.com/en/snow-report"
    },
    {
        "name": "Kitzbühel",
        "country": "Austria",
        "region": "Tyrol",
        "latitude": 47.4467,
        "longitude": 12.3914,
        "base_elevation_m": 800,
        "summit_elevation_m": 2000,
        "vertical_drop_m": 1200,
        "website_url": "https://www.kitzbuehel.com",
        "snow_report_url": "https://www.kitzbuehel.com/en/snow-report"
    },

    # === EUROPE - ITALY ===
    {
        "name": "Cortina d'Ampezzo",
        "country": "Italy",
        "region": "Veneto",
        "latitude": 46.5369,
        "longitude": 12.1357,
        "base_elevation_m": 1224,
        "summit_elevation_m": 2930,
        "vertical_drop_m": 1706,
        "website_url": "https://www.cortinaskiresort.it",
        "snow_report_url": "https://www.dolomitisuperski.com/en/snow-report"
    },

    # === ASIA - JAPAN ===
    {
        "name": "Niseko",
        "country": "Japan",
        "region": "Hokkaido",
        "latitude": 42.8048,
        "longitude": 140.6875,
        "base_elevation_m": 308,
        "summit_elevation_m": 1308,
        "vertical_drop_m": 1000,
        "website_url": "https://www.niseko.ne.jp",
        "snow_report_url": "https://www.niseko.ne.jp/en/snow/"
    },
    {
        "name": "Hakuba Valley",
        "country": "Japan",
        "region": "Nagano",
        "latitude": 36.7000,
        "longitude": 137.8300,
        "base_elevation_m": 760,
        "summit_elevation_m": 1831,
        "vertical_drop_m": 1071,
        "website_url": "https://www.hakubavalley.com",
        "snow_report_url": "https://www.hakubavalley.com/en/winter/snow"
    },
    {
        "name": "Rusutsu",
        "country": "Japan",
        "region": "Hokkaido",
        "latitude": 42.7367,
        "longitude": 140.8861,
        "base_elevation_m": 400,
        "summit_elevation_m": 994,
        "vertical_drop_m": 594,
        "website_url": "https://rusutsu.com",
        "snow_report_url": "https://rusutsu.com/en/snow/"
    },

    # === ASIA - SOUTH KOREA ===
    {
        "name": "Yongpyong",
        "country": "South Korea",
        "region": "Gangwon",
        "latitude": 37.6383,
        "longitude": 128.6806,
        "base_elevation_m": 700,
        "summit_elevation_m": 1458,
        "vertical_drop_m": 758,
        "website_url": "https://www.yongpyong.co.kr",
        "snow_report_url": "https://www.yongpyong.co.kr/eng/snowInfo.do"
    },
]


def get_resorts_by_country(country: str):
    """Get all resorts in a specific country."""
    return [r for r in NORTHERN_HEMISPHERE_RESORTS if r['country'] == country]


def get_resorts_by_region(region: str):
    """Get all resorts in a specific region."""
    return [r for r in NORTHERN_HEMISPHERE_RESORTS if r['region'] == region]


def get_all_countries():
    """Get list of all countries."""
    return sorted(list(set(r['country'] for r in NORTHERN_HEMISPHERE_RESORTS)))


def get_all_regions():
    """Get list of all regions."""
    return sorted(list(set(r['region'] for r in NORTHERN_HEMISPHERE_RESORTS)))
