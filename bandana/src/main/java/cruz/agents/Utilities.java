package cruz.agents;

import es.csic.iiia.fabregues.dip.board.Game;
import es.csic.iiia.fabregues.dip.board.Province;
import es.csic.iiia.fabregues.dip.board.Region;

import java.util.Vector;

public class Utilities {

    public static String getAllProvincesInformation(Game game) {
        Vector<Province> provinces = game.getProvinces();

        StringBuilder sb = new StringBuilder();

        for (Province p : provinces) {
            String name = p.getName();
            Vector<Region> regions = p.getRegions();
            boolean isSupplyCenter = p.isSC();

            sb.append("Province[Name: " + name + "; Regions: ");

            for (Region r : regions) {
                sb.append(r.getName() + ", ");
            }

            sb.append("; isSupplyCenter: " + isSupplyCenter + "]\n");
        }

        return sb.toString();

    }
}
