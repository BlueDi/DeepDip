package ddejonge.bandana.exampleAgents;

import es.csic.iiia.fabregues.dip.Player;
import es.csic.iiia.fabregues.dip.board.*;
import es.csic.iiia.fabregues.dip.comm.CommException;
import es.csic.iiia.fabregues.dip.comm.IComm;
import es.csic.iiia.fabregues.dip.comm.daide.DaideComm;
import es.csic.iiia.fabregues.dip.orders.*;

import java.io.File;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.*;

public class RandomBot extends Player {
    private static final int DEFAULT_GAME_SERVER_PORT = 16713;
    private int finalYear;
    private Random random = new Random();

    /**
     * Client to connect with the game server.
     */
    IComm comm;

    /**
     * Constructor.
     * Note: this.name is the name of the player, e.g. 'RandomBot'.
     * On the other hand, me.getName() returns the name of the Power that this agent is playing, e.g.  'AUS', 'ENG', 'FRA', etcetera.
     *
     * @param name      Bot name on the communication server
     * @param finalYear After this year, the bot tries to call DRAW
     */
    RandomBot(String name, int finalYear, String logPath) {
        super(logPath);
        this.name = "RandomBot";
        this.finalYear = finalYear;

        //Initialize the client
        try {
            InetAddress gameServerIp = InetAddress.getLocalHost();
            this.comm = new DaideComm(gameServerIp, DEFAULT_GAME_SERVER_PORT, name);
        } catch (UnknownHostException e) {
            e.printStackTrace();
        }
    }

