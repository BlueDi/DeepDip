r'''DATC rule variant test cases for Parlance
    Copyright (C) 2001-2008  Lucas B. Kruijswijk and Eric Wald
    
    This module contains placeholders for tests to be implemented when rule
    variants rise a bit higher in the priority queue.  Some of these variants
    may require message syntax modification and/or a new judge class.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

import unittest

from parlance.test.datc import DiplomacyAdjudicatorTestCase

# 7.  COLONIAL VARIANT
class DATC_7_A(DiplomacyAdjudicatorTestCase):
    ''' 7.A.  HONG KONG OPTIONAL RULE''' 
    variant_name = 'colonial'
    
    def _test_7A1(self):
        ''' 7.A.1  HONG KONG IS NOT A SUPPLY CENTER FOR CHINA''' 
    def _test_7A2(self):
        ''' 7.A.2.  HONG KONG IS A SUPPLY CENTER FOR OTHER COUNTRIES''' 
    def _test_7A3(self):
        ''' 7.A.3.  HONG KONG DOES NOT COUNT FOR VICTORY FOR CHINA''' 

class DATC_7_B(DiplomacyAdjudicatorTestCase):
    ''' 7.B.  TRANS SIBERIAN RAILROAD OPTIONAL RULE''' 
    variant_name = 'colonial'
    
    def _test_7B1(self):
        ''' 7.B.1.  TSR BOUNCING ON ARMY OF OTHER COUNTRY''' 
    def _test_7B2(self):
        ''' 7.B.2.  TSR CAN NOT PASS A SUPPORTED ARMY''' 
    def _test_7B3(self):
        ''' 7.B.3.  TSR CAN MOVE THROUGH RUSSIAN ARMY''' 
    def _test_7B4(self):
        ''' 7.B.4,  TSR BOUNCES ON RUSSIAN ARMY''' 
    def _test_7B5(self):
        ''' 7.B.5.  BOUNCING WHILE PASSING THROUGH A RUSSIAN ARMY''' 
    def _test_7B6(self):
        ''' 7.B.6.  TSR CAN PASS WHEN TWO ARMIES BOUNCE''' 
    def _test_7B7(self):
        ''' 7.B.7.  TSR CAN PASS WHEN TWO ARMIES WITH EQUAL SUPPORT BOUNCE''' 
    def _test_7B8(self):
        ''' 7.B.8.  TSR BOUNCES WHEN OTHER FORCES ARE UNBALANCED''' 
    def _test_7B9(self):
        ''' 7.B.9.  TSR CAN PASS TRHOUGH AS LONG AS RUSSIAN ARMY HOLDS''' 
    def _test_7B10(self):
        ''' 7.B.10.  TSR CAN PASS EVEN WHEN RUSSIAN ARMY IS MOVING AWAY''' 
    def _test_7B11(self):
        ''' 7.B.11.  TSR CAN ONLY BOUNCE ONCE''' 
    def _test_7B12(self):
        ''' 7.B.12.  COMPLEX BOUNCE WITH TSR''' 
    def _test_7B13(self):
        ''' 7.B.13.  A MOVE WITH THE TSR CAN NOT DISLODGE UNIT''' 
    def _test_7B14(self):
        ''' 7.B.14.  A MOVE WITH THE TSR CAN NOT CUT SUPPORT''' 
    def _test_7B15(self):
        ''' 7.B.15.  A MOVE WITH THE TSR CAN RECEIVE A SUPPORT TO WIN A BATTLE''' 
    def _test_7B16(self):
        ''' 7.B.16.  A MOVE WITH THE TSR CAN PREVENT DISLODGEMENT''' 
    def _test_7B17(self):
        ''' 7.B.17.  CIRCULAR MOVEMENT WITH THE TSR IS POSSIBLE''' 
    def _test_7B18(self):
        ''' 7.B.18.  TSR CAN NOT PASS AN UNOWNED SUPPLY CENTER''' 
    def _test_7B19(self):
        ''' 7.B.19.  TSR MAY LEAVE AN UNOWNED SUPPLY CENTER''' 
    def _test_7B20(self):
        ''' 7.B.20.  TSR CAN PASS AN UNOWNED SUPPLY CENTER WHEN ANOTHER ARMY IS HOLDING''' 
    def _test_7B21(self):
        ''' 7.B.21.  TSR CAN NOT PASS AN UNOWNED SUPPLY CENTER WHEN ARMY IS MOVING AWAY''' 
    def _test_7B22(self):
        ''' 7.B.22.  TSR CAN PASS AN UNOWNED SUPPLY CENTER WHEN ARMY MOVING AWAY BOUNCES''' 
    def _test_7B23(self):
        ''' 7.B.23.  SIMPLE TWO ARMY TSR PARADOX''' 
    def _test_7B24(self):
        ''' 7.B.24.  COMPLEX TSR PARADOX''' 
    def _test_7B25(self):
        ''' 7.B.25.  TSR SUPPLY CENTER PARADOX''' 
    def _test_7B26(self):
        ''' 7.B.26.  BALANCED HEAD TO HEAD BATTLE WITH TSR''' 
    def _test_7B27(self):
        ''' 7.B.27.  UNBALANCED HEAD TO HEAD BATTLE WITH TSR''' 
    def _test_7B28(self):
        ''' 7.B.28.  SUPPORTED HEAD TO HEAD BATTLE WITH TSR''' 
    def _test_7B29(self):
        ''' 7.B.29.  TSR CAN'T DISLODGE IN HEAD TO HEAD BATTLE''' 
    def _test_7B30(self):
        ''' 7.B.30.  DEPARTURE PLACE DISLODGE WITH SUPPORT FROM ARMY ON TSR''' 
    def _test_7B31(self):
        ''' 7.B.31.  TSR PARADOX WITH DEPARTING TRAIN''' 
    def _test_7B32(self):
        ''' 7.B.32.  NO RETREAT WITH TSR''' 
    def _test_7B33(self):
        ''' 7.B.33.  ONLY ONE UNIT CAN USE THE TSR''' 
    def _test_7B34(self):
        ''' 7.B.34.  ONLY RUSSIA MAY USE THE TSR''' 

