package ddejonge.bandana.exampleAgents;

import es.csic.iiia.fabregues.dip.board.Phase;
import es.csic.iiia.fabregues.dip.board.Province;
import es.csic.iiia.fabregues.dip.board.Region;
import es.csic.iiia.fabregues.dip.orders.MTOOrder;
import es.csic.iiia.fabregues.dip.orders.Order;
import es.csic.iiia.fabregues.dip.orders.SUPMTOOrder;

import java.io.File;
import java.util.*;

public class RandomExe extends RandomBot {
    private Random random = new Random();

    private RandomExe(String name, int finalYear, String logPath) {
        super(name, finalYear, logPath);
        this.name = "RandomBotExercise";
    }

    public static void main(String[] args) {
        String name = "Random Negotiatior Exercise";
        String logPath = "log/";
        int finalYear = 1905;

        for (int i = 0; i < args.length; i++) {
            if (args[i].equals("-name") && args.length > i + 1) {
                name = args[i + 1];
            }

            //set the path to store the log file
            if (args[i].equals("-log") && args.length > i + 1) {
                logPath = args[i + 1];
            }

            //set the final year
            if (args[i].equals("-fy") && args.length > i + 1) {
                try {
                    finalYear = Integer.parseInt(args[i + 1]);
                } catch (NumberFormatException e) {
                    System.err.println("main() The final year argument is not a valid integer: " + args[i + 1]);
                    return;
                }
            }
        }

        //Create the folder to store its log files.
        File logFolder = new File(logPath);
        logFolder.mkdirs();
        RandomExe randomBot = new RandomExe(name, finalYear, logPath);

        try {
            randomBot.start(randomBot.comm);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * At the beginning of the game prints out a list of names of all the provinces,
     * and for each province a list of names of all its regions
     */
    @Override
    public void start() {
        Vector<Province> provinces = game.getProvinces();
        System.out.println(game.getProvinces());

        provinces.forEach(province -> System.out.println(province.getRegions()));
    }

    @Override
    public List<Order> play() {
        if (game.getPhase() == Phase.SPR || game.getPhase() == Phase.FAL) {
            //WE ARE IN A MOVE PHASE.
            return generateMoveOrders();
        } else if (game.getPhase() == Phase.SUM || game.getPhase() == Phase.AUT) {
            //WE ARE IN A RETREAT PHASE
            return super.generateRandomRetreatOrders();
        } else {
            //WE ARE IN A BUILD PHASE

            // Count how many new units we can build. If this number is negative it means we
            // need to remove some units.
            int numberOfBuilds = me.getOwnedSCs().size() - me.getControlledRegions().size();

            if (numberOfBuilds < 0) {
                int numberOfRemoves = -numberOfBuilds;
                return super.generateRandomRemoveOrders(numberOfRemoves);
            } else if (numberOfBuilds > 0) {
                return super.generateRandomBuildOrders(numberOfBuilds);
            } else {
                //If we can't build any new units, and we don't need to remove any units, then
                // simply return an empty list.
                return new ArrayList<>();
            }
        }
    }

    /**
     * If it has a unit inside a Supply Center, which it currently does
     * not own, then make sure that it holds.
     * <p>
     * Otherwise, if a unit is in a province adjacent to a Supply Center
     * which it does not own, make sure it moves there.
     *
     * @return List of orders for each unit
     */
    private List<Order> generateMoveOrders() {
        List<Order> orders = new ArrayList<>();
        List<Region> units = new ArrayList<>(me.getControlledRegions());
        // For every order we create we use this table to map its destination to the order.
        // This is useful for creating support orders.
        HashMap<Province, Order> destination2order = new HashMap<>();

        System.err.println(me.getControlledRegions());
        System.err.println(me.getOwnedSCs());
        for (Region unit : units) {
            Region destination = getBestRegion(unit);
            Order newOrder = getBestOrder(unit, destination, orders, destination2order);

            orders.add(newOrder);
            if (newOrder instanceof MTOOrder) {
                destination2order.put(((MTOOrder) newOrder).getDestination().getProvince(), newOrder);
            } else {
                destination2order.put(unit.getProvince(), newOrder);
            }
        }
        return orders;
    }

    private Region getBestRegion(Region unit) {
        Region destination;
        Province currentProvince = unit.getProvince();

        if (!me.isOwning(currentProvince)) {
            destination = unit;
        } else {
            List<Region> potentialDestinations = new ArrayList<>(unit.getAdjacentRegions());
            potentialDestinations.add(unit);

            List<Region> nearNotOwnedSC = new ArrayList<>();
            List<Region> notSCButValid = new ArrayList<>();
            for (Region r : potentialDestinations) {
                if (!r.getProvince().isSC()) {
                    notSCButValid.add(r);
                } else {
                    nearNotOwnedSC.add(r);
                }
            }
            System.out.println(nearNotOwnedSC.size() + " " + notSCButValid.size());
            if (nearNotOwnedSC.isEmpty()) {
                int randomInt = random.nextInt(notSCButValid.size());
                destination = notSCButValid.get(randomInt);
            } else {
                int randomInt = random.nextInt(nearNotOwnedSC.size());
                destination = nearNotOwnedSC.get(randomInt);
            }
        }

        return destination;
    }

    private Order getBestOrder(Region unit, Region destination, List<Order> orders, HashMap<Province, Order> destination2order) {
        Order newOrder = null;
        if (unit.equals(destination)) {
            newOrder = getHoldOrder(unit, destination2order);
        } else {
            // The unit is not going to hold.
            List<MTOOrder> moveToOrders = new ArrayList<>();
            for (Order order : orders) {
                if (order instanceof MTOOrder) {
                    moveToOrders.add((MTOOrder) order);
                }
            }

            List<Region> potentialDestinations = new ArrayList<>(unit.getAdjacentRegions());
            for (MTOOrder o : moveToOrders) {
                boolean same_destination = o.getDestination().equals(destination);
                boolean destination_not_self = !o.getDestination().equals(unit);
                boolean valid_destination = potentialDestinations.contains(o.getLocation());
                if (same_destination && destination_not_self && valid_destination) {
                    newOrder = new SUPMTOOrder(me, unit, o);
                    break;
                }
            }
            if (newOrder == null) {
                newOrder = new MTOOrder(me, unit, destination);
            }
        }
        return newOrder;
    }
}