    /**
     * Main method to start the agent.
     *
     * @param args command line args
     */
    public static void main(String[] args) {
        String name = "Random Negotiatior";
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
        RandomBot randomBot = new RandomBot(name, finalYear, logPath);

        try {
            randomBot.start(randomBot.comm);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * This method is called once, at the start of the game, before the 'game' field is set.
     * <p>
     * It is called when the HLO message is received from the game server.
     * The HLO contains information about the game such as the power assigned to you, and the deadlines.
     * <p>
     * The power you are playing is stored in the field 'me'.
     * The game field will still be null when this method is called.
     * <p>
     * It is not necessary to implement this method.
     */
    @Override
    public void init() {
        System.out.println("Player " + this.name + " has started and is playing as: " + me.getName());
    }


    /**
     * This method is automatically called at the start of the game, after the 'game' field is set.
     * <p>
     * It is called when the first NOW message is received from the game server.
     * The NOW message contains the current phase and the positions of all the units.
     * <p>
     * Note: the init() method is called before the start() method.
     * <p>
     * It is not necessary to implement this method
     */
    @Override
    public void start() {
    }

    /**
     * This is the most important method of your agent!
     * Here is where you actually implement the behavior of your agent.
     * <p>
     * This method is automatically called every time when the game is in a new phase.
     * You must implement this method to return a list of orders for your units.
     *
     * @return An order for each unit of the power you are playing.
     */
    @Override
    public List<Order> play() {
        if (game.getPhase() == Phase.SPR || game.getPhase() == Phase.FAL) {
            //WE ARE IN A MOVE PHASE.
            return generateRandomMoveOrders();
        } else if (game.getPhase() == Phase.SUM || game.getPhase() == Phase.AUT) {
            //WE ARE IN A RETREAT PHASE
            return generateRandomRetreatOrders();
        } else {
            //WE ARE IN A BUILD PHASE

            // Count how many new units we can build. If this number is negative it means we
            // need to remove some units.
            int numberOfBuilds = me.getOwnedSCs().size() - me.getControlledRegions().size();

            if (numberOfBuilds < 0) {
                int numberOfRemoves = -numberOfBuilds;
                return generateRandomRemoveOrders(numberOfRemoves);
            } else if (numberOfBuilds > 0) {
                return generateRandomBuildOrders(numberOfBuilds);
            } else {
                //If we can't build any new units, and we don't need to remove any units, then
                // simply return an empty list.
                return new ArrayList<>();
            }
        }
    }

    /**
     * After each power has submitted its orders, this method is called several times:
     * once for each order submitted by any power.
     * <p>
     * You can use this to verify whether your allies have obeyed their agreements.
     *
     * @param arg0 Order submitted by another player
     */
    @Override
    public void receivedOrder(Order arg0) {
    }

    /**
     * Generates a random list of orders for Spring or Fal phases.<br/>
     *
     * @return A list containing exactly one order for each of our units.
     */
    private List<Order> generateRandomMoveOrders() {
        //list to store our orders
        List<Order> orders = new ArrayList<>();

        //list containing our units
        List<Region> units = new ArrayList<>(me.getControlledRegions());

        //For every order we create we use this table to map its destination to the order.
        // This is useful for creating support orders.
        HashMap<Province, Order> destination2order = new HashMap<>();

        for (Region unit : units) {
            //create a list of possible regions the unit could move into
            List<Region> potentialDestinations = new ArrayList<>(unit.getAdjacentRegions());
            // Also add the current location to this list (the unit may hold instead of move)
            potentialDestinations.add(unit);

            //choose a random destination:
            int randomInt = random.nextInt(potentialDestinations.size());
            Region destination = potentialDestinations.get(randomInt);

            //add new order to list of orders
            if (unit.equals(destination)) {
                Order newOrder = getHoldOrder(unit, destination2order);
                orders.add(newOrder);
                destination2order.put(unit.getProvince(), newOrder);
            } else {
                MTOOrder mtoOrder = new MTOOrder(me, unit, destination);
                orders.add(mtoOrder);

                destination2order.put(mtoOrder.getDestination().getProvince(), mtoOrder);
            }
        }

        return orders;
    }

    Order getHoldOrder(Region unit, HashMap<Province, Order> destination2order) {
        //If the current location of the unit equals its destination, then we
        // create a Hold order, or a Support Order.
        Order newOrder = null;
        // To create a support order, we must check that its location is adjacent to any province
        // that is the destination of another order.
        Order orderThatCanReceiveSupport;
        for (Region adjacentRegion : unit.getAdjacentRegions()) {
            Province adjacentProvince = adjacentRegion.getProvince();

            orderThatCanReceiveSupport = destination2order.get(adjacentProvince);
            if (orderThatCanReceiveSupport != null) {
                if (orderThatCanReceiveSupport instanceof MTOOrder) {
                    if (!((MTOOrder) orderThatCanReceiveSupport).getDestination().equals(unit)) {
                        newOrder = new SUPMTOOrder(me, unit, (MTOOrder) orderThatCanReceiveSupport);
                    }
                } else {
                    newOrder = new SUPOrder(me, unit, orderThatCanReceiveSupport);
                }
                break;
            }
        }

        //If the current unit can't give support to any other unit, then we create a hold order.
        if (newOrder == null) {
            newOrder = new HLDOrder(me, unit);
        }

        return newOrder;
    }

    List<Order> generateRandomRetreatOrders() {
        List<Order> orders = new ArrayList<>();
        int randomInt;

        //get a table that maps each unit to a Dislodgement object, which contains a list
        // of possible destinations where that unit can legally retreat to.
        HashMap<Region, Dislodgement> unit2dislodgement = game.getDislodgedRegions();
        //Get a list of all my units that are dislodged (i.e. units that must retreat)
        List<Region> dislodgedUnits = game.getDislodgedRegions(me);
        for (Region unit : dislodgedUnits) {
            //Get the potential destinations for the unit.
            Dislodgement dislodgement = unit2dislodgement.get(unit);
            List<Region> potentialDestinations = dislodgement.getRetreateTo();

            if (potentialDestinations.size() == 0) {
                // if the unit has no destinations where it could retreat to, then we have to disband it.
                orders.add(new DSBOrder(unit, me));
            } else {
                //otherwise, pick a random destination for the unit and retreat to there.
                randomInt = random.nextInt(potentialDestinations.size());
                Region retreatDestination = potentialDestinations.get(randomInt);
                orders.add(new RTOOrder(unit, me, retreatDestination));
            }
        }

        return orders;
    }

    List<Order> generateRandomBuildOrders(int nBuilds) {

        //list to store our orders
        List<Order> orders = new ArrayList<>(nBuilds);

        //we can build in any region of a province that is:
        //1. a home province, and
        //2. owned by us, and
        //3. currently not occupied (controlled)

        // Create a list of such available provinces.
        List<Province> availableProvinces = new ArrayList<>();
        for (Province province : me.getHomes()) { //loop over all my Home Supply Centers
            if (me.isOwning(province) && !me.isControlling(province)) { //check that i am the current owner and that I do not have any units in that province.
                availableProvinces.add(province);
            }
        }

        //fill the list of orders
        for (int i = 0; i < nBuilds && availableProvinces.size() > 0; i++) {
            //Pick a province to build in, and remove it from the list of available provinces.
            int randomInt = random.nextInt(availableProvinces.size());
            Province provinceToBuildIn = availableProvinces.remove(randomInt);

            //Pick a region from that province to build in.
            randomInt = random.nextInt(provinceToBuildIn.getRegions().size());
            Region regionToBuildIn = provinceToBuildIn.getRegions().get(randomInt);

            //Create the Build Order and add it to the list of orders.
            orders.add(new BLDOrder(me, regionToBuildIn));
        }

        //If we still have some  builds left, but we don't have any more available provinces to build in,
        // then submit Waive Orders.
        while (orders.size() < nBuilds) {
            orders.add(new WVEOrder(me));
        }


        return orders;
    }

    List<Order> generateRandomRemoveOrders(int nRemoves) {

        //list to store our orders
        List<Order> orders = new ArrayList<>();

        //list containing our units
        List<Region> units = new ArrayList<>(me.getControlledRegions());

        for (int i = 0; i < nRemoves && units.size() > 0; i++) {
            int randomInt = random.nextInt(units.size());
            Region unit = units.remove(randomInt);
            orders.add(new REMOrder(me, unit));
        }

        return orders;
    }


    /**
     * This method is automatically called after every phase.
     * <p>
     * It is not necessary to implement it.
     *
     * @param gameState State of the game at the moment
     */
    @Override
    public void phaseEnd(GameState gameState) {
        //To prevent games from taking too long, we automatically propose a draw after
        // the FAL phase of the year that is set as the final tear.
        if ((game.getYear() == this.finalYear && game.getPhase() == Phase.FAL) || game.getYear() > this.finalYear) {
            proposeDraw();
        }
    }


    /**
     * You can call this method if you want to propose a draw.
     * <p>
     * If all players that are not yet eliminated propose a draw in the same phase, then
     * the server ends the game.
     * <p>
     * Copy-paste this method into your own bot if you want it to be able to propose draws.
     */
    private void proposeDraw() {
        try {
            comm.sendMessage(new String[]{"DRW"});
        } catch (CommException e) {
            e.printStackTrace();
        }
    }


    /**
     * This method is automatically called when the game is over.
     * <p>
     * The message contains about the names of the players, the powers they played and the
     * number of supply centers owned at the end of the game.
     */
    @Override
    public void handleSMR(String[] message) {
        System.out.println("handleSMR() " + Arrays.toString(message));

        //disconnect from the game server.
        this.comm.stop();

        //Call exit to stop the player.
        exit();
    }


    /**
     * This method is automatically called if you submit an illegal order for one of your units.
     * <p>
     * It is highly recommended to copy-paste this method into your own bot because it allows you to
     * see what went wrong if it accidentally submitted a wrong order.
     * <p>
     * MBV means: Order is OK.
     *
     * @param message Array of messages that have errors
     */
    @Override
    public void submissionError(String[] message) {
        if (message.length < 2) { //This should not happen, but just in case...
            System.err.println("submissionError() " + Arrays.toString(message));
            return;
        }

        //Extract the illegal order from the message and print it.
        StringBuilder illegalOrder = new StringBuilder();
        for (int i = 2; i < message.length - 4; i++) {
            illegalOrder.append(message[i]).append(" ");
        }
        System.err.println("Illegal order submitted: " + illegalOrder);
        //Extract the type of error from the message and print a statement explaining the error
        String errorType = message[message.length - 2];
        switch (errorType) {
            case "FAR":
                System.err.println("Reason: Unit is trying to move to a non-adjacent region, or is trying to support a move to a non-adjacent region.");
                break;
            case "NSP":
                System.err.println("Reason: No such province.");
                break;
            case "NSU":
                System.err.println("Reason: No such unit.");
                break;
            case "NAS":
                System.err.println("Reason: Not at sea (for a convoying fleet)");
                break;
            case "NSF":
                System.err.println("Reason: No such fleet (in VIA section of CTO or the unit performing a CVY)");
                break;
            case "NSA":
                System.err.println("Reason: No such army (for unit being ordered to CTO or for unit being CVYed)");
                break;
            case "NYU":
                System.err.println("Reason: Not your unit");
                break;
            case "NRN":
                System.err.println("Reason: No retreat needed for this unit");
                break;
            case "NVR":
                System.err.println("Reason: Not a valid retreat space");
                break;
            case "YSC":
                System.err.println("Reason: Not your supply centre");
                break;
            case "ESC":
                System.err.println("Reason: Not an empty supply centre");
                break;
            case "HSC":
                System.err.println("Reason: Not a home supply centre");
                break;
            case "NSC":
                System.err.println("Reason: Not a supply centre");
                break;
            case "CST":
                System.err.println("Reason: No coast specified for fleet build in StP, or an attempt to build a fleet inland, or an army at sea.");
                break;
            case "NMB":
                System.err.println("Reason: No more builds allowed");
                break;
            case "NMR":
                System.err.println("Reason: No more removals allowed");
                break;
            case "NRS":
                System.err.println("Reason: Not the right season");
                break;
            default:
                System.err.println("submissionError() Received error message of unknown type: " + Arrays.toString(message));
                break;
        }
    }
}