class DATC_7_C(DiplomacyAdjudicatorTestCase):
    ''' 7.C.  SUEZ CANAL OPTIONAL RULE''' 
    variant_name = 'colonial'
    
    def _test_7C1(self):
        ''' 7.C.1.  FLEET CAN NOT TAKE SUEZ CANAL IF NOT PERMITTED''' 
    def _test_7C2(self):
        ''' 7.C.2.  FLEET CAN TAKE SUEZ CANAL IF PERMITTED''' 
        # 4.A.2
    def _test_7C3(self):
        ''' 7.C.3.  IMPLICIT PERMISSION FOR OWN UNIT''' 
    def _test_7C4(self):
        ''' 7.C.4.  EXPLICIT PERMISSION DENIES IMPLICIT PERMISSION''' 
    def _test_7C5(self):
        ''' 7.C.5.  ONLY ONE IMPLICIT PERMISSION''' 
    def _test_7C6(self):
        ''' 7.C.6.  NO HEAD TO HEAD BATTLE THROUGH CANAL''' 
    def _test_7C7(self):
        ''' 7.C.7.  CIRCULAR MOVEMENT THROUGH THE CANAL''' 
    def _test_7C8(self):
        ''' 7.C.8.  SUEZ CANAL MOVE OUT PARADOX''' 
    def _test_7C9(self):
        ''' 7.C.9.  SCHWARZ'S FIRST SUEZ CANAL PARADOX''' 
    def _test_7C10(self):
        ''' 7.C.10.  SCHWARZ'S SECOND SUEZ CANAL PARADOX''' 
    def _test_7C11(self):
        ''' 7.C.11.  SCHWARZ'S THIRD SUEZ CANAL PARADOX''' 
        # 4.A.2
    def _test_7C12(self):
        ''' 7.C.12.  SCHWARZ'S PARADOX ADAPTED TO TWO RESOLUTIONS''' 
    def _test_7C13(self):
        ''' 7.C.13.  SUEZ CANAL DISRUPTED CONVOY PARADOX WITH TWO RESOLUTIONS''' 
        # 4.A.2
    def _test_7C14(self):
        ''' 7.C.14.  SUEZ CANAL DISRUPTED CONVOY PARADOX WITH NO RESOLUTION''' 
        # 4.A.2

class DATC_7_D(DiplomacyAdjudicatorTestCase):
    ''' 7.D.  TRANS-SIBERIAN RAILROAD AND SUEZ CANAL COMBINED ISSUES''' 
    variant_name = 'colonial'
    
    def _test_7D1(self):
        ''' 7.D.1.  CIRCULAR MOVEMENT WITH TSR, CONVOY AND SUEZ CANAL''' 
    def _test_7D2(self):
        ''' 7.D.2.  KRUIJSWIJK'S PARADOX''' 

# Other rule variants
class DATC_8(DiplomacyAdjudicatorTestCase):
    ''' 8.  ICE VARIANT''' 
    variant_name = 'loeb9'
    
    def _test_8A(self):
        ''' 8.A.  MOVE TO AN ICE SECTOR''' 
    def _test_8B(self):
        ''' 8.B.  MOVE FROM AN ICE SECTOR''' 
    def _test_8C(self):
        ''' 8.C.  SUPPORT FROM AN ICE SECTOR''' 
    def _test_8D(self):
        ''' 8.D.  NO RETREAT TO AN ICE SECTOR''' 
    def _test_8E(self):
        ''' 8.E.  NO CONVOY IN ICE SECTOR''' 

