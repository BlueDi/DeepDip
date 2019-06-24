package cruz.agents;

import ddejonge.bandana.tools.Logger;
import ddejonge.bandana.tournament.GameResult;
import es.csic.iiia.fabregues.dip.board.Game;
import es.csic.iiia.fabregues.dip.board.Power;
import es.csic.iiia.fabregues.dip.board.Region;
import es.csic.iiia.fabregues.dip.orders.*;

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class DeepDip extends DumbBot {
    // The OpenAI Adapter contains the necessary functions and fields to make the connection to the Open AI environment
    private OpenAIAdapter openAIAdapter;
    private Logger logger = new Logger();
    private String winner = null;

    private DeepDip(String name, int finalYear, String logPath) {
        super(name, finalYear, logPath);
        this.openAIAdapter = new OpenAIAdapter(this);
    }

    /**
     * Main method to start the agent.
     *
     * @param args command line args
     */
    public static void main(String[] args) {
        String name = "DeepDip";
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

        File logFolder = new File(logPath);
        logFolder.mkdirs();
        DeepDip deepDip = new DeepDip(name, finalYear, logPath);

        try {
            deepDip.start(deepDip.icomm);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Override
    public void init() {
        this.logger.enable(this.logPath, this.me.getName() + ".log");
        this.logger.writeToFile();
    }

    @Override
    public void start() {
        this.openAIAdapter.beginningOfGame();
    }

    List<Order> generateOrders() {
        switch (game.getPhase().ordinal() + 1) {
            case 1:
            case 3:
                List<Order> received_orders = this.openAIAdapter.getOrdersFromDeepDip();
                List<Order> orders = this.getOrdersOfControlledRegions(received_orders);

                if (this.isValidOrders(orders)) {
                    return orders;
                } else {
                    return this.generateHoldOrders();
                }
            case 2:
            case 4:
                return this.generateRetreatOrders();
            case 5:
                int nBuilds = this.me.getOwnedSCs().size() - this.me.getControlledRegions().size();
                if (nBuilds < 0) {
                    return this.generateRemoveOrders(-nBuilds);
                } else if (nBuilds > 0) {
                    return this.generateBuildOrders(nBuilds);
                }
        }
        return new ArrayList<>();
    }

    private List<Order> generateHoldOrders() {
        List<Region> units = new ArrayList<>(this.me.getControlledRegions());
        List<Order> orders = new ArrayList<>(units.size());

        while (!units.isEmpty()) {
            Region unit = units.get(0);
            orders.add(new HLDOrder(this.me, unit));
            units.remove(0);
        }

        return orders;
    }

    private List<Order> getOrdersOfControlledRegions(List<Order> orders) {
        if (orders.isEmpty()) {
            return orders;
        }

        List<Region> player_controlled_regions = this.me.getControlledRegions();
        List<Order> orders_of_controlled_regions = new ArrayList<>();
        for (Order unit_order : orders) {
            Region r = unit_order.getLocation();
            if (player_controlled_regions.contains(r)) {
                orders_of_controlled_regions.add(unit_order);
            }
        }

        return orders_of_controlled_regions;
    }

    private boolean isValidOrders(List<Order> orders) {
        try {
            if (orders.isEmpty()) {
                throw new Exception("EMPTY ORDERS");
            }

            if (this.isOnlySupportOrders(orders)) {
                throw new Exception("ONLY SUPPORT ORDERS");
            }

            List<MTOOrder> mto_orders = this.getMTOOrders(orders);

            for (Order unit_order : orders) {
                List<Region> adjacent_regions = unit_order.getLocation().getAdjacentRegions();
                if (unit_order instanceof MTOOrder && !adjacent_regions.contains(((MTOOrder) unit_order).getDestination())) {
                    throw new Exception("Bad destination in a MTOOrder.");
                } else if (unit_order instanceof SUPOrder) {
                    Region supported_region = ((SUPOrder) unit_order).getSupportedRegion();
                    List<Region> player_controlled_regions = this.me.getControlledRegions();
                    boolean isAdjacentRegions = adjacent_regions.contains(supported_region);
                    boolean isSupportedRegionControlled = player_controlled_regions.contains(supported_region);
                    if (!isAdjacentRegions || !isSupportedRegionControlled) {
                        throw new Exception("Bad supported region in a SUPOrder.");
                    }
                } else if (unit_order instanceof SUPMTOOrder) {
                    Region supported_region = ((SUPMTOOrder) unit_order).getSupportedRegion();
                    boolean isAdjacentRegions = adjacent_regions.contains(supported_region);
                    boolean hasMTOOrder = mto_orders.contains(((SUPMTOOrder) unit_order).getSupportedOrder());
                    if (!isAdjacentRegions || !hasMTOOrder) {
                        throw new Exception("Bad supported region in a SUPMTOOrder.");
                    }
                }
            }
        } catch (Exception e) {
            return false;
        }

        return true;
    }

    private boolean isOnlySupportOrders(List<Order> orders) {
        boolean hasOnlySupport = true;
        for (Order unit_order : orders) {
            if (unit_order instanceof MTOOrder || unit_order instanceof HLDOrder) {
                hasOnlySupport = false;
                break;
            }
        }
        return hasOnlySupport;
    }

    private List<MTOOrder> getMTOOrders(List<Order> orders) {
        List<MTOOrder> mto_orders = new ArrayList<>();
        for (Order unit_order : orders) {
            List<Region> adjacent_regions = unit_order.getLocation().getAdjacentRegions();
            if (unit_order instanceof MTOOrder && !adjacent_regions.contains(((MTOOrder) unit_order).getDestination())) {
                mto_orders.add((MTOOrder) unit_order);
            }
        }
        return mto_orders;
    }

    @Override
    public void handleSlo(String winner) {
        this.winner = winner;
        this.openAIAdapter.setWinner(winner);
        if (this.me.getName().equals(winner)) {
            System.out.println("GAME RESULT: " + this.me + " won with a solo victory.");
        } else {
            System.out.println("GAME RESULT: " + this.me + " did not win with a solo victory. " + winner + " won.");
        }
        super.handleSlo(winner);
    }

    @Override
    public void handleSMR(String[] message) {
        GameResult gameResult = new GameResult(message, 2);

        if (this.me.getControlledRegions().size() < 1) {
            this.openAIAdapter.setWinner("eliminated");
        } else if (this.winner == null) {
            this.openAIAdapter.setWinner("draw");
        }
        this.openAIAdapter.endOfGame(gameResult);

        System.out.println("END GAME: " + Arrays.toString(message));
        super.handleSMR(message);
        this.winner = null;
    }

    public Logger getLogger() {
        return this.logger;
    }

    public Game getGame() {
        return this.game;
    }

    public Power getMe() {
        return this.me;
    }
}

