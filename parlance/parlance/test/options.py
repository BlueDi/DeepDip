r'''DATC option compliance test cases for the Parlance judge
    Copyright (C) 2001-2008  Lucas B. Kruijswijk and Eric Wald
    
    This module tests each option of each disputable item listed in the
    DATC document, using collections of test cases from that document.
    Unfortunately, some of the options have not yet been implemented.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

import unittest

from parlance.functions import fails
from parlance.tokens    import *
from parlance.xtended   import *

from parlance.test.datc import DiplomacyAdjudicatorTestCase

class DATC_4_A(DiplomacyAdjudicatorTestCase):
    ''' 4.A.  CONVOY ISSUES
        Note: This program does not support incomplete paradox resolutions.
        Thus, 4.A.2(a) and (c) are unavailable.
        Note that 4.A.3(b) and (c) override 4.A.4(b),
        and 4.A.2(c) overrides 4.A.5(b).
    '''#'''
    
    def test_4A1_any(self):
        '4.A.1.a  MULTI-ROUTE CONVOY DISRUPTION'
        # From 6.F.9
        self.judge.datc.datc_4a1 = 'a'
        steady_state = [
            [ENG, FLT, NTH],
            [ENG, AMY, LON],
            [FRA, FLT, BRE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, ECH],
            [FRA, FLT, MAO],
        ])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, BRE), SUP, (FRA, FLT, MAO), MTO, ECH])
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, ECH])
        self.assertMapState(steady_state + [
            [ENG, FLT, ECH, MRT],
            [FRA, FLT, ECH],
        ])
    def test_4A1_all(self):
        '4.A.1.b  MULTI-ROUTE CONVOY DISRUPTION'
        # From 6.F.9
        self.judge.datc.datc_4a1 = 'b'
        steady_state = [
            [ENG, FLT, NTH],
            [FRA, FLT, BRE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, ECH],
            [ENG, AMY, LON],
            [FRA, FLT, MAO],
        ])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, BRE), SUP, (FRA, FLT, MAO), MTO, ECH])
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, ECH])
        self.assertMapState(steady_state + [
            [ENG, AMY, BEL],
            [ENG, FLT, ECH, MRT],
            [FRA, FLT, ECH],
        ])
    def test_4A2_1982(self):
        '4.A.2.b  CONVOY DISRUPTION PARADOXES'
        # Combination of 6.F.14, 6.F.18, and 6.F.24
        self.judge.datc.datc_4a2 = 'b'
        steady_state = [
            [RUS, FLT, SEV],
            [TUR, AMY, ANK],
            
            [ITA, FLT, ION],
            [ITA, FLT, TYS],
            [TUR, FLT, AEG],
            [TUR, FLT, GRE],
            
            [ENG, FLT, LON],
            [ENG, FLT, IRI],
            [ENG, FLT, MAO],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [FRA, FLT, BEL],
            [GER, AMY, NWY],
        ]
        
        self.init_state(SPR, 1901, steady_state + [
            [RUS, FLT, RUM],
            [TUR, FLT, BLA],
            
            [ITA, AMY, TUN],
            [AUS, FLT, NAP],
            
            [ENG, FLT, EDI],
            [GER, FLT, NTH],
        ])
        
        self.legalOrder(RUS, [(RUS, FLT, SEV), SUP, (RUS, FLT, RUM), MTO, BLA])
        self.legalOrder(RUS, [(RUS, FLT, RUM), MTO, BLA])
        self.legalOrder(TUR, [(TUR, AMY, ANK), CTO, SEV, VIA, [BLA]])
        self.legalOrder(TUR, [(TUR, FLT, BLA), CVY, (TUR, AMY, ANK), CTO, SEV])
        
        self.legalOrder(ITA, [(ITA, FLT, ION), CVY, (ITA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, AMY, TUN), CTO, NAP, VIA, [ION]])
        self.legalOrder(ITA, [(ITA, FLT, TYS), SUP, (ITA, AMY, TUN), MTO, NAP])
        self.legalOrder(AUS, [(AUS, FLT, NAP), SUP, (ITA, FLT, ION)])
        self.legalOrder(TUR, [(TUR, FLT, AEG), SUP, (TUR, FLT, GRE), MTO, ION])
        self.legalOrder(TUR, [(TUR, FLT, GRE), MTO, ION])
        
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, IRI), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, MAO), SUP, (ENG, FLT, IRI), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(FRA, [(FRA, FLT, BEL), SUP, (FRA, FLT, ECH)])
        self.legalOrder(GER, [(GER, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(GER, [(GER, FLT, NTH), CVY, (GER, AMY, NWY), CTO, BEL])
        
        self.assertMapState(steady_state + [
            [RUS, FLT, BLA],
            [TUR, FLT, BLA, MRT],
            
            [ITA, AMY, NAP],
            [AUS, FLT, NAP, MRT],
            
            [ENG, FLT, NTH],
            [GER, FLT, NTH, MRT],
        ])
    def test_4A2_Szykman(self):
        '4.A.2.d  CONVOY DISRUPTION PARADOXES'
        # Combination of 6.F.14, 6.F.18, and 6.F.24
        self.judge.datc.datc_4a2 = 'd'
        steady_state = [
            [RUS, FLT, SEV],
            [TUR, AMY, ANK],
            
            [ITA, FLT, ION],
            [ITA, AMY, TUN],
            [ITA, FLT, TYS],
            [AUS, FLT, NAP],
            [TUR, FLT, AEG],
            [TUR, FLT, GRE],
            
            [ENG, FLT, LON],
            [ENG, FLT, IRI],
            [ENG, FLT, MAO],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [FRA, FLT, BEL],
            [GER, AMY, NWY],
        ]
        
        self.init_state(SPR, 1901, steady_state + [
            [RUS, FLT, RUM],
            [TUR, FLT, BLA],
            
            [ENG, FLT, EDI],
            [GER, FLT, NTH],
        ])
        
        self.legalOrder(RUS, [(RUS, FLT, SEV), SUP, (RUS, FLT, RUM), MTO, BLA])
        self.legalOrder(RUS, [(RUS, FLT, RUM), MTO, BLA])
        self.legalOrder(TUR, [(TUR, AMY, ANK), CTO, SEV, VIA, [BLA]])
        self.legalOrder(TUR, [(TUR, FLT, BLA), CVY, (TUR, AMY, ANK), CTO, SEV])
        
        self.legalOrder(ITA, [(ITA, FLT, ION), CVY, (ITA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, AMY, TUN), CTO, NAP, VIA, [ION]])
        self.legalOrder(ITA, [(ITA, FLT, TYS), SUP, (ITA, AMY, TUN), MTO, NAP])
        self.legalOrder(AUS, [(AUS, FLT, NAP), SUP, (ITA, FLT, ION)])
        self.legalOrder(TUR, [(TUR, FLT, AEG), SUP, (TUR, FLT, GRE), MTO, ION])
        self.legalOrder(TUR, [(TUR, FLT, GRE), MTO, ION])
        
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, IRI), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, MAO), SUP, (ENG, FLT, IRI), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(FRA, [(FRA, FLT, BEL), SUP, (FRA, FLT, ECH)])
        self.legalOrder(GER, [(GER, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(GER, [(GER, FLT, NTH), CVY, (GER, AMY, NWY), CTO, BEL])
        
        self.assertMapState(steady_state + [
            [RUS, FLT, BLA],
            [TUR, FLT, BLA, MRT],
            
            [ENG, FLT, NTH],
            [GER, FLT, NTH, MRT],
        ])
    def test_4A2_Hold(self):
        '4.A.2.e  CONVOY DISRUPTION PARADOXES'
        # Combination of 6.F.14, 6.F.18, and 6.F.24
        self.judge.datc.datc_4a2 = 'e'
        steady_state = [
            [RUS, FLT, SEV],
            [RUS, FLT, RUM],
            [TUR, FLT, BLA],
            [TUR, AMY, ANK],
            
            [ITA, FLT, ION],
            [ITA, AMY, TUN],
            [ITA, FLT, TYS],
            [AUS, FLT, NAP],
            [TUR, FLT, AEG],
            [TUR, FLT, GRE],
            
            [ENG, FLT, LON],
            [ENG, FLT, IRI],
            [ENG, FLT, MAO],
            [ENG, FLT, EDI],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [FRA, FLT, BEL],
            [GER, FLT, NTH],
            [GER, AMY, NWY],
        ]
        
        self.init_state(SPR, 1901, steady_state)
        
        self.legalOrder(RUS, [(RUS, FLT, SEV), SUP, (RUS, FLT, RUM), MTO, BLA])
        self.legalOrder(RUS, [(RUS, FLT, RUM), MTO, BLA])
        self.legalOrder(TUR, [(TUR, AMY, ANK), CTO, SEV, VIA, [BLA]])
        self.legalOrder(TUR, [(TUR, FLT, BLA), CVY, (TUR, AMY, ANK), CTO, SEV])
        
        self.legalOrder(ITA, [(ITA, FLT, ION), CVY, (ITA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, AMY, TUN), CTO, NAP, VIA, [ION]])
        self.legalOrder(ITA, [(ITA, FLT, TYS), SUP, (ITA, AMY, TUN), MTO, NAP])
        self.legalOrder(AUS, [(AUS, FLT, NAP), SUP, (ITA, FLT, ION)])
        self.legalOrder(TUR, [(TUR, FLT, AEG), SUP, (TUR, FLT, GRE), MTO, ION])
        self.legalOrder(TUR, [(TUR, FLT, GRE), MTO, ION])
        
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, IRI), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, MAO), SUP, (ENG, FLT, IRI), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(FRA, [(FRA, FLT, BEL), SUP, (FRA, FLT, ECH)])
        self.legalOrder(GER, [(GER, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(GER, [(GER, FLT, NTH), CVY, (GER, AMY, NWY), CTO, BEL])
        
        self.assertMapState(steady_state)
    def test_4A2_DPTG(self):
        '4.A.2.f  CONVOY DISRUPTION PARADOXES'
        # Combination of 6.F.14, 6.F.18, and 6.F.24
        self.judge.datc.datc_4a2 = 'f'
        steady_state = [
            [RUS, FLT, SEV],
            [TUR, AMY, ANK],
            
            [ITA, FLT, ION],
            [ITA, AMY, TUN],
            [ITA, FLT, TYS],
            [AUS, FLT, NAP],
            [TUR, FLT, AEG],
            [TUR, FLT, GRE],
            
            [ENG, FLT, LON],
            [ENG, FLT, IRI],
            [ENG, FLT, MAO],
            [ENG, FLT, EDI],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [FRA, FLT, BEL],
            [GER, FLT, NTH],
            [GER, AMY, NWY],
        ]
        
        self.init_state(SPR, 1901, steady_state + [
            [RUS, FLT, RUM],
            [TUR, FLT, BLA],
        ])
        
        self.legalOrder(RUS, [(RUS, FLT, SEV), SUP, (RUS, FLT, RUM), MTO, BLA])
        self.legalOrder(RUS, [(RUS, FLT, RUM), MTO, BLA])
        self.legalOrder(TUR, [(TUR, AMY, ANK), CTO, SEV, VIA, [BLA]])
        self.legalOrder(TUR, [(TUR, FLT, BLA), CVY, (TUR, AMY, ANK), CTO, SEV])
        
        self.legalOrder(ITA, [(ITA, FLT, ION), CVY, (ITA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, AMY, TUN), CTO, NAP, VIA, [ION]])
        self.legalOrder(ITA, [(ITA, FLT, TYS), SUP, (ITA, AMY, TUN), MTO, NAP])
        self.legalOrder(AUS, [(AUS, FLT, NAP), SUP, (ITA, FLT, ION)])
        self.legalOrder(TUR, [(TUR, FLT, AEG), SUP, (TUR, FLT, GRE), MTO, ION])
        self.legalOrder(TUR, [(TUR, FLT, GRE), MTO, ION])
        
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, IRI), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, MAO), SUP, (ENG, FLT, IRI), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(FRA, [(FRA, FLT, BEL), SUP, (FRA, FLT, ECH)])
        self.legalOrder(GER, [(GER, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(GER, [(GER, FLT, NTH), CVY, (GER, AMY, NWY), CTO, BEL])
        
        self.assertMapState(steady_state + [
            [RUS, FLT, BLA],
            [TUR, FLT, BLA, MRT],
        ])
    def test_4A3_1971(self):
        '4.A.3.a  CONVOYING TO ADJACENT PLACE'
        # 6.G.1, 6.G.2, 6.G.3, 6.G.4, and an implicit convoy test
        self.judge.datc.datc_4a3 = 'a'
        steady_state = [
            [FRA, AMY, BUR],
            [FRA, AMY, PIC],
            [FRA, FLT, MAO],
            [TUR, AMY, APU],
            [TUR, AMY, ROM],
            [TUR, FLT, AEG],
            [ITA, AMY, NAP],
            [GER, FLT, SKA],
            [AUS, FLT, ADR],
            [TUR, FLT, BLA],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, FLT, BRE],
            [ENG, FLT, ECH],
            [TUR, FLT, GRE],
            [ITA, FLT, ION],
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
            [AUS, AMY, TRI],
            [ITA, AMY, VEN],
            [TUR, AMY, ANK],
        ])
        self.legalOrder(FRA, [(FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, AMY, BUR), SUP, (FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, MAO), SUP, (FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (FRA, AMY, PIC), CTO, BEL])
        self.legalOrder(TUR, [(TUR, FLT, GRE), MTO, ION])
        self.legalOrder(TUR, [(TUR, AMY, APU), MTO, NAP])
        self.legalOrder(TUR, [(TUR, AMY, ROM), SUP, (TUR, AMY, APU), MTO, NAP])
        self.legalOrder(TUR, [(TUR, FLT, AEG), SUP, (TUR, FLT, GRE), MTO, ION])
        self.legalOrder(ITA, [(ITA, FLT, ION), CVY, (TUR, AMY, APU), CTO, NAP])
        self.legalOrder(ITA, [(ITA, AMY, NAP), MTO, APU])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.legalOrder(GER, [(GER, FLT, SKA), CVY, (ENG, AMY, NWY), CTO, SWE])
        self.legalOrder(AUS, [(AUS, AMY, TRI), MTO, VEN])
        self.legalOrder(AUS, [(AUS, FLT, ADR), CVY, (AUS, AMY, TRI), CTO, VEN])
        self.legalOrder(ITA, [(ITA, AMY, VEN), MTO, TRI])
        self.legalOrder(TUR, [(TUR, AMY, ANK), MTO, SEV])
        self.legalOrder(TUR, [(TUR, FLT, BLA), CVY, (TUR, AMY, ANK), CTO, SEV])
        self.assertMapState(steady_state + [
            [FRA, FLT, ECH],
            [ENG, FLT, ECH, MRT],
            [TUR, FLT, ION],
            [ITA, FLT, ION, MRT],
            [ENG, AMY, SWE],
            [RUS, AMY, NWY],
            [AUS, AMY, VEN],
            [ITA, AMY, TRI],
            [TUR, AMY, SEV],
        ])
    def test_4A3_Walker(self):
        '4.A.3.b  CONVOYING TO ADJACENT PLACE'
        # 6.G.1, 6.G.2, 6.G.3, 6.G.4, and an implicit convoy test
        self.judge.datc.datc_4a3 = 'b'
        steady_state = [
            [FRA, AMY, BUR],
            [FRA, FLT, MAO],
            [TUR, AMY, APU],
            [TUR, AMY, ROM],
            [TUR, FLT, AEG],
            [ITA, AMY, NAP],
            [GER, FLT, SKA],
            [AUS, FLT, ADR],
            [TUR, FLT, BLA],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, AMY, PIC],
            [FRA, FLT, BRE],
            [ENG, FLT, ECH],
            [TUR, FLT, GRE],
            [ITA, FLT, ION],
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
            [AUS, AMY, TRI],
            [ITA, AMY, VEN],
            [TUR, AMY, ANK],
        ])
        self.legalOrder(FRA, [(FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, AMY, BUR), SUP, (FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, MAO), SUP, (FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (FRA, AMY, PIC), CTO, BEL])
        self.legalOrder(TUR, [(TUR, FLT, GRE), MTO, ION])
        self.legalOrder(TUR, [(TUR, AMY, APU), MTO, NAP])
        self.legalOrder(TUR, [(TUR, AMY, ROM), SUP, (TUR, AMY, APU), MTO, NAP])
        self.legalOrder(TUR, [(TUR, FLT, AEG), SUP, (TUR, FLT, GRE), MTO, ION])
        self.legalOrder(ITA, [(ITA, FLT, ION), CVY, (TUR, AMY, APU), CTO, NAP])
        self.legalOrder(ITA, [(ITA, AMY, NAP), MTO, APU])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.legalOrder(GER, [(GER, FLT, SKA), CVY, (ENG, AMY, NWY), CTO, SWE])
        self.legalOrder(AUS, [(AUS, AMY, TRI), MTO, VEN])
        self.legalOrder(AUS, [(AUS, FLT, ADR), CVY, (AUS, AMY, TRI), CTO, VEN])
        self.legalOrder(ITA, [(ITA, AMY, VEN), MTO, TRI])
        self.legalOrder(TUR, [(TUR, AMY, ANK), MTO, SEV])
        self.legalOrder(TUR, [(TUR, FLT, BLA), CVY, (TUR, AMY, ANK), CTO, SEV])
        self.assertMapState(steady_state + [
            [FRA, AMY, BEL],
            [FRA, FLT, ECH],
            [ENG, FLT, ECH, MRT],
            [TUR, FLT, ION],
            [ITA, FLT, ION, MRT],
            [ENG, AMY, SWE],
            [RUS, AMY, NWY],
            [AUS, AMY, VEN],
            [ITA, AMY, TRI],
            [TUR, AMY, SEV],
        ])
    def test_4A3_refined(self):
        '4.A.3.c  CONVOYING TO ADJACENT PLACE'
        # 6.G.1, 6.G.2, 6.G.3, 6.G.4, and an implicit convoy test
        self.judge.datc.datc_4a3 = 'c'
        steady_state = [
            [FRA, AMY, BUR],
            [FRA, FLT, MAO],
            [TUR, AMY, ROM],
            [TUR, FLT, AEG],
            [GER, FLT, SKA],
            [AUS, FLT, ADR],
            [TUR, FLT, BLA],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, AMY, PIC],
            [FRA, FLT, BRE],
            [ENG, FLT, ECH],
            [TUR, AMY, APU],
            [TUR, FLT, GRE],
            [ITA, FLT, ION],
            [ITA, AMY, NAP],
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
            [AUS, AMY, TRI],
            [ITA, AMY, VEN],
            [TUR, AMY, ANK],
        ])
        self.legalOrder(FRA, [(FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, AMY, BUR), SUP, (FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, MAO), SUP, (FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (FRA, AMY, PIC), CTO, BEL])
        self.legalOrder(TUR, [(TUR, FLT, GRE), MTO, ION])
        self.legalOrder(TUR, [(TUR, AMY, APU), MTO, NAP])
        self.legalOrder(TUR, [(TUR, AMY, ROM), SUP, (TUR, AMY, APU), MTO, NAP])
        self.legalOrder(TUR, [(TUR, FLT, AEG), SUP, (TUR, FLT, GRE), MTO, ION])
        self.legalOrder(ITA, [(ITA, FLT, ION), CVY, (TUR, AMY, APU), CTO, NAP])
        self.legalOrder(ITA, [(ITA, AMY, NAP), MTO, APU])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.legalOrder(GER, [(GER, FLT, SKA), CVY, (ENG, AMY, NWY), CTO, SWE])
        self.legalOrder(AUS, [(AUS, AMY, TRI), MTO, VEN])
        self.legalOrder(AUS, [(AUS, FLT, ADR), CVY, (AUS, AMY, TRI), CTO, VEN])
        self.legalOrder(ITA, [(ITA, AMY, VEN), MTO, TRI])
        self.legalOrder(TUR, [(TUR, AMY, ANK), MTO, SEV])
        self.legalOrder(TUR, [(TUR, FLT, BLA), CVY, (TUR, AMY, ANK), CTO, SEV])
        self.assertMapState(steady_state + [
            [FRA, AMY, BEL],
            [FRA, FLT, ECH],
            [ENG, FLT, ECH, MRT],
            [TUR, AMY, NAP],
            [TUR, FLT, ION],
            [ITA, FLT, ION, MRT],
            [ITA, AMY, NAP, MRT],
            [ENG, AMY, SWE],
            [RUS, AMY, NWY],
            [AUS, AMY, VEN],
            [ITA, AMY, TRI],
            [TUR, AMY, SEV],
        ])
    def test_4A3_1982(self):
        '4.A.3.d  CONVOYING TO ADJACENT PLACE'
        # 6.G.1, 6.G.2, 6.G.3, 6.G.4, and an implicit convoy test
        self.judge.datc.datc_4a3 = 'd'
        steady_state = [
            [FRA, AMY, BUR],
            [FRA, FLT, MAO],
            [TUR, AMY, ROM],
            [TUR, FLT, AEG],
            [GER, FLT, SKA],
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
            [AUS, FLT, ADR],
            [TUR, FLT, BLA],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, AMY, PIC],
            [FRA, FLT, BRE],
            [ENG, FLT, ECH],
            [TUR, AMY, APU],
            [TUR, FLT, GRE],
            [ITA, FLT, ION],
            [ITA, AMY, NAP],
            [AUS, AMY, TRI],
            [ITA, AMY, VEN],
            [TUR, AMY, ANK],
        ])
        self.legalOrder(FRA, [(FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, AMY, BUR), SUP, (FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, MAO), SUP, (FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (FRA, AMY, PIC), CTO, BEL])
        self.legalOrder(TUR, [(TUR, FLT, GRE), MTO, ION])
        self.legalOrder(TUR, [(TUR, AMY, APU), MTO, NAP])
        self.legalOrder(TUR, [(TUR, AMY, ROM), SUP, (TUR, AMY, APU), MTO, NAP])
        self.legalOrder(TUR, [(TUR, FLT, AEG), SUP, (TUR, FLT, GRE), MTO, ION])
        self.legalOrder(ITA, [(ITA, FLT, ION), CVY, (TUR, AMY, APU), CTO, NAP])
        self.legalOrder(ITA, [(ITA, AMY, NAP), MTO, APU])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.legalOrder(GER, [(GER, FLT, SKA), CVY, (ENG, AMY, NWY), CTO, SWE])
        self.legalOrder(AUS, [(AUS, AMY, TRI), MTO, VEN])
        self.legalOrder(AUS, [(AUS, FLT, ADR), CVY, (AUS, AMY, TRI), CTO, VEN])
        self.legalOrder(ITA, [(ITA, AMY, VEN), MTO, TRI])
        self.legalOrder(TUR, [(TUR, AMY, ANK), MTO, SEV])
        self.legalOrder(TUR, [(TUR, FLT, BLA), CVY, (TUR, AMY, ANK), CTO, SEV])
        self.assertMapState(steady_state + [
            [FRA, AMY, BEL],
            [FRA, FLT, ECH],
            [ENG, FLT, ECH, MRT],
            [TUR, AMY, NAP],
            [TUR, FLT, ION],
            [ITA, FLT, ION, MRT],
            [ITA, AMY, NAP, MRT],
            [AUS, AMY, VEN],
            [ITA, AMY, TRI],
            [TUR, AMY, SEV],
        ])
    def test_4A3_DPTG(self):
        '4.A.3.e  CONVOYING TO ADJACENT PLACE'
        # 6.G.1, 6.G.2, 6.G.3, 6.G.4, and an implicit convoy test
        self.judge.datc.datc_4a3 = 'e'
        steady_state = [
            [FRA, AMY, BUR],
            [FRA, FLT, MAO],
            [TUR, AMY, ROM],
            [TUR, FLT, AEG],
            [GER, FLT, SKA],
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
            [AUS, FLT, ADR],
            [AUS, AMY, TRI],
            [ITA, AMY, VEN],
            [TUR, FLT, BLA],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, AMY, PIC],
            [FRA, FLT, BRE],
            [ENG, FLT, ECH],
            [TUR, AMY, APU],
            [TUR, FLT, GRE],
            [ITA, FLT, ION],
            [ITA, AMY, NAP],
            [TUR, AMY, ANK],
        ])
        self.legalOrder(FRA, [(FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, AMY, BUR), SUP, (FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, MAO), SUP, (FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (FRA, AMY, PIC), CTO, BEL])
        self.legalOrder(TUR, [(TUR, FLT, GRE), MTO, ION])
        self.legalOrder(TUR, [(TUR, AMY, APU), MTO, NAP])
        self.legalOrder(TUR, [(TUR, AMY, ROM), SUP, (TUR, AMY, APU), MTO, NAP])
        self.legalOrder(TUR, [(TUR, FLT, AEG), SUP, (TUR, FLT, GRE), MTO, ION])
        self.legalOrder(ITA, [(ITA, FLT, ION), CVY, (TUR, AMY, APU), CTO, NAP])
        self.legalOrder(ITA, [(ITA, AMY, NAP), MTO, APU])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.legalOrder(GER, [(GER, FLT, SKA), CVY, (ENG, AMY, NWY), CTO, SWE])
        self.legalOrder(AUS, [(AUS, AMY, TRI), MTO, VEN])
        self.legalOrder(AUS, [(AUS, FLT, ADR), CVY, (AUS, AMY, TRI), CTO, VEN])
        self.legalOrder(ITA, [(ITA, AMY, VEN), MTO, TRI])
        self.legalOrder(TUR, [(TUR, AMY, ANK), MTO, SEV])
        self.legalOrder(TUR, [(TUR, FLT, BLA), CVY, (TUR, AMY, ANK), CTO, SEV])
        self.assertMapState(steady_state + [
            [FRA, AMY, BEL],
            [FRA, FLT, ECH],
            [ENG, FLT, ECH, MRT],
            [TUR, AMY, NAP],
            [TUR, FLT, ION],
            [ITA, FLT, ION, MRT],
            [ITA, AMY, NAP, MRT],
            [TUR, AMY, SEV],
        ])
    def test_4A3_explicit(self):
        '4.A.3.f  CONVOYING TO ADJACENT PLACE'
        # 6.G.1, 6.G.2, 6.G.3, 6.G.4, and an implicit convoy test
        self.judge.datc.datc_4a3 = 'f'
        steady_state = [
            [FRA, AMY, BUR],
            [FRA, FLT, MAO],
            [TUR, AMY, ROM],
            [TUR, FLT, AEG],
            [GER, FLT, SKA],
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
            [AUS, FLT, ADR],
            [AUS, AMY, TRI],
            [ITA, AMY, VEN],
            [TUR, FLT, BLA],
            [TUR, AMY, ANK],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, AMY, PIC],
            [FRA, FLT, BRE],
            [ENG, FLT, ECH],
            [TUR, AMY, APU],
            [TUR, FLT, GRE],
            [ITA, FLT, ION],
            [ITA, AMY, NAP],
        ])
        self.legalOrder(FRA, [(FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, AMY, BUR), SUP, (FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, MAO), SUP, (FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (FRA, AMY, PIC), CTO, BEL])
        self.legalOrder(TUR, [(TUR, FLT, GRE), MTO, ION])
        self.legalOrder(TUR, [(TUR, AMY, APU), MTO, NAP])
        self.legalOrder(TUR, [(TUR, AMY, ROM), SUP, (TUR, AMY, APU), MTO, NAP])
        self.legalOrder(TUR, [(TUR, FLT, AEG), SUP, (TUR, FLT, GRE), MTO, ION])
        self.legalOrder(ITA, [(ITA, FLT, ION), CVY, (TUR, AMY, APU), CTO, NAP])
        self.legalOrder(ITA, [(ITA, AMY, NAP), MTO, APU])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.legalOrder(GER, [(GER, FLT, SKA), CVY, (ENG, AMY, NWY), CTO, SWE])
        self.legalOrder(AUS, [(AUS, AMY, TRI), MTO, VEN])
        self.legalOrder(AUS, [(AUS, FLT, ADR), CVY, (AUS, AMY, TRI), CTO, VEN])
        self.legalOrder(ITA, [(ITA, AMY, VEN), MTO, TRI])
        self.illegalOrder(TUR, [(TUR, AMY, ANK), MTO, SEV])
        self.legalOrder(TUR, [(TUR, FLT, BLA), CVY, (TUR, AMY, ANK), CTO, SEV])
        self.assertMapState(steady_state + [
            [FRA, AMY, BEL],
            [FRA, FLT, ECH],
            [ENG, FLT, ECH, MRT],
            [TUR, AMY, NAP],
            [TUR, FLT, ION],
            [ITA, FLT, ION, MRT],
            [ITA, AMY, NAP, MRT],
        ])
    def test_4A4_given(self):
        '4.A.4.a  SUPPORT CUT ON ATTACK ON ITSELF VIA CONVOY'
        # Test 6.G.13
        self.judge.datc.datc_4a4 = 'a'
        steady_state = [
            [AUS, FLT, ADR],
            [ITA, FLT, VEN],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [AUS, AMY, TRI],
            [ITA, AMY, ALB],
        ])
        self.legalOrder(AUS, [(AUS, AMY, TRI), CTO, VEN, VIA, [ADR]])
        self.legalOrder(AUS, [(AUS, FLT, ADR), CVY, (AUS, AMY, TRI), CTO, VEN])
        self.legalOrder(ITA, [(ITA, AMY, ALB), MTO, TRI])
        self.legalOrder(ITA, [(ITA, FLT, VEN), SUP, (ITA, AMY, ALB), MTO, TRI])
        self.assertMapState(steady_state + [
            [AUS, AMY, TRI, MRT],
            [ITA, AMY, TRI],
        ])
    @fails
    def test_4A4_cut(self):
        '4.A.4.b  SUPPORT CUT ON ATTACK ON ITSELF VIA CONVOY'
        # Test 6.G.13
        # This situation cannot occur with 4.A.3 choice b or c.
        self.judge.datc.datc_4a3 = 'd'
        self.judge.datc.datc_4a4 = 'b'
        steady_state = [
            [AUS, FLT, ADR],
            [AUS, AMY, TRI],
            [ITA, AMY, ALB],
            [ITA, FLT, VEN],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(AUS, [(AUS, AMY, TRI), CTO, VEN, VIA, [ADR]])
        self.legalOrder(AUS, [(AUS, FLT, ADR), CVY, (AUS, AMY, TRI), CTO, VEN])
        self.legalOrder(ITA, [(ITA, AMY, ALB), MTO, TRI])
        self.legalOrder(ITA, [(ITA, FLT, VEN), SUP, (ITA, AMY, ALB), MTO, TRI])
        self.assertMapState(steady_state + [
        ])
    def test_4A5_blocked(self):
        '4.A.5.a  RETREAT WHEN DISLODGED BY CONVOY'
        # Test 6.H.12
        self.judge.datc.datc_4a5 = 'a'
        steady_state = [
            [ENG, AMY, BUR],
            [ENG, FLT, IRI],
            [ENG, FLT, NTH],
            [FRA, FLT, MAO],
            [RUS, FLT, NWG],
            [RUS, FLT, NAO],
            [RUS, AMY, CLY],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LVP],
            [ENG, FLT, ECH],
            [FRA, FLT, BRE],
            [RUS, AMY, EDI],
        ])
        self.legalOrder(FRA, [(FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(FRA, [(FRA, FLT, MAO), SUP, (FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(ENG, [(ENG, AMY, LVP), CTO, EDI, VIA, [IRI, ECH, NTH]])
        self.legalOrder(ENG, [(ENG, FLT, IRI), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(RUS, [(RUS, AMY, EDI), CTO, LVP, VIA, [NWG, NAO]])
        self.legalOrder(RUS, [(RUS, FLT, NWG), CVY, (RUS, AMY, EDI), CTO, LVP])
        self.legalOrder(RUS, [(RUS, FLT, NAO), CVY, (RUS, AMY, EDI), CTO, LVP])
        self.legalOrder(RUS, [(RUS, AMY, CLY), SUP, (RUS, AMY, EDI), MTO, LVP])
        self.assertMapState(steady_state + [
            [ENG, AMY, LVP, MRT],
            [ENG, FLT, ECH, MRT],
            [FRA, FLT, ECH],
            [RUS, AMY, LVP],
        ])
        self.illegalOrder(ENG, [(ENG, AMY, LVP), RTO, EDI])
        self.assertMapState(steady_state + [
            [FRA, FLT, ECH],
            [RUS, AMY, LVP],
        ])
    @fails
    def test_4A5_retreat(self):
        '4.A.5.b  RETREAT WHEN DISLODGED BY CONVOY'
        # Test 6.H.12
        # This situation cannot occur with 4.A.3 choice c.
        self.judge.datc.datc_4a3 = 'd'
        self.judge.datc.datc_4a5 = 'b'
        steady_state = [
            [ENG, AMY, BUR],
            [ENG, FLT, IRI],
            [ENG, FLT, NTH],
            [FRA, FLT, MAO],
            [RUS, FLT, NWG],
            [RUS, FLT, NAO],
            [RUS, AMY, CLY],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LVP],
            [ENG, FLT, ECH],
            [FRA, FLT, BRE],
            [RUS, AMY, EDI],
        ])
        self.legalOrder(FRA, [(FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(FRA, [(FRA, FLT, MAO), SUP, (FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(ENG, [(ENG, AMY, LVP), CTO, EDI, VIA, [IRI, ECH, NTH]])
        self.legalOrder(ENG, [(ENG, FLT, IRI), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(RUS, [(RUS, AMY, EDI), CTO, LVP, VIA, [NWG, NAO]])
        self.legalOrder(RUS, [(RUS, FLT, NWG), CVY, (RUS, AMY, EDI), CTO, LVP])
        self.legalOrder(RUS, [(RUS, FLT, NAO), CVY, (RUS, AMY, EDI), CTO, LVP])
        self.legalOrder(RUS, [(RUS, AMY, CLY), SUP, (RUS, AMY, EDI), MTO, LVP])
        self.assertMapState(steady_state + [
            [ENG, AMY, LVP, MRT],
            [ENG, FLT, ECH, MRT],
            [FRA, FLT, ECH],
            [RUS, AMY, LVP],
        ])
        self.legalOrder(ENG, [(ENG, AMY, LVP), RTO, EDI])
        self.assertMapState(steady_state + [
            [ENG, AMY, EDI],
            [FRA, FLT, ECH],
            [RUS, AMY, LVP],
        ])
    def test_4A6_ignored(self):
        '4.A.6.a  CONVOY PATH SPECIFICATION'
        self.judge.datc.datc_4a6 = 'a'
        steady_state = [
            [ENG, FLT, NTH],
            [ENG, FLT, NWG],
            [FRA, FLT, BRE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, ECH],
            [ENG, AMY, LON],
            [ENG, AMY, EDI],
            [FRA, FLT, MAO],
        ])
        self.legalOrder(ENG, [(ENG, AMY, EDI), CTO, NWY])
        self.legalOrder(ENG, [(ENG, FLT, NWG), CVY, (ENG, AMY, EDI), CTO, NWY])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL, VIA, [ECH]])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, ECH])
        self.legalOrder(FRA, [(FRA, FLT, BRE), SUP, (FRA, FLT, MAO), MTO, ECH])
        self.assertMapState(steady_state + [
            [ENG, FLT, ECH, MRT],
            [ENG, AMY, BEL],
            [ENG, AMY, NWY],
            [FRA, FLT, ECH],
        ])
    def test_4A6_optional(self):
        '4.A.6.b  CONVOY PATH SPECIFICATION'
        self.judge.datc.datc_4a6 = 'b'
        steady_state = [
            [ENG, FLT, NTH],
            [ENG, FLT, NWG],
            [ENG, AMY, LON],
            [FRA, FLT, BRE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, ECH],
            [ENG, AMY, EDI],
            [FRA, FLT, MAO],
        ])
        self.legalOrder(ENG, [(ENG, AMY, EDI), CTO, NWY])
        self.legalOrder(ENG, [(ENG, FLT, NWG), CVY, (ENG, AMY, EDI), CTO, NWY])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL, VIA, [ECH]])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, ECH])
        self.legalOrder(FRA, [(FRA, FLT, BRE), SUP, (FRA, FLT, MAO), MTO, ECH])
        self.assertMapState(steady_state + [
            [ENG, FLT, ECH, MRT],
            [ENG, AMY, NWY],
            [FRA, FLT, ECH],
        ])
    def test_4A6_required(self):
        '4.A.6.c  CONVOY PATH SPECIFICATION'
        self.judge.datc.datc_4a6 = 'c'
        steady_state = [
            [ENG, FLT, NTH],
            [ENG, FLT, NWG],
            [ENG, AMY, LON],
            [ENG, AMY, EDI],
            [FRA, FLT, BRE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, ECH],
            [FRA, FLT, MAO],
        ])
        self.illegalOrder(ENG, [(ENG, AMY, EDI), CTO, NWY])
        self.legalOrder(ENG, [(ENG, FLT, NWG), CVY, (ENG, AMY, EDI), CTO, NWY])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL, VIA, [ECH]])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, ECH])
        self.legalOrder(FRA, [(FRA, FLT, BRE), SUP, (FRA, FLT, MAO), MTO, ECH])
        self.assertMapState(steady_state + [
            [ENG, FLT, ECH, MRT],
            [FRA, FLT, ECH],
        ])
    @fails
    def test_4A7_never(self):
        '4.A.7.a  AVOIDING A HEAD TO HEAD BATTLE TO BOUNCE A UNIT'
        # Test 6.G.15
        self.judge.datc.datc_4a7 = 'a'
        steady_state = [
            [ENG, FLT, NTH],
            [ENG, AMY, HOL],
            [ENG, AMY, LON],
            [FRA, FLT, ECH],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, YOR],
            [FRA, AMY, BEL],
        ])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, HOL), SUP, (ENG, AMY, LON), MTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, YOR), MTO, LON])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL, VIA, [NTH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BEL), CTO, LON])
        self.legalOrder(FRA, [(FRA, AMY, BEL), CTO, LON, VIA, [ECH]])
        self.assertMapState(steady_state + [
            [ENG, AMY, BEL],
            [FRA, AMY, BEL, MRT],
        ])
    def test_4A7_bounce(self):
        '4.A.7.b  AVOIDING A HEAD TO HEAD BATTLE TO BOUNCE A UNIT'
        # Test 6.G.15
        self.judge.datc.datc_4a7 = 'b'
        steady_state = [
            [ENG, FLT, NTH],
            [ENG, AMY, HOL],
            [ENG, AMY, YOR],
            [FRA, FLT, ECH],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LON],
            [FRA, AMY, BEL],
        ])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, HOL), SUP, (ENG, AMY, LON), MTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, YOR), MTO, LON])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL, VIA, [NTH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BEL), CTO, LON])
        self.legalOrder(FRA, [(FRA, AMY, BEL), CTO, LON, VIA, [ECH]])
        self.assertMapState(steady_state + [
            [ENG, AMY, BEL],
            [FRA, AMY, BEL, MRT],
        ])