class DATC_9(DiplomacyAdjudicatorTestCase):
    ''' 9.  CONVOYING COASTAL AREA VARIANT''' 
    variant_name = 'loeb9'
    
    def _test_9A(self):
        ''' 9.A.  DISLODGING OWN CONVOY''' 
    def _test_9B(self):
        ''' 9.B.  CONVOYING TO OWN AREA WITH A LOOP''' 
    def _test_9C(self):
        ''' 9.C.  CONVOY DISRUPTED BY ARMY''' 
    def _test_9D(self):
        ''' 9.D.  CONVOY DISRUPTED BY CONVOYING ARMY''' 
    def _test_9E(self):
        ''' 9.E.  TWO DISRUPTED CONVOYS PARADOX''' 
        # 4.A.2
    def _test_9F(self):
        ''' 9.F.  DISRUPTED CONVOY SUPPORT PARADOX WITH NO RESOLUTION''' 
        # 4.A.2
    def _test_9G(self):
        ''' 9.G.  DISRUPTED CONVOY SUPPORT PARADOX WITH TWO RESOLUTIONS''' 
        # 4.A.2

class DATC_10(DiplomacyAdjudicatorTestCase):
    ''' 10.  DIFFICULT PASSABLE BORDER VARIANT''' 
    variant_name = 'loeb9'
    
    def _test_10A(self):
        ''' 10.A.  SUPPORT CAN NOT BE CUT OVER DIFFICULT PASSABLE BORDER''' 
    def _test_10B(self):
        ''' 10.B.  MOVE OVER DIFFICULT PASSABLE BORDER WITH SUPPORTS CUT SUPPORTS''' 
    def _test_10C(self):
        ''' 10.C.  MOVE OVER DIFFICULT PASSABLE BORDER CAN NOT BOUNCE WITH NORMAL MOVE''' 
    def _test_10D(self):
        ''' 10.D.  TWO MOVES OVER DIFFICULT PASSABLE BORDER CAN BOUNCE''' 
    def _test_10E(self):
        ''' 10.E.  SUPPORT CAN NOT BE GIVEN OVER DIFFICULT PASSABLE BORDER''' 
    def _test_10F(self):
        ''' 10.F.  SUPPORT PARADOX''' 
    def _test_10G(self):
        ''' 10.G.  ALMOST PARADOX''' 
    def _test_10H(self):
        ''' 10.H.  CIRCULAR MOVEMENT WITH DIFFICULT PASSABLE BORDER''' 
    def _test_10I(self):
        ''' 10.I.  CIRCULAR MOVEMENT WITH BOUNCE''' 
    def _test_10J(self):
        ''' 10.J.  CIRCULAR MOVEMENT CAN NOT BE DISRUPTED BY ARMY USING DIFFICULT PASSABLE BORDER''' 
    def _test_10K(self):
        ''' 10.K.  DIFFICULT PASSABLE BORDER DURING RETREAT''' 
    def _test_10L(self):
        ''' 10.L.  DIFFICULT PASSABLE BORDER IS PROPERTY OF BORDER NOT OF SECTOR''' 
    def _test_10M(self):
        ''' 10.M.  USING CONVOY INSTEAD OF DIFFICULT PASSABLE BORDER''' 
    def _test_10N(self):
        ''' 10.N.  USING CONVOY INSTEAD OF DIFFICULT PASSABLE BORDER CUTS SUPPORT''' 
    def _test_10O(self):
        ''' 10.O.  SUPPORT ON ATTACK ON OWN ARMY OVER DIFFICULT PASSABLE BORDER DOES NOT CUT SUPPORT''' 

class DATC_11(DiplomacyAdjudicatorTestCase):
    ''' 11.  BUILD IN ANY SUPPLY CENTER VARIANT''' 
    variant_name = 'chaos'
    
    def _test_11A(self):
        ''' 11.A.  CIVIL DISORDER''' 

class DATC_12(DiplomacyAdjudicatorTestCase):
    ''' 12.  1898 VARIANT''' 
    variant_name = '1898'
    
    def _test_12A(self):
        ''' 12.A.  HOME SUPPLY CENTER HAS TO BE CAPTURED FIRST''' 
    def _test_12B(self):
        ''' 12.B.  BUILD IN NON-STARTING POSITION ALLOWED''' 
    def _test_12C(self):
        ''' 12.C.  COUNTRIES CAN STILL ONLY BUILD IN HOME SUPPLY CENTERS''' 
    def _test_12D(self):
        ''' 12.D.  CIVIL DISORDER STILL BASED ON HOME SUPPLY CENTERS''' 

if __name__ == '__main__': unittest.main()
