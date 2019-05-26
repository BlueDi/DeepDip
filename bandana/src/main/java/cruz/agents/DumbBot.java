package cruz.agents;

import es.csic.iiia.fabregues.dip.Player;
import es.csic.iiia.fabregues.dip.board.*;
import es.csic.iiia.fabregues.dip.comm.CommException;
import es.csic.iiia.fabregues.dip.comm.Comm;
import es.csic.iiia.fabregues.dip.comm.IComm;
import es.csic.iiia.fabregues.dip.comm.daide.DaideComm;
import es.csic.iiia.fabregues.dip.orders.*;
import es.csic.iiia.fabregues.utilities.Interface;

import java.io.File;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.*;
import java.util.List;

public class DumbBot extends Player {
    private final int[] m_spr_prox_weight = new int[]{100, 1000, 30, 10, 6, 5, 4, 3, 2, 1};
    private final int[] m_fall_prox_weight = new int[]{1000, 100, 30, 10, 6, 5, 4, 3, 2, 1};
    private final int[] m_build_prox_weight = new int[]{1000, 100, 30, 10, 6, 5, 4, 3, 2, 1};
    private final int[] m_rem_prox_weight = new int[]{1000, 100, 30, 10, 6, 5, 4, 3, 2, 1};
    private HashMap<Province, Float> defenseValue;
    private HashMap<Province, Float> attackValue;
    private HashMap<Province, Integer> strengthValue;
    private HashMap<Province, Integer> competitionValue;
    private HashMap<Region, Float[]> proximity;
    private HashMap<Region, Integer> destinationValue;

    private static final int DEFAULT_GAME_SERVER_PORT = 16713;
    private int finalYear;

    IComm icomm;