class DATC_4_B(DiplomacyAdjudicatorTestCase):
    ''' 4.B.  COASTAL ISSUES
        Note: This suite does not currently test for default coasts.
        Thus, 4.B.1(b), 4.B.2(b), 4.B.4(b), and 4.B.7(b) are unavailable.
    '''#'''
    
    def test_4B1_fail(self):
        '4.B.1.a  OMITTED COAST SPECIFICATION IN MOVE ORDER WHEN TWO COASTS ARE POSSIBLE'
        self.judge.datc.datc_4b1 = 'a'
        steady_state = [
            [FRA, FLT, MAO],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.illegalOrder(FRA, [(FRA, FLT, MAO), MTO, SPA])
        self.assertMapState(steady_state + [
        ])
    def test_4B2_infer(self):
        '4.B.2.a  OMITTED COAST SPECIFICATION IN MOVE ORDER WHEN ONE COAST IS POSSIBLE'
        # The pair of potentially bouncing fleets
        # distinguish this from case b (default coast).
        self.judge.datc.datc_4b2 = 'a'
        steady_state = [
            [FRA, FLT, MAR],
            [ENG, FLT, GAS],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [TUR, FLT, RUM],
        ])
        self.legalOrder(FRA, [(FRA, FLT, MAR), MTO, SPA])
        self.legalOrder(ENG, [(ENG, FLT, GAS), MTO, SPA])
        self.legalOrder(TUR, [(TUR, FLT, RUM), MTO, BUL])
        self.assertMapState(steady_state + [
            [TUR, FLT, [BUL, ECS]],
        ])
    def test_4B2_fail(self):
        '4.B.2.c  OMITTED COAST SPECIFICATION IN MOVE ORDER WHEN ONE COAST IS POSSIBLE'
        # The pair of potentially bouncing fleets
        # distinguish this from case b (default coast).
        self.judge.datc.datc_4b2 = 'c'
        steady_state = [
            [FRA, FLT, MAR],
            [ENG, FLT, GAS],
            [TUR, FLT, RUM],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.illegalOrder(FRA, [(FRA, FLT, MAR), MTO, SPA])
        self.illegalOrder(ENG, [(ENG, FLT, GAS), MTO, SPA])
        self.illegalOrder(TUR, [(TUR, FLT, RUM), MTO, BUL])
        self.assertMapState(steady_state + [
        ])
    def test_4B3_infer(self):
        '4.B.3.a  MOVE ORDER TO IMPOSSIBLE COAST'
        self.judge.datc.datc_4b3 = 'a'
        steady_state = [
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, FLT, MAR],
        ])
        self.legalOrder(FRA, [(FRA, FLT, MAR), MTO, (SPA, NCS)])
        self.assertMapState(steady_state + [
            [FRA, FLT, [SPA, SCS]],
        ])
    def test_4B3_fail(self):
        '4.B.3.b  MOVE ORDER TO IMPOSSIBLE COAST'
        self.judge.datc.datc_4b3 = 'b'
        steady_state = [
            [FRA, FLT, MAR],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.illegalOrder(FRA, [(FRA, FLT, MAR), MTO, (SPA, NCS)])
        self.assertMapState(steady_state + [
        ])
    def test_4B4_required(self):
        '4.B.4.a  COAST SPECIFICATION IN SUPPORT ORDER'
        # If either Portugal or Mid-Atlantic Ocean move,
        # you have the unsupported option 'b' (default coast).
        self.judge.datc.datc_4b4 = 'a'
        steady_state = [
            [RUS, FLT, GOB],
            [RUS, FLT, FIN],
            [ENG, FLT, NWY],
            [FRA, FLT, POR],
            [FRA, FLT, GAS],
            [ITA, FLT, MAO],
            [ITA, FLT, MAR],
            [ITA, FLT, CON],
            [AUS, AMY, SER],
            [TUR, FLT, BLA],
            [TUR, FLT, RUM],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, BAR],
        ])
        self.legalOrder(RUS, [(RUS, FLT, GOB), MTO, (STP, SCS)])
        self.illegalOrder(RUS, [(RUS, FLT, FIN), SUP, (RUS, FLT, GOB), MTO, STP])
        self.legalOrder(ENG, [(ENG, FLT, BAR), MTO, (STP, NCS)])
        self.legalOrder(ENG, [(ENG, FLT, NWY), SUP, (ENG, FLT, BAR), MTO, (STP, NCS)])
        self.legalOrder(FRA, [(FRA, FLT, POR), MTO, (SPA, SCS)])
        self.illegalOrder(FRA, [(FRA, FLT, GAS), SUP, (FRA, FLT, POR), MTO, SPA])
        self.legalOrder(ITA, [(ITA, FLT, MAO), MTO, (SPA, NCS)])
        self.illegalOrder(ITA, [(ITA, FLT, MAR), SUP, (ITA, FLT, MAO), MTO, SPA])
        self.legalOrder(ITA, [(ITA, FLT, CON), MTO, (BUL, SCS)])
        self.illegalOrder(AUS, [(AUS, AMY, SER), SUP, (ITA, FLT, CON), MTO, BUL])
        self.legalOrder(TUR, [(TUR, FLT, BLA), MTO, (BUL, ECS)])
        self.illegalOrder(TUR, [(TUR, FLT, RUM), SUP, (TUR, FLT, BLA), MTO, BUL])
        self.assertMapState(steady_state + [
            [ENG, FLT, [STP, NCS]],
        ])
    def test_4B4_infer(self):
        '4.B.4.c  COAST SPECIFICATION IN SUPPORT ORDER'
        # If either Portugal or Mid-Atlantic Ocean move,
        # you have the unsupported option 'b' (default coast).
        self.judge.datc.datc_4b4 = 'c'
        steady_state = [
            [RUS, FLT, GOB],
            [RUS, FLT, FIN],
            [ENG, FLT, BAR],
            [ENG, FLT, NWY],
            [FRA, FLT, POR],
            [FRA, FLT, GAS],
            [ITA, FLT, MAO],
            [ITA, FLT, MAR],
            [ITA, FLT, CON],
            [AUS, AMY, SER],
            [TUR, FLT, RUM],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [TUR, FLT, BLA],
        ])
        self.legalOrder(RUS, [(RUS, FLT, GOB), MTO, (STP, SCS)])
        self.legalOrder(RUS, [(RUS, FLT, FIN), SUP, (RUS, FLT, GOB), MTO, STP])
        self.legalOrder(ENG, [(ENG, FLT, BAR), MTO, (STP, NCS)])
        self.legalOrder(ENG, [(ENG, FLT, NWY), SUP, (ENG, FLT, BAR), MTO, (STP, NCS)])
        self.legalOrder(FRA, [(FRA, FLT, POR), MTO, (SPA, SCS)])
        self.illegalOrder(FRA, [(FRA, FLT, GAS), SUP, (FRA, FLT, POR), MTO, SPA])
        self.legalOrder(ITA, [(ITA, FLT, MAO), MTO, (SPA, NCS)])
        self.illegalOrder(ITA, [(ITA, FLT, MAR), SUP, (ITA, FLT, MAO), MTO, SPA])
        self.legalOrder(ITA, [(ITA, FLT, CON), MTO, (BUL, SCS)])
        self.illegalOrder(AUS, [(AUS, AMY, SER), SUP, (ITA, FLT, CON), MTO, BUL])
        self.legalOrder(TUR, [(TUR, FLT, BLA), MTO, (BUL, ECS)])
        self.legalOrder(TUR, [(TUR, FLT, RUM), SUP, (TUR, FLT, BLA), MTO, BUL])
        self.assertMapState(steady_state + [
            [TUR, FLT, [BUL, ECS]],
        ])
    def test_4B4_optional(self):
        '4.B.4.d  COAST SPECIFICATION IN SUPPORT ORDER'
        # If either Portugal or Mid-Atlantic Ocean move,
        # you have the unsupported option 'b' (default coast).
        self.judge.datc.datc_4b4 = 'd'
        steady_state = [
            [RUS, FLT, GOB],
            [RUS, FLT, FIN],
            [ENG, FLT, BAR],
            [ENG, FLT, NWY],
            [FRA, FLT, POR],
            [FRA, FLT, GAS],
            [ITA, FLT, MAO],
            [ITA, FLT, MAR],
            [ITA, FLT, CON],
            [AUS, AMY, SER],
            [TUR, FLT, BLA],
            [TUR, FLT, RUM],
        ]
        self.init_state(SPR, 1901, steady_state)
        self.legalOrder(RUS, [(RUS, FLT, GOB), MTO, (STP, SCS)])
        self.legalOrder(RUS, [(RUS, FLT, FIN), SUP, (RUS, FLT, GOB), MTO, STP])
        self.legalOrder(ENG, [(ENG, FLT, BAR), MTO, (STP, NCS)])
        self.legalOrder(ENG, [(ENG, FLT, NWY), SUP, (ENG, FLT, BAR), MTO, (STP, NCS)])
        self.legalOrder(FRA, [(FRA, FLT, POR), MTO, (SPA, SCS)])
        self.legalOrder(FRA, [(FRA, FLT, GAS), SUP, (FRA, FLT, POR), MTO, SPA])
        self.legalOrder(ITA, [(ITA, FLT, MAO), MTO, (SPA, NCS)])
        self.legalOrder(ITA, [(ITA, FLT, MAR), SUP, (ITA, FLT, MAO), MTO, SPA])
        self.legalOrder(ITA, [(ITA, FLT, CON), MTO, (BUL, SCS)])
        self.legalOrder(AUS, [(AUS, AMY, SER), SUP, (ITA, FLT, CON), MTO, BUL])
        self.legalOrder(TUR, [(TUR, FLT, BLA), MTO, (BUL, ECS)])
        self.legalOrder(TUR, [(TUR, FLT, RUM), SUP, (TUR, FLT, BLA), MTO, BUL])
        self.assertMapState(steady_state)
    def test_4B4_impossible(self):
        '4.B.4.e  COAST SPECIFICATION IN SUPPORT ORDER'
        # If either Portugal or Mid-Atlantic Ocean move,
        # you have the unsupported option 'b' (default coast).
        self.judge.datc.datc_4b4 = 'e'
        steady_state = [
            [RUS, FLT, FIN],
            [ENG, FLT, BAR],
            [ENG, FLT, NWY],
            [FRA, FLT, POR],
            [FRA, FLT, GAS],
            [ITA, FLT, MAO],
            [ITA, FLT, MAR],
            [ITA, FLT, CON],
            [AUS, AMY, SER],
            [TUR, FLT, BLA],
            [TUR, FLT, RUM],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [RUS, FLT, GOB],
        ])
        self.legalOrder(RUS, [(RUS, FLT, GOB), MTO, (STP, SCS)])
        self.legalOrder(RUS, [(RUS, FLT, FIN), SUP, (RUS, FLT, GOB), MTO, STP])
        self.legalOrder(ENG, [(ENG, FLT, BAR), MTO, (STP, NCS)])
        self.illegalOrder(ENG, [(ENG, FLT, NWY), SUP, (ENG, FLT, BAR), MTO, (STP, NCS)])
        self.legalOrder(FRA, [(FRA, FLT, POR), MTO, (SPA, SCS)])
        self.legalOrder(FRA, [(FRA, FLT, GAS), SUP, (FRA, FLT, POR), MTO, SPA])
        self.legalOrder(ITA, [(ITA, FLT, MAO), MTO, (SPA, NCS)])
        self.legalOrder(ITA, [(ITA, FLT, MAR), SUP, (ITA, FLT, MAO), MTO, SPA])
        self.legalOrder(ITA, [(ITA, FLT, CON), MTO, (BUL, SCS)])
        self.legalOrder(AUS, [(AUS, AMY, SER), SUP, (ITA, FLT, CON), MTO, BUL])
        self.legalOrder(TUR, [(TUR, FLT, BLA), MTO, (BUL, ECS)])
        self.legalOrder(TUR, [(TUR, FLT, RUM), SUP, (TUR, FLT, BLA), MTO, BUL])
        self.assertMapState(steady_state + [
            [RUS, FLT, [STP, SCS]],
        ])
    def test_4B5_fail(self):
        '4.B.5.a  WRONG COAST OF ORDERED UNIT'
        # Test 6.B.10
        self.judge.datc.datc_4b5 = 'a'
        start_state = [
            [FRA, FLT, [SPA, SCS]],
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(FRA, [(FRA, FLT, [SPA, NCS]), MTO, GOL])
        self.assertMapState(start_state)
    @fails
    def test_4B5_ignore(self):
        '4.B.5.b  WRONG COAST OF ORDERED UNIT'
        # Test 6.B.10
        self.judge.datc.datc_4b5 = 'b'
        start_state = [
            [FRA, FLT, [SPA, SCS]],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(FRA, [(FRA, FLT, [SPA, NCS]), MTO, GOL])
        self.assertMapState([
            [FRA, FLT, GOL],
        ])
    def test_4B6_fail(self):
        '4.B.6.a  UNKNOWN COASTS OR IRRELEVANT COASTS'
        # Test 6.B.12
        self.judge.datc.datc_4b6 = 'a'
        start_state = [
            [FRA, AMY, GAS]
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(FRA, [(FRA, AMY, GAS), MTO, (SPA, NCS)])
        self.assertMapState(start_state)
    def test_4B6_ignore(self):
        '4.B.6.b  UNKNOWN COASTS OR IRRELEVANT COASTS'
        # Test 6.B.12
        self.judge.datc.datc_4b6 = 'b'
        start_state = [
            [FRA, AMY, GAS]
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(FRA, [(FRA, AMY, GAS), MTO, (SPA, NCS)])
        self.assertMapState([
            [FRA, AMY, SPA],
        ])
    def test_4B7_fail(self):
        '4.B.7.a  COAST SPECIFICATION IN BUILD ORDER'
        # Test 6.B.14
        self.judge.datc.datc_4b7 = 'a'
        start_state = []
        self.init_state(WIN, 1901, start_state)
        self.illegalOrder(RUS, [(RUS, FLT, STP), BLD])
        self.assertMapState(start_state)

class DATC_4_C(DiplomacyAdjudicatorTestCase):
    ''' 4.C.  UNIT DESIGNATION AND NATIONALITY ISSUES
        Note: This program does not support validity based on other orders.
        Thus, 4.C.1(c), 4.C.2(c), 4.B.5(c), and 4.B.6(c) are unavailable.
    '''#'''
    
    @fails
    def test_4C1_invalid(self):
        '4.C.1.a  MISSING UNIT DESIGNATION'
        self.judge.datc.datc_4c1 = 'a'
        steady_state = [
            [GER, FLT, BEL],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.illegalOrder(GER, [BEL, MTO, HOL])
        self.assertMapState(steady_state + [
        ])
    def test_4C1_valid(self):
        '4.C.1.b  MISSING UNIT DESIGNATION'
        self.judge.datc.datc_4c1 = 'b'
        steady_state = [
        ]
        self.init_state(SPR, 1901, steady_state + [
            [GER, FLT, BEL],
        ])
        self.legalOrder(GER, [BEL, MTO, HOL])
        self.assertMapState(steady_state + [
            [GER, FLT, HOL],
        ])
    def test_4C2_invalid(self):
        '4.C.2.a  WRONG UNIT DESIGNATION'
        self.judge.datc.datc_4c2 = 'a'
        steady_state = [
            [GER, FLT, BEL],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.illegalOrder(GER, [(GER, AMY, BEL), MTO, HOL])
        self.assertMapState(steady_state + [
        ])
    @fails
    def test_4C2_valid(self):
        '4.C.2.b  WRONG UNIT DESIGNATION'
        self.judge.datc.datc_4c2 = 'b'
        steady_state = [
        ]
        self.init_state(SPR, 1901, steady_state + [
            [GER, FLT, BEL],
        ])
        self.legalOrder(GER, [(GER, AMY, BEL), MTO, HOL])
        self.assertMapState(steady_state + [
            [GER, FLT, HOL],
        ])
    @fails
    def test_4C3_fail(self):
        '4.C.3.a  MISSING UNIT DESIGNATION IN BUILD ORDER'
        self.judge.datc.datc_4c3 = 'a'
        start_state = []
        self.init_state(WIN, 1901, start_state)
        self.illegalOrder(RUS, [SEV, BLD])
        self.illegalOrder(RUS, [MOS, BLD])
        self.illegalOrder(RUS, [(STP, NTH), BLD])
        self.assertMapState(start_state)
    def test_4C3_inland(self):
        '4.C.3.b  MISSING UNIT DESIGNATION IN BUILD ORDER'
        self.judge.datc.datc_4c3 = 'b'
        start_state = []
        self.init_state(WIN, 1901, start_state)
        self.illegalOrder(RUS, [SEV, BLD])
        self.legalOrder(RUS, [MOS, BLD])
        self.illegalOrder(RUS, [(STP, NTH), BLD])
        self.assertMapState(start_state + [
            [RUS, AMY, MOS],
        ])
    @fails
    def test_4C3_coastal(self):
        '4.C.3.c  MISSING UNIT DESIGNATION IN BUILD ORDER'
        self.judge.datc.datc_4c3 = 'c'
        start_state = []
        self.init_state(WIN, 1901, start_state)
        self.illegalOrder(RUS, [SEV, BLD])
        self.legalOrder(RUS, [MOS, BLD])
        self.legalOrder(RUS, [(STP, NTH), BLD])
        self.assertMapState(start_state + [
            [RUS, AMY, MOS],
            [RUS, FLT, [STP, NTH]],
        ])
    def test_4C4_fail(self):
        '4.C.4.a  BUILDING A FLEET IN A LAND AREA'
        self.judge.datc.datc_4c4 = 'a'
        start_state = []
        self.init_state(WIN, 1901, start_state)
        self.illegalOrder(RUS, [(RUS, FLT, MOS), BLD])
        self.assertMapState(start_state)
    @fails
    def test_4C4_army(self):
        '4.C.4.b  BUILDING A FLEET IN A LAND AREA'
        self.judge.datc.datc_4c4 = 'b'
        start_state = []
        self.init_state(WIN, 1901, start_state)
        self.legalOrder(RUS, [(RUS, FLT, MOS), BLD])
        self.assertMapState(start_state + [
            [RUS, AMY, MOS],
        ])
    @fails
    def test_4C5_invalid(self):
        '4.C.5.a  MISSING NATIONALITY IN SUPPORT ORDER'
        self.judge.datc.datc_4c5 = 'a'
        steady_state = [
            [GER, AMY, HOL],
            [ENG, AMY, BEL],
            [FRA, AMY, BUR],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, AMY, BEL), HLD])
        self.legalOrder(FRA, [(FRA, AMY, BUR), MTO, BEL])
        self.illegalOrder(GER, [(GER, AMY, HOL), SUP, BUR, MTO, BEL])
        self.assertMapState(steady_state + [
        ])
    def test_4C5_valid(self):
        '4.C.5.b  MISSING NATIONALITY IN SUPPORT ORDER'
        self.judge.datc.datc_4c5 = 'b'
        steady_state = [
            [GER, AMY, HOL],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, BEL],
            [FRA, AMY, BUR],
        ])
        self.legalOrder(ENG, [(ENG, AMY, BEL), HLD])
        self.legalOrder(FRA, [(FRA, AMY, BUR), MTO, BEL])
        self.legalOrder(GER, [(GER, AMY, HOL), SUP, BUR, MTO, BEL])
        self.assertMapState(steady_state + [
            [ENG, AMY, BEL, MRT],
            [FRA, AMY, BEL],
        ])
    def test_4C6_invalid(self):
        '4.C.6.a  WRONG NATIONALITY IN SUPPORT ORDER'
        self.judge.datc.datc_4c6 = 'a'
        steady_state = [
            [GER, AMY, HOL],
            [ENG, AMY, BEL],
            [FRA, AMY, BUR],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, AMY, BEL), HLD])
        self.legalOrder(FRA, [(FRA, AMY, BUR), MTO, BEL])
        self.illegalOrder(GER, [(GER, AMY, HOL), SUP, (GER, AMY, BUR), MTO, BEL])
        self.assertMapState(steady_state + [
        ])
    @fails
    def test_4C6_valid(self):
        '4.C.6.b  WRONG NATIONALITY IN SUPPORT ORDER'
        self.judge.datc.datc_4c6 = 'b'
        steady_state = [
            [GER, AMY, HOL],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, BEL],
            [FRA, AMY, BUR],
        ])
        self.legalOrder(ENG, [(ENG, AMY, BEL), HLD])
        self.legalOrder(FRA, [(FRA, AMY, BUR), MTO, BEL])
        self.legalOrder(GER, [(GER, AMY, HOL), SUP, (GER, AMY, BUR), MTO, BEL])
        self.assertMapState(steady_state + [
            [ENG, AMY, BEL, MRT],
            [FRA, AMY, BEL],
        ])

