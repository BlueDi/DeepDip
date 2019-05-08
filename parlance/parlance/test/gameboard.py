r'''Test cases for the Parlance gameboard and unit orders
    Copyright (C) 2004-2008  Eric Wald
    
    A few of these tests currently fail, because the features they test are
    only allowed under AOA or certain rule variants.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

import time
import unittest

from parlance.config     import variants
from parlance.functions  import fails
from parlance.gameboard  import Map, Province, Turn, Variant
from parlance.judge      import DatcOptions
from parlance.language   import IntegerToken, Representation, protocol
from parlance.orders     import createUnitOrder
from parlance.tokens     import *
from parlance.validation import Validator
from parlance.xtended    import *

def load_variant(information):
    variant = Variant("testing")
    variant.parse(line.strip() for line in information.splitlines())
    variant.rep = variant.tokens()
    return variant

class VariantFileTests(unittest.TestCase):
    "Tests for loading information from a variant file"
    def assertContains(self, container, item):
        if item not in container:
            raise self.failureException, '%s not in %s' % (item, container)
    
    def test_parse_empty(self):
        # Variant.parse() must be able to handle an empty stream
        variant = load_variant("")
    
    def test_default_name(self):
        variant = Variant("testing")
        self.failUnlessEqual(variant.name, "testing")
    def test_name_loaded(self):
        variant = load_variant('''
            [variant]
            name=Something
        ''')
        self.failUnlessEqual(variant.name, "Something")
    def test_default_mapname(self):
        variant = Variant("testing")
        self.failUnlessEqual(variant.mapname, "testing")
    def test_mapname_loaded(self):
        variant = load_variant('''
            [variant]
            mapname=Something
        ''')
        self.failUnlessEqual(variant.mapname, "Something")
    def test_default_description(self):
        variant = Variant("testing")
        self.failUnlessEqual(variant.description, "")
    def test_description_loaded(self):
        variant = load_variant('''
            [variant]
            description=Something
        ''')
        self.failUnlessEqual(variant.description, "Something")
    def test_default_judge(self):
        variant = Variant("testing")
        self.failUnlessEqual(variant.judge, "standard")
    def test_judge_loaded(self):
        variant = load_variant('''
            [variant]
            judge=Something
        ''')
        self.failUnlessEqual(variant.judge, "Something")
    def test_default_season(self):
        variant = Variant("testing")
        self.failUnlessEqual(variant.start, (SPR, 0))
    def test_season_loaded(self):
        variant = load_variant('''
            [variant]
            start=WIN 2000
        ''')
        self.failUnlessEqual(variant.start, (WIN, 2000))
    
    def test_default_powers(self):
        variant = Variant("testing")
        self.failUnlessEqual(variant.powers, {})
    def test_powers_both(self):
        variant = load_variant('''
            [powers]
            ONE=name,adj
        ''')
        self.failUnlessEqual(variant.powers, {
                "ONE": ("name", "adj"),
        })
    def test_powers_spaced(self):
        variant = load_variant('''
            [powers]
            ONE=name, adj
        ''')
        self.failUnlessEqual(variant.powers, {
                "ONE": ("name", "adj"),
        })
    def test_powers_name(self):
        variant = load_variant('''
            [powers]
            TWO=someone
        ''')
        self.failUnlessEqual(variant.powers, {
                "TWO": ("someone", "someone"),
        })
    def test_powers_empty(self):
        variant = load_variant('''
            [powers]
            TRE=
        ''')
        self.failUnlessEqual(variant.powers, {
                "TRE": ("TRE", "TRE"),
        })
    def test_powers_multiple(self):
        variant = load_variant('''
            [powers]
            ONE=name,adj
            TWO=someone,somewhere
        ''')
        self.failUnlessEqual(variant.powers, {
                "ONE": ("name", "adj"),
                "TWO": ("someone", "somewhere"),
        })
    
    def test_default_provinces(self):
        variant = Variant("testing")
        self.failUnlessEqual(variant.provinces, {})
    def test_provinces_name(self):
        variant = load_variant('''
            [provinces]
            TWO=somewhere
        ''')
        self.failUnlessEqual(variant.provinces, {"TWO": "somewhere"})
    def test_provinces_empty(self):
        variant = load_variant('''
            [provinces]
            ONE=
        ''')
        self.failUnlessEqual(variant.provinces, {"ONE": "ONE"})
    def test_provinces_multiple(self):
        variant = load_variant('''
            [provinces]
            ONE=name
            TWO=somewhere
        ''')
        self.failUnlessEqual(variant.provinces, {
                "ONE": "name",
                "TWO": "somewhere",
        })
    
    def test_default_homes(self):
        variant = Variant("testing")
        self.failUnlessEqual(variant.homes, {})
    def test_homes_many(self):
        variant = load_variant('''
            [homes]
            ONE=TWO,TRE,FUR
        ''')
        self.failUnlessEqual(variant.homes, {
                "ONE": ["TWO", "TRE", "FUR"],
        })
    def test_homes_one(self):
        variant = load_variant('''
            [homes]
            ONE=TWO
        ''')
        self.failUnlessEqual(variant.homes, {"ONE": ["TWO"]})
    def test_homes_empty(self):
        variant = load_variant('''
            [homes]
            ONE=
        ''')
        self.failUnlessEqual(variant.homes, {"ONE": []})
    def test_homes_multiple(self):
        variant = load_variant('''
            [homes]
            ONE=TRE,FIV
            TWO=FUR,SIX
        ''')
        self.failUnlessEqual(variant.homes, {
                "ONE": ["TRE", "FIV"],
                "TWO": ["FUR", "SIX"],
        })
    def test_homes_comma(self):
        variant = load_variant('''
            [homes]
            ONE=TWO,TRE,
        ''')
        self.failUnlessEqual(variant.homes, {"ONE": ["TWO", "TRE"]})
    def test_homes_spaces(self):
        variant = load_variant('''
            [homes]
            ONE=TWO, TRE, FUR
        ''')
        self.failUnlessEqual(variant.homes, {
                "ONE": ["TWO", "TRE", "FUR"],
        })
    
    def test_default_ownership(self):
        variant = Variant("testing")
        self.failUnlessEqual(variant.ownership, {})
    def test_ownership_many(self):
        variant = load_variant('''
            [ownership]
            ONE=TWO,TRE,FUR
        ''')
        self.failUnlessEqual(variant.ownership, {
                "ONE": ["TWO", "TRE", "FUR"],
        })
    def test_ownership_one(self):
        variant = load_variant('''
            [ownership]
            ONE=TWO
        ''')
        self.failUnlessEqual(variant.ownership, {"ONE": ["TWO"]})
    def test_ownership_empty(self):
        variant = load_variant('''
            [ownership]
            ONE=
        ''')
        self.failUnlessEqual(variant.ownership, {"ONE": []})
    def test_ownership_multiple(self):
        variant = load_variant('''
            [ownership]
            ONE=TRE,FIV
            TWO=FUR,SIX
        ''')
        self.failUnlessEqual(variant.ownership, {
                "ONE": ["TRE", "FIV"],
                "TWO": ["FUR", "SIX"],
        })
    def test_ownership_comma(self):
        variant = load_variant('''
            [ownership]
            ONE=TWO,TRE,
        ''')
        self.failUnlessEqual(variant.ownership, {"ONE": ["TWO", "TRE"]})
    def test_ownership_spaces(self):
        variant = load_variant('''
            [ownership]
            ONE=TWO, TRE, FUR
        ''')
        self.failUnlessEqual(variant.ownership, {
                "ONE": ["TWO", "TRE", "FUR"],
        })
    
    def test_default_position(self):
        variant = Variant("testing")
        self.failUnlessEqual(variant.position, {})
    def test_position_many(self):
        variant = load_variant('''
            [positions]
            ONE=AMY TWO,AMY TRE,FLT FUR
        ''')
        self.failUnlessEqual(variant.position, {
                "ONE": ["AMY TWO", "AMY TRE", "FLT FUR"],
        })
    def test_position_one(self):
        variant = load_variant('''
            [positions]
            ONE=AMY TWO
        ''')
        self.failUnlessEqual(variant.position, {"ONE": ["AMY TWO"]})
    def test_position_empty(self):
        variant = load_variant('''
            [positions]
            ONE=
        ''')
        self.failUnlessEqual(variant.position, {"ONE": []})
    def test_position_multiple(self):
        variant = load_variant('''
            [positions]
            ONE=AMY TRE,FLT FIV
            TWO=AMY FUR,FLT SIX
        ''')
        self.failUnlessEqual(variant.position, {
                "ONE": ["AMY TRE", "FLT FIV"],
                "TWO": ["AMY FUR", "FLT SIX"],
        })
    def test_position_comma(self):
        variant = load_variant('''
            [positions]
            ONE=AMY TWO,FLT TRE,
        ''')
        self.failUnlessEqual(variant.position, {
                "ONE": ["AMY TWO", "FLT TRE"],
        })
    def test_position_spaces(self):
        variant = load_variant('''
            [positions]
            ONE=AMY TWO, AMY TRE, FLT FUR
        ''')
        self.failUnlessEqual(variant.position, {
                "ONE": ["AMY TWO", "AMY TRE", "FLT FUR"],
        })
    
    def test_default_borders(self):
        variant = Variant("testing")
        self.failUnlessEqual(variant.borders, {})
    def test_borders_empty(self):
        variant = load_variant('''
            [borders]
            ONE=
        ''')
        self.failUnlessEqual(variant.borders, {"ONE": {}})
    def test_borders_army(self):
        variant = load_variant('''
            [borders]
            ONE=AMY TWO TRE FUR
        ''')
        self.failUnlessEqual(variant.borders, {
                "ONE": {AMY: "TWO TRE FUR"},
        })
    def test_borders_swiss(self):
        variant = load_variant('''
            [borders]
            ONE=AMY
        ''')
        self.failUnlessEqual(variant.borders, {
                "ONE": {AMY: ""},
        })
    def test_borders_island(self):
        variant = load_variant('''
            [borders]
            ONE=AMY, FLT TWO
        ''')
        self.failUnlessEqual(variant.borders, {
                "ONE": {
                    AMY: "",
                    FLT: "TWO",
                },
        })
    def test_borders_fleet(self):
        variant = load_variant('''
            [borders]
            ONE=FLT TWO TRE FUR
        ''')
        self.failUnlessEqual(variant.borders, {
                "ONE": {FLT: "TWO TRE FUR"},
        })
    def test_borders_lake(self):
        variant = load_variant('''
            [borders]
            ONE=FLT
        ''')
        self.failUnlessEqual(variant.borders, {
                "ONE": {FLT: ""},
        })
    def test_borders_coastal(self):
        variant = load_variant('''
            [borders]
            ONE=AMY TWO, FLT TRE
        ''')
        self.failUnlessEqual(variant.borders, {
                "ONE": {
                    AMY: "TWO",
                    FLT: "TRE",
                },
        })
    def test_borders_coastlines(self):
        variant = load_variant('''
            [borders]
            ONE=AMY TWO, (FLT SCS) TRE, (FLT NCS) FUR
        ''')
        self.failUnlessEqual(variant.borders, {
                "ONE": {
                    AMY: "TWO",
                    (FLT, SCS): "TRE",
                    (FLT, NCS): "FUR",
                },
        })
    def test_bordering_coastline(self):
        variant = load_variant('''
            [borders]
            ONE=FLT (TRE SCS)
        ''')
        self.failUnlessEqual(variant.borders, {
                "ONE": {
                    FLT: "(TRE SCS)",
                },
        })
    
    def test_default_rep(self):
        variant = Variant("testing")
        self.failUnlessEqual(variant.rep, protocol.default_rep)
    def test_passed_rep(self):
        rep = Representation({0x4A00: "ONE"}, protocol.base_rep)
        variant = Variant("testing", rep=rep)
        self.failUnlessEqual(variant.rep, rep)
    def test_rep_empty(self):
        variant = load_variant("")
        self.failUnlessEqual(variant.rep, {})
    def test_rep_inland(self):
        variant = load_variant('''
            [borders]
            ONE=AMY TWO
        ''')
        self.failUnlessEqual(variant.rep, {
                "ONE": 0x5000,
        })
    def test_rep_inland_sc(self):
        variant = load_variant('''
            [homes]
            UNO=ONE
            [borders]
            ONE=AMY TWO
        ''')
        self.failUnlessEqual(variant.rep, {
                "ONE": 0x5100,
        })
    def test_rep_inland_home(self):
        variant = load_variant('''
            [homes]
            TRE=ONE
            [borders]
            ONE=AMY TWO
        ''')
        self.failUnlessEqual(variant.rep, {
                "ONE": 0x5100,
                "TRE": 0x4100,
        })
    def test_rep_sea(self):
        variant = load_variant('''
            [borders]
            ONE=FLT TWO
        ''')
        self.failUnlessEqual(variant.rep, {
                "ONE": 0x5200,
        })
    def test_rep_sea_sc(self):
        variant = load_variant('''
            [homes]
            UNO=ONE
            [borders]
            ONE=FLT TWO
        ''')
        self.failUnlessEqual(variant.rep, {
                "ONE": 0x5300,
        })
    def test_rep_sea_home(self):
        variant = load_variant('''
            [homes]
            TRE=ONE
            [borders]
            ONE=FLT TWO
        ''')
        self.failUnlessEqual(variant.rep, {
                "ONE": 0x5300,
                "TRE": 0x4100,
        })
    def test_rep_coastal(self):
        variant = load_variant('''
            [borders]
            ONE=AMY TWO, FLT FUR
        ''')
        self.failUnlessEqual(variant.rep, {
                "ONE": 0x5400,
        })
    def test_rep_coastal_sc(self):
        variant = load_variant('''
            [homes]
            UNO=ONE
            [borders]
            ONE=AMY TWO, FLT FUR
        ''')
        self.failUnlessEqual(variant.rep, {
                "ONE": 0x5500,
        })
    def test_rep_coastal_home(self):
        variant = load_variant('''
            [homes]
            TRE=ONE
            [borders]
            ONE=AMY TWO, FLT FUR
        ''')
        self.failUnlessEqual(variant.rep, {
                "ONE": 0x5500,
                "TRE": 0x4100,
        })
    def test_rep_bicoastal(self):
        variant = load_variant('''
            [borders]
            ONE=AMY TWO, (FLT NCS) FUR, (FLT SCS) SIX
        ''')
        self.failUnlessEqual(variant.rep, {
                "ONE": 0x5600,
        })
    def test_rep_bicoastal_sc(self):
        variant = load_variant('''
            [homes]
            UNO=ONE
            [borders]
            ONE=AMY TWO, (FLT NCS) FUR, (FLT SCS) SIX
        ''')
        self.failUnlessEqual(variant.rep, {
                "ONE": 0x5700,
        })
    def test_rep_bicoastal_home(self):
        variant = load_variant('''
            [homes]
            TRE=ONE
            [borders]
            ONE=AMY TWO, (FLT NCS) FUR, (FLT SCS) SIX
        ''')
        self.failUnlessEqual(variant.rep, {
                "ONE": 0x5700,
                "TRE": 0x4100,
        })
    def test_rep_two_inland(self):
        variant = load_variant('''
            [borders]
            ONE=AMY TWO
            TWO=AMY ONE
        ''')
        self.failUnlessEqual(variant.rep, {
                "ONE": 0x5000,
                "TWO": 0x5001,
        })
    def test_rep_two_inland_swapped(self):
        variant = load_variant('''
            [borders]
            TWO=AMY ONE
            ONE=AMY TWO
        ''')
        self.failUnlessEqual(variant.rep, {
                "ONE": 0x5000,
                "TWO": 0x5001,
        })
    def test_rep_categories(self):
        variant = load_variant('''
            [borders]
            ONE=AMY TWO, FLT TWO
            TWO=AMY ONE
        ''')
        self.failUnlessEqual(variant.rep, {
                "ONE": 0x5401,
                "TWO": 0x5000,
        })
    def test_rep_power(self):
        variant = load_variant('''
            [homes]
            ONE=TWO
        ''')
        self.failUnlessEqual(variant.rep, {
                "ONE": 0x4100,
        })
    def test_rep_powers(self):
        variant = load_variant('''
            [homes]
            ONE=TWO
            TRE=TWO
        ''')
        self.failUnlessEqual(variant.rep, {
                "ONE": 0x4100,
                "TRE": 0x4101,
        })
    def test_rep_type(self):
        variant = load_variant("")
        self.failUnlessEqual(type(variant.rep), Representation)
    def test_rep_standard(self):
        # Final exam: Does the standard map match the protocol?
        self.failUnlessEqual(standard.tokens(), protocol.default_rep)
    
    def test_mdf_empty(self):
        variant = load_variant("")
        mdf = MDF () ([], []) ()
        self.failUnlessEqual(variant.mdf(), mdf)
    def test_mdf_neutral(self):
        variant = load_variant('''
            [homes]
            UNO=
        ''')
        powers = variant.mdf().fold()[1]
        self.failUnlessEqual([], powers)
    def test_mdf_power(self):
        variant = load_variant('''
            [homes]
            ONE=
        ''')
        ONE = variant.rep["ONE"]
        powers = variant.mdf().fold()[1]
        self.failUnlessEqual([ONE], powers)
    def test_mdf_neutral_empty(self):
        variant = load_variant('''
            [homes]
            UNO=
        ''')
        centers = variant.mdf().fold()[2][0]
        self.failUnlessEqual([[UNO]], centers)
    def test_mdf_neutral_center(self):
        variant = load_variant('''
            [homes]
            UNO=ONE
            [borders]
            ONE=AMY
        ''')
        ONE = variant.rep["ONE"]
        centers = variant.mdf().fold()[2][0]
        self.failUnlessEqual([[UNO, ONE]], centers)
    def test_mdf_neutral_multiple(self):
        variant = load_variant('''
            [homes]
            UNO=ONE,TWO
            [borders]
            ONE=AMY TWO
            TWO=AMY ONE
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        centers = variant.mdf().fold()[2][0]
        self.failUnlessEqual([[UNO, ONE, TWO]], centers)
    def test_mdf_homes_empty(self):
        variant = load_variant('''
            [homes]
            ONE=
        ''')
        ONE = variant.rep["ONE"]
        centers = variant.mdf().fold()[2][0]
        self.failUnlessEqual([[ONE]], centers)
    def test_mdf_homes_center(self):
        variant = load_variant('''
            [homes]
            TRE=ONE
            [borders]
            ONE=AMY
        ''')
        ONE = variant.rep["ONE"]
        TRE = variant.rep["TRE"]
        centers = variant.mdf().fold()[2][0]
        self.failUnlessEqual([[TRE, ONE]], centers)
    def test_mdf_homes_multiple(self):
        variant = load_variant('''
            [homes]
            TRE=ONE,TWO
            [borders]
            ONE=AMY TWO
            TWO=AMY ONE
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        TRE = variant.rep["TRE"]
        centers = variant.mdf().fold()[2][0]
        self.failUnlessEqual([[TRE, ONE, TWO]], centers)
    def test_mdf_prov(self):
        variant = load_variant('''
            [borders]
            ONE=AMY
        ''')
        ONE = variant.rep["ONE"]
        provs = variant.mdf().fold()[2][1]
        self.failUnlessEqual(provs, [ONE])
    def test_mdf_provs(self):
        variant = load_variant('''
            [borders]
            ONE=AMY TWO
            TWO=AMY ONE
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        provs = variant.mdf().fold()[2][1]
        self.failUnlessEqual(provs, [ONE, TWO])
    def test_mdf_provs_without_center(self):
        variant = load_variant('''
            [homes]
            UNO=TWO
            [borders]
            ONE=AMY TWO
            TWO=AMY ONE
        ''')
        ONE = variant.rep["ONE"]
        provs = variant.mdf().fold()[2][1]
        self.failUnlessEqual(provs, [ONE])
    def test_mdf_provs_without_home(self):
        variant = load_variant('''
            [homes]
            TRE=TWO
            [borders]
            ONE=AMY TWO
            TWO=AMY ONE
        ''')
        ONE = variant.rep["ONE"]
        provs = variant.mdf().fold()[2][1]
        self.failUnlessEqual(provs, [ONE])
    def test_mdf_borders_empty(self):
        variant = load_variant('''
            [borders]
        ''')
        borders = variant.mdf().fold()[3]
        self.failUnlessEqual(borders, [])
    def test_mdf_borders_swiss(self):
        variant = load_variant('''
            [borders]
            ONE=AMY
        ''')
        ONE = variant.rep["ONE"]
        borders = variant.mdf().fold()[3]
        self.failUnlessEqual(borders, [[ONE, [AMY]]])
    def test_mdf_borders_inland(self):
        variant = load_variant('''
            [borders]
            ONE=AMY TWO TRE
            TWO=
            TRE=
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        TRE = variant.rep["TRE"]
        borders = variant.mdf().fold()[3]
        self.assertContains(borders, [ONE, [AMY, TWO, TRE]])
    def test_mdf_borders_island(self):
        variant = load_variant('''
            [borders]
            ONE=AMY, FLT TWO
            TWO=
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        borders = variant.mdf().fold()[3]
        self.assertContains(borders, [ONE, [AMY], [FLT, TWO]])
    def test_mdf_borders_sea(self):
        variant = load_variant('''
            [borders]
            ONE=FLT TWO TRE
            TWO=
            TRE=
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        TRE = variant.rep["TRE"]
        borders = variant.mdf().fold()[3]
        self.assertContains(borders, [ONE, [FLT, TWO, TRE]])
    def test_mdf_borders_lake(self):
        variant = load_variant('''
            [borders]
            ONE=FLT
        ''')
        ONE = variant.rep["ONE"]
        borders = variant.mdf().fold()[3]
        self.failUnlessEqual(borders, [[ONE, [FLT]]])
    def test_mdf_borders_coastal(self):
        variant = load_variant('''
            [borders]
            ONE=AMY TWO, FLT TRE
            TWO=
            TRE=
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        TRE = variant.rep["TRE"]
        borders = variant.mdf().fold()[3]
        self.assertContains(borders, [ONE, [AMY, TWO], [FLT, TRE]])
    def test_mdf_borders_coastlines(self):
        variant = load_variant('''
            [borders]
            ONE=AMY TWO, (FLT SCS) TRE, (FLT NCS) FUR
            TWO=
            TRE=
            FUR=
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        TRE = variant.rep["TRE"]
        FUR = variant.rep["FUR"]
        borders = variant.mdf().fold()[3]
        self.assertContains(borders,
            [ONE, [AMY, TWO], [[FLT, SCS], TRE], [[FLT, NCS], FUR]])
    def test_mdf_bordering_coastline(self):
        variant = load_variant('''
            [borders]
            ONE=FLT (TWO SCS)
            TWO=
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        borders = variant.mdf().fold()[3]
        self.assertContains(borders, [ONE, [FLT, [TWO, SCS]]])
    
    def test_sco_empty(self):
        variant = load_variant("")
        self.failUnlessEqual(variant.sco(), +SCO)
    def test_sco_neutral(self):
        variant = load_variant('''
            [homes]
            UNO=ONE,TWO
            [ownership]
            UNO=ONE,TWO
            [borders]
            ONE=AMY TWO
            TWO=AMY ONE
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        self.failUnlessEqual(variant.sco(), SCO (UNO, ONE, TWO))
    def test_sco_single(self):
        variant = load_variant('''
            [homes]
            ONE=TWO
            [ownership]
            ONE=TWO
            [borders]
            TWO=
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        self.failUnlessEqual(variant.sco(), SCO (ONE, TWO))
    def test_sco_multiple(self):
        variant = load_variant('''
            [homes]
            ONE=TWO
            TRE=FUR
            [ownership]
            ONE=TWO
            TRE=FUR
            [borders]
            TWO=
            FUR=
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        TRE = variant.rep["TRE"]
        FUR = variant.rep["FUR"]
        self.failUnlessEqual(variant.sco(), SCO (ONE, TWO) (TRE, FUR))
    def test_sco_position(self):
        variant = load_variant('''
            [homes]
            ONE=FUR
            TRE=TWO
            [positions]
            ONE=FLT TWO
            TRE=AMY FUR
            [borders]
            TWO=AMY FUR, FLT FUR
            FUR=AMY TWO, FLT TWO
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        TRE = variant.rep["TRE"]
        FUR = variant.rep["FUR"]
        self.failUnlessEqual(variant.sco(), SCO (ONE, TWO) (TRE, FUR) (UNO))
    def test_sco_position_neutral(self):
        variant = load_variant('''
            [homes]
            ONE=TWO
            TRE=TWO
            [positions]
            ONE=AMY FUR
            TRE=AMY FIV
            [borders]
            TWO=AMY FUR FIV, FLT FUR
            FUR=AMY TWO FIV, FLT TWO
            FIV=AMY TWO FUR
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        TRE = variant.rep["TRE"]
        FIV = variant.rep["FIV"]
        self.failUnlessEqual(variant.sco(), SCO (ONE) (TRE) (UNO, TWO))
    
    def test_now_empty(self):
        variant = load_variant("")
        self.failUnlessEqual(variant.now(), NOW (SPR, 0))
    def test_now_season(self):
        variant = load_variant('''
            [variant]
            start=WIN 2000
        ''')
        season = variant.now().fold()[1]
        self.failUnlessEqual(season, [WIN, 2000])
    def test_now_army(self):
        variant = load_variant('''
            [homes]
            ONE=TWO
            [positions]
            ONE=AMY TWO
            [borders]
            TWO=AMY
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        units = variant.now().fold()[2:]
        self.failUnlessEqual(units, [[ONE, AMY, TWO]])
    def test_now_fleet(self):
        variant = load_variant('''
            [homes]
            ONE=TWO
            [positions]
            ONE=FLT TWO
            [borders]
            TWO=FLT
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        units = variant.now().fold()[2:]
        self.failUnlessEqual(units, [[ONE, FLT, TWO]])
    def test_now_bicoastal(self):
        variant = load_variant('''
            [homes]
            ONE=TWO
            [positions]
            ONE=FLT TWO NCS
            [borders]
            TWO=(FLT SCS), (FLT NCS)
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        units = variant.now().fold()[2:]
        self.failUnlessEqual(units, [[ONE, FLT, [TWO, NCS]]])
    def test_now_multiple(self):
        variant = load_variant('''
            [homes]
            ONE=TWO
            TRE=FUR
            [positions]
            ONE=AMY TWO
            TRE=AMY FUR
            [borders]
            TWO=
            FUR=
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        TRE = variant.rep["TRE"]
        FUR = variant.rep["FUR"]
        units = variant.now().fold()[2:]
        self.failUnlessEqual(units, [[ONE, AMY, TWO], [TRE, AMY, FUR]])
    def test_now_double(self):
        variant = load_variant('''
            [homes]
            ONE=TWO
            TRE=FUR
            [positions]
            ONE=AMY TWO, AMY TRE
            [borders]
            TWO=
            TRE=
        ''')
        ONE = variant.rep["ONE"]
        TWO = variant.rep["TWO"]
        TRE = variant.rep["TRE"]
        units = variant.now().fold()[2:]
        self.failUnlessEqual(units, [[ONE, AMY, TWO], [ONE, AMY, TRE]])

class StandardVariantTests(unittest.TestCase):
    "Tests for the standard map variant"
    variant = "standard"
    def failUnlessValid(self, message):
        result = Validator().validate_server_message(message)
        self.failIf(result, result)
    def test_mdf_valid(self):
        self.failUnlessValid(variants[self.variant].mdf())
    def test_sco_valid(self):
        self.failUnlessValid(variants[self.variant].sco())
    def test_now_valid(self):
        self.failUnlessValid(variants[self.variant].sco())

class Map_Bugfix(unittest.TestCase):
    ''' Tests to reproduce bugs related to the Map class'''
    def test_empty_UNO(self):
        ''' Test whether Map can define maps with no non-home supply centers.'''
        # Almost Standard...
        mdf = '''
            MDF (AUS ENG FRA GER ITA RUS TUR)
            (((AUS bud tri vie)(ENG edi lon lvp)(FRA bre mar par)
              (GER ber kie mun)(ITA nap rom ven)(RUS mos sev stp war)
              (TUR ank con smy bel bul den gre hol nwy por rum ser spa swe tun)
              (UNO))
             (alb apu arm boh bur cly fin gal gas lvn naf pic pie pru ruh sil syr
              tus tyr ukr wal yor adr aeg bal bar bla gob eas ech hel ion iri gol
              mao nao nth nwg ska tys wes))
            ((adr(FLT alb apu ven tri ion))
             (aeg(FLT gre (bul scs) con smy eas ion))
             (alb(AMY tri gre ser)(FLT adr tri gre ion))
             (ank(AMY arm con smy)(FLT bla arm con))
             (apu(AMY ven nap rom)(FLT ven adr ion nap))
             (arm(AMY smy syr ank sev)(FLT ank sev bla))
             (bal(FLT lvn pru ber kie den swe gob))
             (bar(FLT nwg (stp ncs) nwy))
             (bel(AMY hol pic ruh bur)(FLT ech nth hol pic))
             (ber(AMY kie pru sil mun)(FLT kie bal pru))
             (bla(FLT rum sev arm ank con (bul ecs)))
             (boh(AMY mun sil gal vie tyr))
             (gob(FLT swe fin (stp scs) lvn bal))
             (bre(AMY pic gas par)(FLT mao ech pic gas))
             (bud(AMY vie gal rum ser tri))
             (bul((FLT ECS) con bla rum)(AMY gre con ser rum)((FLT SCS) gre aeg con))
             (bur(AMY mar gas par pic bel ruh mun))
             (cly(AMY edi lvp)(FLT edi lvp nao nwg))
             (con(AMY bul ank smy)(FLT (bul scs) (bul ecs) bla ank smy aeg))
             (den(AMY swe kie)(FLT hel nth swe bal kie ska))
             (eas(FLT syr smy aeg ion))
             (edi(AMY lvp yor cly)(FLT nth nwg cly yor))
             (ech(FLT mao iri wal lon nth bel pic bre))
             (fin(AMY swe stp nwy)(FLT swe (stp scs) gob))
             (gal(AMY war ukr rum bud vie boh sil))
             (gas(AMY par bur mar spa bre)(FLT (spa ncs) mao bre))
             (gre(AMY bul alb ser)(FLT (bul scs) aeg ion alb))
             (hel(FLT nth den kie hol))
             (hol(AMY bel kie ruh)(FLT bel nth hel kie))
             (ion(FLT tun tys nap apu adr alb gre aeg eas))
             (iri(FLT nao lvp wal ech mao))
             (kie(AMY hol den ber mun ruh)(FLT hol hel den bal ber))
             (lon(AMY yor wal)(FLT yor nth ech wal))
             (lvn(AMY pru stp mos war)(FLT pru bal gob (stp scs)))
             (lvp(AMY wal edi yor cly)(FLT wal iri nao cly))
             (gol(FLT (spa scs) mar pie tus tys wes))
             (mao(FLT nao iri ech bre gas (spa ncs) por (spa scs) naf wes))
             (mar(AMY spa pie gas bur)(FLT (spa scs) gol pie))
             (mos(AMY stp lvn war ukr sev))
             (mun(AMY bur ruh kie ber sil boh tyr))
             (naf(AMY tun)(FLT mao wes tun))
             (nao(FLT nwg lvp iri mao cly))
             (nap(AMY rom apu)(FLT rom tys ion apu))
             (nwy(AMY fin stp swe)(FLT ska nth nwg bar (stp ncs) swe))
             (nth(FLT yor edi nwg nwy ska den hel hol bel ech lon))
             (nwg(FLT nao bar nwy nth cly edi))
             (par(AMY bre pic bur gas))
             (pic(AMY bur par bre bel)(FLT bre ech bel))
             (pie(AMY mar tus ven tyr)(FLT mar gol tus))
             (por(AMY spa)(FLT mao (spa ncs) (spa scs)))
             (pru(AMY war sil ber lvn)(FLT ber bal lvn))
             (rom(AMY tus nap ven apu)(FLT tus tys nap))
             (ruh(AMY bur bel hol kie mun))
             (rum(AMY ser bud gal ukr sev bul)(FLT sev bla (bul ecs)))
             (ser(AMY tri bud rum bul gre alb))
             (sev(AMY ukr mos rum arm)(FLT rum bla arm))
             (sil(AMY mun ber pru war gal boh))
             (ska(FLT nth nwy den swe))
             (smy(AMY syr con ank arm)(FLT syr eas aeg con))
             (spa(AMY gas por mar)((FLT NCS) gas mao por)((FLT SCS) por wes gol mar mao))
             (stp(AMY fin lvn nwy mos)((FLT NCS) bar nwy)((FLT SCS) fin lvn gob))
             (swe(AMY fin den nwy)(FLT fin gob bal den ska nwy))
             (syr(AMY smy arm)(FLT eas smy))
             (tri(AMY tyr vie bud ser alb ven)(FLT alb adr ven))
             (tun(AMY naf)(FLT naf wes tys ion))
             (tus(AMY rom pie ven)(FLT rom tys gol pie))
             (tyr(AMY mun boh vie tri ven pie))
             (tys(FLT wes gol tus rom nap ion tun))
             (ukr(AMY rum gal war mos sev))
             (ven(AMY tyr tus rom pie apu tri)(FLT apu adr tri))
             (vie(AMY tyr boh gal bud tri))
             (wal(AMY lvp lon yor)(FLT lvp iri ech lon))
             (war(AMY sil pru lvn mos ukr gal))
             (wes(FLT mao (spa scs) gol tys tun naf))
             (yor(AMY edi lon lvp wal)(FLT edi nth lon))
            )
        '''#'''
        options = Variant("testing")
        mdf = options.rep.translate(mdf)
        game_map = Map(options)
        msg = game_map.define(mdf)
        self.failIf(msg, msg)
    def test_island_Pale(self):
        "Check that Map can handle island provinces."
        variant = load_variant('''
            [borders]
            ONE=AMY, FLT TWO, FLT TRE
            TWO=FLT TRE, FLT ONE
            TRE=FLT TWO, FLT ONE
        ''')
        game_map = Map(variant)
        prov = variant.rep['ONE']
        self.failUnless(prov.category_name().split()[0] == 'Coastal')
        coast = game_map.coasts[(AMY, prov, None)]
        self.failUnless(coast.is_valid())
        self.failUnless(coast.province.is_valid())
    def test_island_province(self):
        ''' Test whether Province can define island spaces.'''
        island = Province(NAF, [[AMY], [FLT, MAO, WES]], None)
        self.failUnless(island.is_valid())
    @fails  # MDF messages no longer get cached.
    def test_cache_mdf(self):
        opts = Variant('testing')
        Map(opts).handle_MDF(standard.mdf())
        new_map = Map(opts)
        self.failUnless(new_map.valid)
    def test_power_names(self):
        variant = load_variant('''
            [powers]
            ONE=Somebody,Someone's
            [homes]
            ONE=
            [borders]
            TWO=AMY TRE
            TRE=AMY TWO
        ''')
        board = Map(variant)
        power = board.powers[variant.rep["ONE"]]
        self.failUnlessEqual(power.name, "Somebody")
    def test_province_names(self):
        variant = load_variant('''
            [provinces]
            TWO=Somewhere
            [homes]
            ONE=
            [borders]
            TWO=AMY TRE
            TRE=AMY TWO
        ''')
        board = Map(variant)
        province = board.spaces[variant.rep["TWO"]]
        self.failUnlessEqual(province.name, "Somewhere")

class Coast_Bugfix(unittest.TestCase):
    ''' Tests to reproduce bugs related to the Coast class'''
    def test_infinite_convoy(self):
        # Originally notices in the Americas4 variant.
        variant = load_variant('''
            [borders]
            ALA=AMY NCA NWT, FLT BEA BER GOA NCA NPO NWT
            ORE=AMY CAL NCA, FLT CAL GOA NCA NPO
            NWT=AMY ALA NCA, FLT ALA ARC BEA HUD LAB
            CAL=AMY ORE, FLT GSC NPO ORE
            NCA=AMY ALA NWT ORE, FLT ALA GOA ORE
            ACH=FLT ECB MAO SAR
            AGU=FLT CGU HUM SPO
            ARC=FLT BEA LAB NAO NWT
            APP=FLT FST GOM
            BBL=FLT BGR RLP SAO
            BEA=FLT ALA ARC BER NWT
            BER=FLT ALA BEA NPO
            BGR=FLT BBL DRA SAO
            BTR=FLT NAO NTH SAR STH
            CGU=FLT AGU DRA SPO
            CHG=FLT GFO GOG GOP MPO
            COB=FLT GBA MAO SAO
            COM=FLT GOT MPO SOC
            COP=FLT GOG HUM SPO
            CPO=FLT MPO NPO SPO
            DRA=FLT BGR CGU SAO SPO
            ECB=FLT ACH GOU GOV NCB SAR WCB
            FST=FLT APP GOM SCH
            GBA=FLT COB PBA SAO
            GOA=FLT ALA NCA NPO ORE
            GOC=FLT GOM
            GFO=FLT CHG GOT MPO
            GOG=FLT CHG COP GOP SPO
            GOH=FLT WCB
            GOM=FLT APP FST GOC SOY
            GOP=FLT CHG GOG
            GOS=FLT LAB NAO
            GOT=FLT COM GFO MPO
            GOU=FLT ECB GOV MOS WCB
            GOV=FLT ECB GOU
            GSC=FLT CAL MPO NPO
            GSE=FLT MAO MBA
            HUD=FLT LAB NWT
            HUM=FLT AGU COP SPO
            LAB=FLT ARC GOS HUD NAO NWT
            MAO=FLT ACH COB GSE MBA NAO SAO SAR
            MAS=FLT NAO NTH
            MBA=FLT GSE MAO
            MOS=FLT GOU WCB
            MPO=FLT CHG COM CPO GFO GOT GSC NPO SOC SPO
            NAO=FLT ARC BTR GOS LAB MAO MAS NTH SAR
            NCB=FLT ECB SCH SOY WCB
            NTH=FLT BTR MAS NAO STH
            NPO=FLT ALA BER CAL CPO GOA GSC MPO ORE
            PBA=FLT GBA RLP SAO
            RLP=FLT BBL PBA SAO
            SAO=FLT BBL BGR COB DRA GBA MAO PBA RLP
            SAR=FLT ACH BTR ECB MAO NAO SCH STH
            SCH=FLT FST NCB SAR STH
            STH=FLT BTR NTH SAR SCH
            SOC=FLT COM MPO
            SOY=FLT GOM NCB WCB
            SPO=FLT AGU CGU COP CPO DRA GOG HUM MPO
            WCB=FLT ECB GOH GOU MOS NCB SOY
        ''')
        board = Map(variant)
        Alaska = board.spaces[variant.rep['ALA']]
        Oregon = board.coasts[(AMY, variant.rep['ORE'], None)]
        start = time.time()
        results = Oregon.convoy_routes(Alaska, board)
        finish = time.time()
        self.failUnlessEqual(results, [])
        self.failUnless(finish - start < 1, "convoy_routes() took too long.")

class Order_Strings(unittest.TestCase):
    def check_order(self, order, result):
        order = createUnitOrder(order, standard_map.powers[FRA],
                standard_map, DatcOptions())
        self.failUnlessEqual(str(order), result)
    def test_hold_string(self):
        self.check_order([[FRA, FLT, BRE], HLD], 'Fleet Brest HOLD')
    def test_hold_coastal(self):
        self.check_order([[FRA, FLT, [SPA, SCS]], HLD],
                'Fleet Spain (south coast) HOLD')
    def test_move_string(self):
        self.check_order([[FRA, FLT, BRE], MTO, MAO],
                'Fleet Brest -> Mid-Atlantic Ocean')
    def test_move_to_coast(self):
        self.check_order([[FRA, FLT, MAO], MTO, [SPA, SCS]],
                'Fleet Mid-Atlantic Ocean -> Spain (south coast)')
    def test_move_from_coast(self):
        self.check_order([[FRA, FLT, [SPA, SCS]], MTO, MAO],
                'Fleet Spain (south coast) -> Mid-Atlantic Ocean')
    
    def test_support_hold_string(self):
        self.check_order([[FRA, FLT, BRE], SUP, MAO, HLD],
                'Fleet Brest SUPPORT Fleet Mid-Atlantic Ocean')
    def test_support_hold_ambiguous(self):
        # Perhaps not the best form, but it works.
        self.check_order([[FRA, FLT, BRE], SUP, GAS, HLD],
                'Fleet Brest SUPPORT  Gascony')
    def test_support_hold_foreign(self):
        self.check_order([[FRA, FLT, BRE], SUP, LON, HLD],
                'Fleet Brest SUPPORT English Fleet London')
    def test_support_move_string(self):
        self.check_order([[FRA, AMY, PAR], SUP, MAR, MTO, GAS],
                'Army Paris SUPPORT Army Marseilles -> Gascony')
    
    def test_convoying_string(self):
        self.check_order([[FRA, FLT, BRE], CVY, MAR, CTO, GAS],
                'Fleet Brest CONVOY Army Marseilles -> Gascony')
    def test_convoyed_string(self):
        self.check_order([[FRA, AMY, MAR], CTO, GAS, VIA, [BRE]],
                'Army Marseilles -> Brest -> Gascony')
    def test_convoyed_long(self):
        self.check_order([[FRA, AMY, MAR], CTO, GAS, VIA, [GOL, WES, MAO]],
                'Army Marseilles -> Gulf of Lyon -> Western Mediterranean Sea -> Mid-Atlantic Ocean -> Gascony')
    
    def test_retreat_string(self):
        self.check_order([[FRA, AMY, PAR], RTO, GAS],
                'Army Paris -> Gascony')
    def test_disband_string(self):
        self.check_order([[FRA, AMY, PAR], DSB],
                'Army Paris DISBAND')
    
    def test_build_string(self):
        self.check_order([[FRA, AMY, PAR], BLD],
                'Builds an army in Paris')
    @fails
    def test_build_foreign(self):
        self.check_order([[GER, AMY, PAR], BLD],
                'Builds a German army in Paris')
    def test_remove_string(self):
        self.check_order([[FRA, AMY, PAR], REM],
                'Removes the army in Paris')
    @fails
    def test_remove_foreign(self):
        self.check_order([[GER, AMY, PAR], REM],
                'Removes the German army in Paris')
    def test_waive_string(self):
        self.check_order([FRA, WVE],
                'Waives a build')
    @fails
    def test_waive_foreign(self):
        self.check_order([GER, WVE],
                'Waives a German build')

class Gameboard_Doctests(unittest.TestCase):
    ''' Tests that were once doctests, but no longer work as such.'''
    def test_map_define(self):
        ''' Test the creation of a new map from a simple MDF.'''
        
        mdf = MDF (ENG, FRA) ([
            (ENG, EDI, LON),
            (FRA, BRE, PAR),
            ([ENG, FRA], BEL, HOL),
            (UNO, SPA, NWY),
        ], [ECH, NTH, PIC]) (
            (EDI, [AMY, LON], [FLT, NTH]),
            (LON, [AMY, EDI], [FLT, NTH, ECH]),
            (BRE, [AMY, PAR, PIC, SPA], [FLT, ECH, PIC, (SPA, NCS)]),
            (PAR, [AMY, PAR, SPA, PIC]),
            (BEL, [AMY, PIC, HOL], [FLT, NTH, ECH, PIC, HOL]),
            (HOL, [AMY, BEL], [FLT, NTH]),
            (SPA, [AMY, PAR, BRE], [(FLT, NCS), BRE]),
            (NWY, [AMY], [FLT, NTH]),
            (ECH, [FLT, NTH, BRE, LON, BEL, PIC]),
            (NTH, [FLT, ECH, BEL, HOL, LON, NWY, EDI]),
            (PIC, [AMY, BRE, PAR, BEL], [FLT, ECH, BRE, BEL]),
        )
        
        self.failIf(Validator().validate_server_message(mdf),
                'Invalid MDF message')
        m = Map(Variant('simplified'))
        self.failIf(m.valid, 'Map valid before MDF')
        result = m.define(mdf)
        self.failIf(result, result)
    def test_turn_compare_lt(self):
        spring = Turn(SPR, 1901)
        fall = Turn(FAL, 1901)
        self.failUnlessEqual(cmp(spring, fall), -1)
    def test_turn_compare_gt(self):
        spring = Turn(SPR, 1901)
        fall = Turn(FAL, 1901)
        self.failUnlessEqual(cmp(fall, spring.key), 1)
    def test_turn_compare_eq(self):
        fall = Turn(FAL, 1901)
        self.failUnlessEqual(cmp(fall, fall.key), 0)
    def test_turn_phase_hex(self):
        t = Turn(SUM, 1901)
        self.failUnlessEqual(t.phase(), 0x40)
    def test_turn_phase_name(self):
        t = Turn(SUM, 1901)
        self.failUnlessEqual(t.phase(), Turn.retreat_phase)

if __name__ == '__main__': unittest.main()