    DumbBot(String name, int finalYear, String logPath) {
        super(logPath);
        this.name = name;
        this.finalYear = finalYear;

        try {
            InetAddress gameServerIp = InetAddress.getLocalHost();
            this.icomm = new DaideComm(gameServerIp, DEFAULT_GAME_SERVER_PORT, this.name);
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
        String name = "DumbBot";
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
        DumbBot dumbBot = new DumbBot(name, finalYear, logPath);

        try {
            dumbBot.start(dumbBot.icomm);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Override
    public void init() {}

    @Override
    public void start() {}

    @Override
    public void start(IComm comm) {
        this.name = comm.getName();
        this.log = new Interface(this.logPath + "dip_" + this.name);
        this.comm = new Comm(comm, this);
        try {
            this.comm.start();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public List<Order> play() {
        this.calculateFactors();
        this.calculateDestinationValue();
        return this.generateOrders();
    }

    private float getSize(Power power) {
        if (power == null) {
            return 0.0F;
        } else {
            float ownedSCs = (float) power.getOwnedSCs().size();
            return ownedSCs * ownedSCs * 1.0F + ownedSCs * 4.0F + 16.0F;
        }
    }

    List<Order> generateOrders() {
        switch (game.getPhase().ordinal() + 1) {
            case 1:
            case 3:
                return this.generateMovementOrders();
            case 2:
            case 4:
                return this.generateRetreatOrders();
            case 5:
                int nBuilds = this.me.getOwnedSCs().size() - this.me.getControlledRegions().size();
                if (nBuilds < 0) {
                    return this.generateRemoveOrders(-nBuilds);
                } else {
                    if (nBuilds > 0) {
                        return this.generateBuildOrders(nBuilds);
                    }

                    return new ArrayList<>();
                }
            default:
                return null;
        }
    }

    List<Order> generateMovementOrders() {
        List<Order> orders = new ArrayList<>(this.me.getControlledRegions().size());
        boolean selectionIsOK;
        boolean orderUnitToMove;
        Random r = new Random(System.currentTimeMillis());
        List<Region> units = new ArrayList<>();
        this.copy(units, this.me.getControlledRegions());

        while (!units.isEmpty()) {
            Region unit = units.get(0);
            List<Region> destList = new ArrayList<>(unit.getAdjacentRegions().size() + 1);
            this.copy(destList, unit.getAdjacentRegions());
            destList.add(unit);
            destList.sort(new DestValueComparator(this.destinationValue));
            Region destination;

            label100:
            do {
                destination = destList.get(0);
                boolean tryNextNode = true;
                int provCount = 1;

                while (true) {
                    while (true) {
                        while (tryNextNode) {
                            if (provCount < destList.size()) {
                                Region nextDest = destList.get(provCount++);
                                int nextNodeChance;
                                if (this.destinationValue.get(destination) == 0) {
                                    nextNodeChance = 0;
                                } else {
                                    nextNodeChance = Math.round((float) (this.destinationValue.get(destination) - this.destinationValue.get(nextDest)) * 500.0F / (float) (Integer) this.destinationValue.get(destination));
                                }

                                if (r.nextInt(100) < 50 && r.nextInt(100) >= nextNodeChance) {
                                    destination = nextDest;
                                } else {
                                    tryNextNode = false;
                                }
                            } else {
                                tryNextNode = false;
                            }
                        }

                        selectionIsOK = true;
                        orderUnitToMove = true;
                        if (unit.equals(destination)) {
                            orders.add(new HLDOrder(this.me, destination));
                        } else {
                            if (this.me.getControlledRegions().contains(destination)) {
                                Order alreadyOrdered = null;

                                for (Order order : orders) {
                                    if (order.getLocation().equals(destination)) {
                                        alreadyOrdered = order;
                                        break;
                                    }
                                }

                                if (alreadyOrdered == null) {
                                    units.add(units.indexOf(destination) + 1, unit);
                                    orderUnitToMove = false;
                                } else if (!(alreadyOrdered instanceof MTOOrder)) {
                                    if (this.competitionValue.get(destination.getProvince()) > 1) {
                                        orders.add(new SUPOrder(this.me, unit, alreadyOrdered));
                                        orderUnitToMove = false;
                                    } else {
                                        selectionIsOK = false;
                                        destList.remove(destination);
                                    }
                                }
                            }

                            Province destProvince = destination.getProvince();
                            MTOOrder beingMovedTo = null;

                            for (Order order : orders) {
                                if (order instanceof MTOOrder && ((MTOOrder) order).getDestination().getProvince().equals(destProvince)) {
                                    beingMovedTo = (MTOOrder) order;
                                    break;
                                }
                            }

                            if (beingMovedTo != null) {
                                if (this.competitionValue.get(destProvince) > 0) {
                                    orders.add(new SUPMTOOrder(this.me, unit, beingMovedTo));
                                    orderUnitToMove = false;
                                } else {
                                    selectionIsOK = false;
                                    destList.remove(destination);
                                }
                            }

                            if (selectionIsOK && orderUnitToMove) {
                                orders.add(new MTOOrder(this.me, unit, destination));
                            }
                        }
                        continue label100;
                    }
                }
            } while (!selectionIsOK);

            units.remove(0);
        }

        return this.checkForWastedHolds(orders);
    }

    private void copy(List<Region> units, List<Region> controlledRegions) {
        units.addAll(controlledRegions);
    }

    private List<Order> checkForWastedHolds(List<Order> orders) {
        List<Region> units = this.me.getControlledRegions();
        Iterator var4 = units.iterator();

        while (true) {
            Region unit;
            Region unitSupported;
            int maxDestValue;
            label124:
            do {
                Order currentUnitOrder;
                do {
                    if (!var4.hasNext()) {
                        for (int k = 0; k < orders.size(); ++k) {
                            Order order = orders.get(k);
                            int count = 0;

                            for (Order order2 : orders) {
                                if (order.getLocation().equals(order2.getLocation())) {
                                    ++count;
                                }
                            }

                            int i = orders.size() - 1;

                            for (int j = 1; i >= 0 && j < count; --i) {
                                Order order2 = orders.get(i);
                                if (order.getLocation().equals(order2.getLocation())) {
                                    orders.remove(i);
                                    ++j;
                                }
                            }
                        }

                        return orders;
                    }

                    unit = (Region) var4.next();
                    Region destination = null;
                    unitSupported = null;
                    currentUnitOrder = null;

                    for (Order order : orders) {
                        if (order.getLocation().equals(unit)) {
                            currentUnitOrder = order;
                            break;
                        }
                    }
                } while (!(currentUnitOrder instanceof HLDOrder));

                maxDestValue = 0;
                List<Region> destList = new ArrayList<>(unit.getAdjacentRegions().size());
                this.copy(destList, unit.getAdjacentRegions());
                Collections.shuffle(destList, new Random(System.currentTimeMillis()));
                Iterator var11 = destList.iterator();

                while (true) {
                    while (true) {
                        if (!var11.hasNext()) {
                            continue label124;
                        }

                        Region dest = (Region) var11.next();
                        boolean isBeingMovedTo = false;
                        MTOOrder mto = null;
                        Iterator var15 = orders.iterator();

                        Order destUnitOrder;
                        while (var15.hasNext()) {
                            destUnitOrder = (Order) var15.next();
                            if (destUnitOrder instanceof MTOOrder) {
                                mto = (MTOOrder) destUnitOrder;
                                if (mto.getDestination().equals(dest)) {
                                    isBeingMovedTo = true;
                                }
                            }
                        }

                        if (isBeingMovedTo) {
                            if (this.competitionValue.get(dest.getProvince()) > 0 && this.destinationValue.get(dest) > maxDestValue) {
                                maxDestValue = this.destinationValue.get(dest);
                                unitSupported = mto.getLocation();
                            }
                        } else if (this.me.isControlling(dest)) {
                            destUnitOrder = null;

                            for (Order or : orders) {
                                if (or.getLocation().equals(dest)) {
                                    destUnitOrder = or;
                                    break;
                                }
                            }

                            if (!(destUnitOrder instanceof MTOOrder) && this.competitionValue.get(dest.getProvince()) > 1 && this.destinationValue.get(dest) > maxDestValue) {
                                maxDestValue = this.destinationValue.get(dest);
                                unitSupported = dest;
                            }
                        }
                    }
                }
            } while (maxDestValue <= 0);

            Order unitSupportedOrder = null;

            for (Order order : orders) {
                if (order.getLocation().equals(unitSupported)) {
                    unitSupportedOrder = order;
                    break;
                }
            }

            if (!(unitSupportedOrder instanceof MTOOrder)) {
                orders.add(new SUPOrder(this.me, unit, unitSupportedOrder));
            } else {
                orders.add(new SUPMTOOrder(this.me, unit, (MTOOrder) unitSupportedOrder));
            }
        }
    }

    List<Order> generateRetreatOrders() {
        List<Order> orders = new ArrayList<>(this.game.getDislodgedRegions().size());
        Random rn = new Random(System.currentTimeMillis());
        HashMap<Region, Dislodgement> units = this.game.getDislodgedRegions();
        List<Region> dislodgedUnits = this.game.getDislodgedRegions(this.me);

        for (Region region : dislodgedUnits) {
            Dislodgement dislodgement = units.get(region);
            List<Region> dest = new ArrayList<>();
            this.copy(dest, dislodgement.getRetreateTo());
            boolean selectionIsOK;

            do {
                if (dest.size() == 0) {
                    orders.add(new DSBOrder(region, this.me));
                    selectionIsOK = true;
                } else {
                    Region currentNode = dest.get(0);

                    for (int i = 1; i < dest.size(); ++i) {
                        Region nextNode = dest.get(i);
                        int nextNodeChance;
                        if (this.destinationValue.get(currentNode) == 0) {
                            nextNodeChance = 0;
                        } else {
                            nextNodeChance = (this.destinationValue.get(currentNode) - this.destinationValue.get(nextNode)) * 500 / this.destinationValue.get(currentNode);
                        }

                        if (rn.nextInt(100) < 50 && rn.nextInt(100) >= nextNodeChance) {
                            currentNode = nextNode;
                        }
                    }

                    selectionIsOK = true;

                    for (Order order : orders) {
                        if (order instanceof RTOOrder) {
                            Province provinceToRetreate = ((RTOOrder) order).getDestination().getProvince();
                            if (provinceToRetreate.equals(currentNode.getProvince())) {
                                selectionIsOK = false;
                                dest.remove(currentNode);
                            }
                        }
                    }

                    if (selectionIsOK) {
                        orders.add(new RTOOrder(region, this.me, currentNode));
                    }
                }

            } while (!selectionIsOK);
        }

        return orders;
    }

    List<Order> generateRemoveOrders(int nRemoves) {
        List<Region> regions = new ArrayList<>();
        this.copy(regions, this.me.getControlledRegions());
        regions.sort(new DestValueComparator(this.destinationValue));
        List<Order> orders = new ArrayList<>(nRemoves);

        for (int i = 0; i < nRemoves; ++i) {
            Region value = regions.get(i);
            orders.add(new REMOrder(this.me, value));
        }

        return orders;
    }

    List<Order> generateBuildOrders(int nBuilds) {
        Random r = new Random(System.currentTimeMillis());
        if (nBuilds <= 0) {
            return new ArrayList<>();
        } else {
            List<Order> orders = new ArrayList<>(nBuilds);
            List<Region> valuedHomeRegions = new ArrayList<>();
            this.copy(valuedHomeRegions, this.getBuildHomeList(this.me));
            valuedHomeRegions.sort(new DestValueComparator(this.destinationValue));

            label66:
            while (!valuedHomeRegions.isEmpty() && nBuilds > 0) {
                boolean tryNextHome = true;
                Region currentHome = valuedHomeRegions.get(0);
                int homeCounter = 0;

                while (true) {
                    while (true) {
                        while (tryNextHome) {
                            if (homeCounter < valuedHomeRegions.size()) {
                                Region nextHome = valuedHomeRegions.get(homeCounter++);
                                int nextHomeChance;
                                if (this.destinationValue.get(nextHome) == 0) {
                                    nextHomeChance = 0;
                                } else {
                                    nextHomeChance = (this.destinationValue.get(currentHome) - this.destinationValue.get(nextHome)) * 500 / this.destinationValue.get(currentHome);
                                }

                                if (r.nextInt(100) < 50 && r.nextInt(100) >= nextHomeChance) {
                                    currentHome = nextHome;
                                } else {
                                    tryNextHome = false;
                                }
                            } else {
                                tryNextHome = false;
                            }
                        }

                        orders.add(new BLDOrder(this.me, currentHome));
                        List<Region> sameNodeList = currentHome.getProvince().getRegions();

                        for (Region region : sameNodeList) {
                            valuedHomeRegions.remove(region);
                        }

                        --nBuilds;
                        continue label66;
                    }
                }
            }

            for (int i = 0; i < nBuilds; ++i) {
                orders.add(new WVEOrder(this.me));
            }

            return orders;
        }
    }

    private List<Region> getBuildHomeList(Power me) {
        List<Region> homeRegions = new ArrayList<>();

        for (Province province : me.getHomes()) {
            if (me.isOwning(province) && this.game.getController(province) == null) {
                homeRegions.addAll(province.getRegions());
            }
        }

        return homeRegions;
    }

    private void calculateDestinationValue() {
        switch (game.getPhase().ordinal() + 1) {
            case 1:
            case 2:
                this.calculateDestinationValue(this.m_spr_prox_weight, 1000, 1000);
                break;
            case 3:
            case 4:
                this.calculateDestinationValue(this.m_fall_prox_weight, 1000, 1000);
                break;
            case 5:
                if (this.me.getOwnedSCs().size() > this.me.getControlledRegions().size()) {
                    this.calculateWINDestinationValue(this.m_rem_prox_weight, 1000);
                } else {
                    this.calculateWINDestinationValue(this.m_build_prox_weight, 1000);
                }
        }

    }

    private void calculateDestinationValue(int[] prox_weight, int strength_weight, int competition_weight) {
        this.destinationValue = new HashMap<>(this.game.getRegions().size());

        for (Region region : this.game.getRegions()) {
            int destWeight = 0;

            for (int i = 0; i < 10; ++i) {
                destWeight = (int) ((float) destWeight + this.proximity.get(region)[i] * (float) prox_weight[i]);
            }

            destWeight += strength_weight * this.strengthValue.get(region.getProvince());
            destWeight -= competition_weight * this.competitionValue.get(region.getProvince());
            this.destinationValue.put(region, destWeight);
        }

        List<Region> regions = this.game.getRegions();
        regions.sort(new DestValueComparator(this.destinationValue));
    }

    private void calculateWINDestinationValue(int[] prox_weight, int defense_weight) {
        this.destinationValue = new HashMap<>(this.game.getRegions().size());

        for (Region region : this.game.getRegions()) {
            int destWeight = 0;

            for (int proxCount = 0; proxCount < 10; ++proxCount) {
                destWeight = (int) ((float) destWeight + this.proximity.get(region)[proxCount] * (float) prox_weight[proxCount]);
            }

            destWeight = (int) ((float) destWeight + (float) defense_weight * this.defenseValue.get(region.getProvince()));
            this.destinationValue.put(region, destWeight);
        }
    }

    private Power getOwner(Province province) {
        for (Power power : this.game.getPowers()) {
            if (power.getOwnedSCs().contains(province)) {
                return power;
            }
        }
        return null;
    }

    private float calcDefVal(Province province) {
        float maxPower = 0.0F;
        List<Region> adjacentRegions = new ArrayList<>();
        List<Power> neighborPowers = new ArrayList<>();
        Iterator var6 = province.getRegions().iterator();

        Region region;
        while (var6.hasNext()) {
            region = (Region) var6.next();
            adjacentRegions.addAll(region.getAdjacentRegions());
        }

        var6 = adjacentRegions.iterator();

        while (var6.hasNext()) {
            region = (Region) var6.next();
            neighborPowers.add(this.game.getController(region));
        }

        var6 = neighborPowers.iterator();

        while (var6.hasNext()) {
            Power power = (Power) var6.next();
            if (power != null && !power.equals(this.me) && this.getSize(power) > maxPower) {
                maxPower = this.getSize(power);
            }
        }

        return maxPower;
    }

    @Override
    public void receivedOrder(Order arg0) {
    }

    private void calculateFactors() {
        int prox_att_weight = 0;
        int prox_def_weight = 0;
        switch (this.game.getPhase().ordinal()) {
            case 1:
            case 2:
            case 5:
                prox_att_weight = 700;
                prox_def_weight = 300;
                break;
            case 3:
            case 4:
                prox_att_weight = 600;
                prox_def_weight = 400;
                break;
        }

        this.defenseValue = new HashMap<>();
        this.attackValue = new HashMap<>();
        Iterator var4 = this.game.getProvinces().iterator();

        while (var4.hasNext()) {
            Province province = (Province) var4.next();
            if (province.isSC()) {
                if (this.me.getOwnedSCs().contains(province)) {
                    this.defenseValue.put(province, this.calcDefVal(province));
                    this.attackValue.put(province, 0.0F);
                } else {
                    this.attackValue.put(province, this.getSize(this.getOwner(province)));
                    this.defenseValue.put(province, 0.0F);
                }
            } else {
                this.attackValue.put(province, 0.0F);
                this.defenseValue.put(province, 0.0F);
            }
        }

        this.proximity = new HashMap<>();
        var4 = this.game.getProvinces().iterator();

        while (var4.hasNext()) {
            Province province = (Province) var4.next();

            for (Region region : province.getRegions()) {
                Float[] nearby = new Float[10];
                nearby[0] = this.attackValue.get(province) * (float) prox_att_weight + this.defenseValue.get(province) * (float) prox_def_weight;
                this.proximity.put(region, nearby);
            }
        }

        for (int proxCount = 1; proxCount < 10; ++proxCount) {

            for (Province province : this.game.getProvinces()) {
                Region region;
                label65:
                for (Iterator var16 = province.getRegions().iterator(); var16.hasNext(); this.proximity.get(region)[proxCount] = this.proximity.get(region)[proxCount] / 5.0F) {
                    region = (Region) var16.next();
                    Float[] proximities = this.proximity.get(region);
                    proximities[proxCount] = proximities[proxCount - 1];
                    Region multipleCoasts = null;
                    Iterator var11 = region.getAdjacentRegions().iterator();

                    while (true) {
                        while (true) {
                            if (!var11.hasNext()) {
                                continue label65;
                            }

                            Region adjRegion = (Region) var11.next();
                            if (adjRegion.getName().substring(4).compareTo("CS") == 0 && multipleCoasts != null) {
                                if (this.proximity.get(adjRegion)[proxCount - 1] > this.proximity.get(multipleCoasts)[proxCount - 1]) {
                                    this.proximity.get(region)[proxCount] = this.proximity.get(region)[proxCount] - this.proximity.get(multipleCoasts)[proxCount - 1] + this.proximity.get(adjRegion)[proxCount - 1];
                                }
                            } else {
                                this.proximity.get(region)[proxCount] = this.proximity.get(region)[proxCount] + this.proximity.get(adjRegion)[proxCount - 1];
                                if (adjRegion.getName().substring(4).compareTo("CS") == 0) {
                                    multipleCoasts = adjRegion;
                                }
                            }
                        }
                    }
                }
            }
        }

        this.initStrCompValues();
    }

    private void initStrCompValues() {
        this.strengthValue = new HashMap<>();
        this.competitionValue = new HashMap<>();
        Iterator var2 = this.game.getProvinces().iterator();

        Province province;
        while (var2.hasNext()) {
            province = (Province) var2.next();
            HashMap<Power, Integer> adjUnitCount = new HashMap<>();

            Power power;
            Iterator var5;
            int count;
            label59:
            for (var5 = this.game.getPowers().iterator(); var5.hasNext(); adjUnitCount.put(power, count)) {
                power = (Power) var5.next();
                count = 0;
                Iterator var8 = power.getControlledRegions().iterator();

                while (true) {
                    while (true) {
                        if (!var8.hasNext()) {
                            continue label59;
                        }

                        Region unit = (Region) var8.next();

                        for (Region region : province.getRegions()) {
                            if (region.getAdjacentRegions().contains(unit)) {
                                ++count;
                                break;
                            }
                        }
                    }
                }
            }

            var5 = this.game.getPowers().iterator();

            while (var5.hasNext()) {
                power = (Power) var5.next();
                if (power.equals(this.me)) {
                    this.strengthValue.put(province, adjUnitCount.get(this.me));
                } else if (!this.competitionValue.containsKey(province)) {
                    this.competitionValue.put(province, adjUnitCount.get(power));
                } else if (adjUnitCount.get(power) > this.competitionValue.get(province)) {
                    this.competitionValue.put(province, adjUnitCount.get(power));
                }
            }
        }

        var2 = this.game.getProvinces().iterator();

        while (var2.hasNext()) {
            province = (Province) var2.next();
            if (!this.competitionValue.containsKey(province)) {
                this.competitionValue.put(province, 0);
            }

            if (!this.strengthValue.containsKey(province)) {
                this.strengthValue.put(province, 0);
            }
        }

    }

    @Override
    public void phaseEnd(GameState gameState) {
        if ((game.getYear() == this.finalYear && game.getPhase() == Phase.FAL) || game.getYear() > this.finalYear) {
            proposeDraw();
        }
    }

    private void proposeDraw() {
        try {
            comm.sendMessage(new String[]{"DRW"});
        } catch (CommException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void handleSMR(String[] message) {
        //disconnect from the game server.
        this.comm.stop();

        //Call exit to stop the player.
        exit();
    }

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

class DestValueComparator implements Comparator<Region> {
    private HashMap<Region, Integer> destinationValue;

    DestValueComparator(HashMap<Region, Integer> destValue) {
        this.destinationValue = destValue;
    }

    public int compare(Region region1, Region region2) {
        return -this.destinationValue.get(region1).compareTo(this.destinationValue.get(region2));
    }
}