class DATC_4_D(DiplomacyAdjudicatorTestCase):
    ''' 4.D.  TOO MANY AND TOO FEW ORDERS'''
    
    def _test_4D1_(self):
        '4.D.1.  MULTIPLE ORDER SETS WITH DEFINED ORDER'
        self.judge.datc.datc_4d1 = 'b'
    def _test_4D2_(self):
        '4.D.2.  MULTIPLE ORDER SETS WITH UNDEFINED ORDER'
        self.judge.datc.datc_4d2 = 'b'
    def _test_4D3_(self):
        '4.D.3.  MULTIPLE ORDERS TO THE SAME UNIT'
        self.judge.datc.datc_4d3 = 'b'
    def _test_4D4_(self):
        '4.D.4.  TOO MANY BUILD ORDERS'
        self.judge.datc.datc_4d4 = 'b'
    def _test_4D5_(self):
        '4.D.5.  MULTIPLE BUILD ORDERS FOR ONE AREA'
        self.judge.datc.datc_4d5 = 'c'
    def _test_4D6_(self):
        '4.D.6.  TOO MANY DISBAND ORDERS'
        self.judge.datc.datc_4d6 = 'b'
    def _test_4D7_(self):
        '4.D.7.  WAIVING BUILDS'
        self.judge.datc.datc_4d7 = 'ab'
    def _test_4D8_(self):
        '4.D.8.  REMOVING A UNIT IN CIVIL DISORDER'
        self.judge.datc.datc_4d8 = 'abcde'
    def _test_4D9_(self):
        '4.D.9.  RECEIVING HOLD SUPPORT IN CIVIL DISORDER'
        self.judge.datc.datc_4d9 = 'ab'

class DATC_4_E(DiplomacyAdjudicatorTestCase):
    ''' 4.E.  MISCELLANEOUS ISSUES'''
    
    def _test_4E1_(self):
        '4.E.1.  ILLEGAL ORDERS'
        self.judge.datc.datc_4e1 = 'abcd'
    def _test_4E2_(self):
        '4.E.2.  POORLY WRITTEN ORDERS'
        self.judge.datc.datc_4e2 = 'e'
    def _test_4E3_(self):
        '4.E.3.  IMPLICIT ORDERS'
        self.judge.datc.datc_4e3 = 'ab'
    def _test_4E4_(self):
        '4.E.4.  PERPETUAL ORDERS'
        self.judge.datc.datc_4e4 = 'ab'
    def _test_4E5_(self):
        '4.E.5.  PROXY ORDERS'
        self.judge.datc.datc_4e5 = 'abc'
    def _test_4E6_(self):
        '4.E.6.  FLYING DUTCHMAN'
        self.judge.datc.datc_4e6 = 'a'


if __name__ == '__main__': unittest.main()
