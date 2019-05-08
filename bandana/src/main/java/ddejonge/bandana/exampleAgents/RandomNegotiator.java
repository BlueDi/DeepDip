package ddejonge.bandana.exampleAgents;


import java.io.File;
import java.io.IOException;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Random;

import ddejonge.bandana.negoProtocol.DMZ;
import ddejonge.bandana.negoProtocol.BasicDeal;
import ddejonge.bandana.negoProtocol.DiplomacyNegoClient;
import ddejonge.bandana.negoProtocol.DiplomacyProposal;
import ddejonge.bandana.negoProtocol.OrderCommitment;
import ddejonge.bandana.tools.Logger;
import ddejonge.bandana.tools.Utilities;
import ddejonge.negoServer.Message;
import ddejonge.negoServer.NegotiationClient.STATUS;
import es.csic.iiia.fabregues.dip.Player;
import es.csic.iiia.fabregues.dip.board.Dislodgement;
import es.csic.iiia.fabregues.dip.board.GameState;
import es.csic.iiia.fabregues.dip.board.Phase;
import es.csic.iiia.fabregues.dip.board.Power;
import es.csic.iiia.fabregues.dip.board.Province;
import es.csic.iiia.fabregues.dip.board.Region;
import es.csic.iiia.fabregues.dip.comm.CommException;
import es.csic.iiia.fabregues.dip.comm.IComm;
import es.csic.iiia.fabregues.dip.orders.BLDOrder;
import es.csic.iiia.fabregues.dip.orders.DSBOrder;
import es.csic.iiia.fabregues.dip.orders.HLDOrder;
import es.csic.iiia.fabregues.dip.orders.MTOOrder;
import es.csic.iiia.fabregues.dip.orders.Order;
import es.csic.iiia.fabregues.dip.orders.REMOrder;
import es.csic.iiia.fabregues.dip.orders.RTOOrder;
import es.csic.iiia.fabregues.dip.orders.SUPMTOOrder;
import es.csic.iiia.fabregues.dip.orders.SUPOrder;
import es.csic.iiia.fabregues.dip.orders.WVEOrder;
import es.csic.iiia.fabregues.dip.comm.daide.DaideComm;



/**
 * This agent is an example that shows how you can implement a negotiating agent
 * on top of the strategic module of D-Brane.
 * 
 * 
 * @author Dave de Jonge
 *
 */
public class RandomNegotiator extends Player{

	public static final int DEFAULT_GAME_SERVER_PORT = 16713;
	public static final int DEFAULT_NEGO_SERVER_PORT = 16714;
	
	//Unless specified otherwise in the command line, this agent will always propose a draw after this year.
	public static final int DEFAULT_FINAL_YEAR = 2000; 
	
	/**
	 * Main method to start the agent.
	 * @param args
	 */
	public static void main(String[] args){
		
		
		//set the default name, game server port, and log path for the agent. 
		String name = "Random Negotiatior";
		String logPath = "log/";
		int gameServerPort = DEFAULT_GAME_SERVER_PORT;
		int negoPort = DEFAULT_NEGO_SERVER_PORT;
		int finalYear = DEFAULT_FINAL_YEAR;
		
		//Overwrite these values if specified by the arguments.
		for(int i=0; i<args.length; i++){
			
			//set the name of this agent
			if(args[i].equals("-name") && args.length > i+1){
				name = args[i+1];
			}
			
			//set the path to store the log file
			if(args[i].equals("-log") && args.length > i+1){
				logPath = args[i+1];
			}
			
			//set the final year
			if(args[i].equals("-fy") && args.length > i+1){
				try{
					finalYear = Integer.parseInt(args[i+1]);
				}catch (NumberFormatException e) {
					System.out.println("main() The final year argument is not a valid integer: " + args[i+1]);
					return;
				}
			}
			
			//set the port number of the game server
			if(args[i].equals("-gamePort") && args.length > i+1){
				
				try{
					gameServerPort = Integer.parseInt(args[i+1]);
				}catch (NumberFormatException e) {
					System.out.println("The port number argument is not a valid integer: " + args[i+1]);
					return;
				}
			}
			
			//set the port number of the negotiation server
			if(args[i].equals("-negoPort") && args.length > i+1){
				
				try{
					negoPort = Integer.parseInt(args[i+1]);
				}catch (NumberFormatException e) {
					System.out.println("The port number argument is not a valid integer: " + args[i+1]);
				}
			}
			
		}
		
		//Create the folder to store its log files.
		File logFolder = new File(logPath);
		logFolder.mkdirs();
		
		RandomNegotiator randomNegotiator = new RandomNegotiator(name, finalYear, logPath, gameServerPort, negoPort);
		
		//Connect to the game server.
		try{
			randomNegotiator.start(randomNegotiator.comm);
		}catch (Exception e) {
			e.printStackTrace();
		}
		
		
		//Make sure the log file is written to hard disk when the agent is shut down.
		final RandomNegotiator rn = randomNegotiator;
		Runtime.getRuntime().addShutdownHook(new Thread(new Runnable() {
	        public void run() {
    			rn.logger.writeToFile();
	        }
	    }));
	}
	
	
	//FIELDS
	
	//Random number generator.
	private Random random = new Random();
	
	/**Client to connect with the game server.*/
	private IComm comm;
	
	/**Client to connect with the negotiation server.*/
	private DiplomacyNegoClient negoClient;
	

	
	/** After This year the agent will always propose a draw.*/
	int finalYear;
	
	/**
	 * For logging debug information to a log file.
	 * To log something to the log file, call:  
	 * 		logger.logln("some text to log");
	 * To log something to the log file and simultaneously print it to the standard output stream, call:  
	 * 		logger.logln("some text to log", true);
	 * 
	 * Note however, that calling logln only stores the text in temporary memory. It will not be written to 
	 *   the file on hard disk until you call logger.writeTofile().
	 *   
	 * Also note that the logger is by default disabled. In order to enable it you must first call logger.enable()
	 * which in this example is done in the init() method of the RandomNegotiator.  
	 * 
	 * Furthermore, note that the Player class also defines a log field which should not be confused with this one.
	 * That logger is the logger provided by the
	 * DipGame framework which logs all the communication between game server and the agent.
	 * 
	 * */
	private Logger logger = new Logger();
	
	/**A list to store all deals that we are committed to.*/
	ArrayList<BasicDeal> confirmedDeals = new ArrayList<BasicDeal>();
	
	//CONSTRUCTOR
	RandomNegotiator(String name, int finalYear, String logPath, int gameServerPort, int negoServerPort){
		super(logPath);
		
		this.name = name;
		this.finalYear = finalYear;
		
		//Initialize the clients
		try {
			InetAddress gameServerIp =  InetAddress.getLocalHost();
			
			this.comm = new DaideComm(gameServerIp, gameServerPort, name);
			this.negoClient = new DiplomacyNegoClient(this, negoServerPort);
			
		} catch (UnknownHostException e) {
			e.printStackTrace();
		}
				

		
	}
	
	/**
	 * This method is called once, at the start of the game, before the 'game' field is set.
	 * 
	 * It is called when the HLO message is received from the game server.
	 * The HLO contains information about the game such as the power assigned to you, and the deadlines.
	 * 
	 * The power you are playing is stored in the field 'me'.
	 * The game field will still be null when this method is called.
	 * 
	 * It is not necessary to implement this method.
	 */
	@Override
	public void init() {
		
		//enable logging at the specified path.
		logger.enable(logPath, this.me.getName() + ".log");
		
		//write our name and the power we are playing to the log file.
		logger.logln(this.name + " playing as " + this.me.getName(), true);
		logger.writeToFile();
		
		//Connect to the negotiation server.
		this.negoClient.connect();
		
		//Wait till we the connection with the server is established and we have received a start message from the Notary.
		this.negoClient.waitTillReady();
		
		if(this.negoClient.getStatus() == STATUS.READY){
			logger.logln("RandomNegotiator.init() " + this.me.getName() + " Connection with negotiator correctly established. Ready to start negotiating!");
		}else{
			logger.logln("RandomNegotiator.init() " + this.me.getName() + " connection failed! " + this.negoClient.getStatus(), true);
		}
		logger.writeToFile();
	
	}
	
	
	/**
	 * This method is automatically called at the start of the game, after the 'game' field is set.
	 *
	 * It is called when the first NOW message is received from the game server.
	 * The NOW message contains the current phase and the positions of all the units.
	 * 
	 * Note: the init() method is called before the start() method.
	 * 
	 * It is not necessary to implement this method
	 * 
	 */
	@Override
	public void start() {
		
		//Send a welcome message to all other players.
		//the method negoClient.inform() can be used to send anything you like, without formal meaning.
		// The Notary will ignore such messages and simply forward them to all recipients.
		List<Power> receivers = game.getPowers();
		this.negoClient.sendInformalMessage(receivers, "Hello World! I am " + me.getName());
	}
	
	
	@Override
	public List<Order> play() {

		logger.logln();
		logger.logln("PHASE: " + game.getPhase() + " " + game.getYear());
		
		
		
		//Test whether any of the deals we are committed to have become in valid.
		// A deal is invalid if it has an order for a unit that is not at that location.
		// e.g. There is an order for France to move an army from PIC to PAR, but FRA currently does not have an
		//  army at PIC.
		// This can happen if you make deals for future rounds, but the game develops in an unexpected manner.
		// e.g. you agree to move an army from BEL to PIC in the current round, and then to move from PIC to PAR 
		// in the next round. However, the move from BEL to PIC fails.
		ArrayList<BasicDeal> invalidDeals = new ArrayList<BasicDeal>();
		for(BasicDeal confirmedDeal : confirmedDeals){
			
			//If testValidity returns null it means the deal is still valid.
			// If the deal is not valid it returns a String which explains why it isn't valid. 
			// It may be useful to print or log this String for debugging purposes.
			if(Utilities.testValidity(game, confirmedDeal) != null){
				invalidDeals.add(confirmedDeal);
			}
		}
		//Remove all invalid deals from the list of confirmed deals.
		confirmedDeals.removeAll(invalidDeals);
		
		
		if(game.getPhase() == Phase.SPR || game.getPhase() == Phase.FAL){
			
			negotiate();
			
			return generateRandomMoveOrders();
			
		}else if(game.getPhase() == Phase.SUM || game.getPhase() == Phase.AUT){
			
			//RETREAT PHASE
			logger.writeToFile();
			
			
			//RandomNegotiator does not negotiate during retreat phases, but you can implement your agent to do so.
			
			return generateRandomRetreatOrders();
			
		}else{
			
			//BUILD PHASE 
			logger.writeToFile();
			
			//RandomNegotiator does not negotiate during build phases, but you can implement your agent to do so.
			
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
				return new ArrayList<Order>();
			}
			
		}
		
	}

	
	
	void negotiate(){
		
		long negotiationDeadline = System.currentTimeMillis() + 3*1000; //Let's say we negotiate for 3 seconds.
		
		//This loop repeats 2 steps. The first step is to handle any incoming messages, 
		// while the second step tries to find deals to propose to the other negotiators.
		while(System.currentTimeMillis() < negotiationDeadline){
			
			
			//STEP 1: Handle incoming messages.
			
			
			//See if we have received any message from any of the other negotiators.
			// e.g. a new proposal or an acceptance of a proposal made earlier.
			while(negoClient.hasMessage()){
				//Warning: you may want to add some extra code to break out of this loop,
				// just in case the other agents send so many proposals that your agent can't get
				// the chance to make any proposals itself.
				
				//if yes, remove it from the message queue.
				Message receivedMessage = negoClient.removeMessageFromQueue();
				
				if(receivedMessage.getPerformative().equals(DiplomacyNegoClient.ACCEPT)){
					
					DiplomacyProposal acceptedProposal = (DiplomacyProposal)receivedMessage.getContent();
					
					this.logger.logln("RandomNegotiator.negotiate() Received acceptance from " + receivedMessage.getSender() + ": " + acceptedProposal);
					
					// Here we can handle any incoming acceptances.
					// This random negotiator doesn't do anything with such messages however.
					
					// Note: if a certain proposal has been accepted by all players it is still not considered
					// officially binding until the protocol manager has sent a CONFIRM message.
					
					
				}else if(receivedMessage.getPerformative().equals(DiplomacyNegoClient.PROPOSE)){
					
					DiplomacyProposal receivedProposal = (DiplomacyProposal)receivedMessage.getContent();
					
					this.logger.logln("RandomNegotiator.negotiate() Received proposal: " + receivedProposal);
					
					BasicDeal deal = (BasicDeal)receivedProposal.getProposedDeal();
					
					boolean outDated = false;
					
					for(DMZ dmz : deal.getDemilitarizedZones()){
						
						
						//TODO: decide whether this DMZ is acceptable or not (in combination with the rest of the proposed deal).
						/*
						List<Power> powers = dmz.getPowers();
						List<Province> provinces = dmz.getProvinces();
						*/
						
						
						// Sometimes we may receive messages too late, so we check if the proposal does not
						// refer to some round of the game that has already passed.
						if( isHistory(dmz.getPhase(), dmz.getYear())){
							outDated = true;
							break;
						}
					}
					for(OrderCommitment orderCommitment : deal.getOrderCommitments()){
						
						
						// Sometimes we may receive messages too late, so we check if the proposal does not
						// refer to some round of the game that has already passed.
						if( isHistory(orderCommitment.getPhase(), orderCommitment.getYear())){
							outDated = true;
						}
						if(outDated){
							break;
						}
						
						//TODO: decide whether this order commitment is acceptable or not (in combination with the rest of the proposed deal).
						/*Order order = orderCommitment.getOrder();*/
					}
					
					String consistencyReport = null;
					if(!outDated){
					
						List<BasicDeal> commitments = new ArrayList<BasicDeal>();
						commitments.addAll(this.confirmedDeals);
						commitments.add(deal);
						consistencyReport = Utilities.testConsistency(game, commitments);
						
						// If testConsistency returns null it means the given list of deals is consistent.
						// If the list is not consistent it returns a String which explains what is wrong. 
						// It may be useful to print or log this String for debugging purposes.
						
					}
					
					
					
					if(!outDated && consistencyReport == null){
						
						// This agent simply flips a coin to determine whether to accept the proposal or not.
						if(random.nextInt(2) == 0){ // accept with 50% probability.
							this.negoClient.acceptProposal(receivedProposal.getId());
							this.logger.logln("RandomNegotiator.negotiate()  Accepting: " + receivedProposal);
						}
					}
					
					//We have received a new proposal. Let's evaluate whether we should accept it or not.
					
				}else if(receivedMessage.getPerformative().equals(DiplomacyNegoClient.CONFIRM)){
					
					// The protocol manager confirms that a certain proposal has been accepted by all players involved in it.
					// From now on we consider the deal as a binding agreement.
					
					DiplomacyProposal confirmedProposal = (DiplomacyProposal)receivedMessage.getContent();
					
					//this.logger.logln();
					this.logger.logln("RandomNegotiator.negotiate() RECEIVED CONFIRMATION OF: " + confirmedProposal);
					
					BasicDeal confirmedDeal = (BasicDeal)confirmedProposal.getProposedDeal();
					
					this.confirmedDeals.add(confirmedDeal);
					
					//Reject any proposal that has not yet been confirmed and that is inconsistent with the confirmed deal.
					// NOTE that normally this is not really necessary because the Notary will already check that 
					// any deal is consistent with earlier confirmed deals before it becomes confirmed. 
					// However, this behavior of the Notary may be turned off in which case we do need to check consistency ourselves.
					List<BasicDeal> deals = new ArrayList<BasicDeal>();
					deals.add(confirmedDeal);
					for(DiplomacyProposal standingProposal : this.negoClient.getUnconfirmedProposals()){
						deals.add((BasicDeal)standingProposal.getProposedDeal());
						
						if(Utilities.testConsistency(game, deals) != null){
							this.negoClient.rejectProposal(standingProposal.getId());
						}
						
						deals.remove(1);
					}
					

					
				}else if(receivedMessage.getPerformative().equals(DiplomacyNegoClient.REJECT)){
					
					DiplomacyProposal rejectedProposal = (DiplomacyProposal)receivedMessage.getContent();
					
					// Some player has rejected a certain proposal.
					// This random negotiator doesn't do anything with such messages however.
					
					//If a player first accepts a proposal and then rejects the same proposal the reject message cancels 
					// his earlier accept proposal.
					// However, this is not true if the reject message is sent after the Notary has already sent a confirm
					// message for that proposal. Once a proposal is confirmed it cannot be undone anymore.
				}else{
					
					//We have received any other kind of message.
					
					this.logger.logln("Received a message of unhandled type: " + receivedMessage.getPerformative() + ". Message content: " + receivedMessage.getContent().toString());
					
				}
			
			}
			
			
			
			//STEP 2:  try to find a proposal to make, and if we do find one, propose it.
			BasicDeal newDealToPropose = searchForNewDealToPropose();
			
			if(newDealToPropose != null){
				
				try {
					this.logger.logln("RandomNegotiator.negotiate() Proposing: " + newDealToPropose);
					this.negoClient.proposeDeal(newDealToPropose);
					
				} catch (IOException e) {
					e.printStackTrace();
				}
			}
			
			
		}
	}

	
	BasicDeal searchForNewDealToPropose(){
		
		//waste some time to simulate that we are performing a time-consuming search algorithm.
		try {
			Thread.sleep(500);
		} catch (InterruptedException e) {

		}
		
		//TODO: for a real implementation, we should still check that the deal we want to propose
		// is consistent with any deals that we are committed to (the deals that have been confirmed).
		//We can get the list of all confirmed deals by calling: this.negoClient.getConfirmedDeals();
		
		//Furthermore, we need to check whether it is consistent with the deals that have been proposed 
		// so far (either by me or by another power), but that are not yet confirmed.
		// We can get a list of such deals by calling:	this.negoClient.getProposedDeals();
		
		//If this list contains some deal A that is not consistent with a deal B we wish to propose,
		// then we should either first send a reject message to reject A, or we should not propose B.
		//
		// In case we do decide to propose B without rejecting A anyway, then we risk that both will get confirmed,
		// which means that we will be forced to disobey one of our commitments, which will harm our reputation.
		
		
		if(random.nextBoolean()){ //sometimes return null to simulate an unsuccessful search.
			return null;
		}else{
			return generateRandomDeal(); //return a randomly generated deal.
		}
	}
	
	
	
	/**
	 * After each power has submitted its orders, this method is called several times: 
	 * once for each order submitted by any other power.
	 * 
	 * You can use this to verify whether your allies have obeyed their agreements.
	 * 
	 * @param orderSubmittedByOtherPlayer An order submitted by any of the other powers.
	 */
	@Override
	public void receivedOrder(Order orderSubmittedByOtherPlayer) {
		
	}
	
	/**
	 * Returns true if the given phase and year are in the past with respect to the current phase and year of the game.
	 * @param phase
	 * @param year
	 * @return
	 */
	boolean isHistory(Phase phase, int year){
		
		if(year == game.getYear()){
			return getPhaseValue(phase) < getPhaseValue(game.getPhase());
		}
		
		return year < game.getYear();
	}
	
	int getPhaseValue(Phase phase){
		
		switch (phase) {
		case SPR:
			return 0;
		case SUM:
			return 1;
		case FAL:
			return 2;
		case AUT:
			return 3;
		case WIN:
			return 4;
		default:
			return -1;
		}
		
		
	}
	
	
	/**
	 * Generates a random list of orders for Spring or Fal phases such that they comply with the commitments we have made during the negotiations.<br/>
	 * (unless there is any inconsistency between the commitments).<br/>
	 * 
	 * @return A list containing exactly one order for each of our units.
	 */
	private List<Order> generateRandomMoveOrders() {
		
		//The list of orders that is going to be returned by this method.
		List<Order> orders = new ArrayList<Order>(me.getControlledRegions().size());
		
		//list containing our units
		List<Region> units = new ArrayList<Region>(me.getControlledRegions().size());
		for (Region region : me.getControlledRegions()) {
			units.add(region);
		}
		
		//For every order we create we use this table to map its destination to the order.
		// This is useful for creating support orders.
		HashMap<Province, Order> destination2order = new HashMap<Province, Order>();
		
		
		
		
		//Check if we are committed to any orders, and collect all provinces we can't enter.
		ArrayList<Province> illegalProvinces = new ArrayList<>();
		for(BasicDeal deal : this.confirmedDeals){
			
			for(OrderCommitment orderCommitment : deal.getOrderCommitments()){
				
				//Check if the OrderCommitment refers to the current phase.
				if(orderCommitment.getPhase() != game.getPhase()){
					continue;
				}
				if(orderCommitment.getYear() != game.getYear()){
					continue;
				}
				
				Order order = orderCommitment.getOrder();
				
				if(order.getPower().equals(me)){
					
					boolean wasOnTheList = units.remove(order.getLocation()); //remove the unit of this order from the list of units that need to receive an order.
					
					if(wasOnTheList){
						orders.add(order); // add the order we have committed to to the list of orders
					}
					//if the unit wasn't on the list it means it has already received an order and we can't obey the current order.
					// or it could mean that the order is impossible to execute because we simply don't have any unit at that location.
					
					//EDIT: this is not entirely correct! if the earlier order was a Hold order and the current order is a support order,
					// then we can still consider them consistent. In that case we should remove the Hold order from the list of orders and replace it 
					// with the support order. We leave that as an exercise.
					
					
				}
			}
			
			for(DMZ dmz : deal.getDemilitarizedZones()){
				
				//Check if the DMZ refers to the current phase.
				if(dmz.getPhase() != game.getPhase()){
					continue;
				}
				if(dmz.getYear() != game.getYear()){
					continue;
				}
				
				if(dmz.getPowers().contains(me)){ //If the DMZ involves me, then I cannot enter any of its provinces.
					illegalProvinces.addAll(dmz.getProvinces());
				}
				
			}
		}
		
		
		
		
		for(Region unit : units){	
			
			
			//create a list of possible regions the unit could move into
			List<Region> potentialDestinations = new ArrayList<Region>(unit.getAdjacentRegions().size() + 1);
			for (Region region : unit.getAdjacentRegions() ) {
				
				if( ! illegalProvinces.contains(region.getProvince())){
					potentialDestinations.add(region);
				}
			}
			// Also add the current location to this list (we can hold rather than move)
			if( ! illegalProvinces.contains(unit.getProvince()) || potentialDestinations.isEmpty()){
				potentialDestinations.add(unit);
			}
			//Note: if the unit does not have any place to go because all its possible destinations are 
			// demilitarized, including its current location, then we still add the current location to 
			// its possible destination.
			
			//choose a random destination:			
			int randomInt = random.nextInt(potentialDestinations.size());		
			Region destination = potentialDestinations.get(randomInt);
		
		
		
			//add new order to list of orders
			if(unit.equals(destination)){
				
				//If the current location of the unit equals its destination, then we 
				// create a Hold order, or a Support Order.
				
				Order newOrder = null;
				
				// To create a support order, we must check that its location is adjacent to any province
				// that is the destination of another order.
				Order orderThatCanReceiveSupport = null;
				for(Region adjacentRegion : unit.getAdjacentRegions()){
					Province adjacentProvince = adjacentRegion.getProvince();
					
					orderThatCanReceiveSupport = destination2order.get(adjacentProvince);
					
					if(orderThatCanReceiveSupport != null){
						
						if(orderThatCanReceiveSupport instanceof MTOOrder){
							
							newOrder = new SUPMTOOrder(me, unit, (MTOOrder)orderThatCanReceiveSupport);
							
						}else{
							newOrder = new SUPOrder(me, unit, orderThatCanReceiveSupport);
						}
						
						break;
					}
					
				}
				
				//If the current unit can't give support to any other unit, then we create a hold order.
				if(newOrder == null){
					newOrder = new HLDOrder(me, unit);
				}
				
				orders.add(newOrder);
				destination2order.put(unit.getProvince(), newOrder);
				
				
			}else{
				
				MTOOrder mtoOrder = new MTOOrder(me, unit, destination);
				orders.add(mtoOrder);
				
				 //TODO: remove debug
				 if(unit.equals(destination)){
					 throw new RuntimeException("DBraneTactics.determinePartialPlans() Error!");
				 }
				
				destination2order.put(mtoOrder.getDestination().getProvince(), mtoOrder);
			}
		}
		
		this.logger.logln();
		this.logger.logln("Submitting the following orders:");
		this.logger.logln(orders);
		this.logger.writeToFile();
		
		return orders;
	}
	
	
	private List<Order> generateRandomRetreatOrders() {
		
		List<Order> orders = new ArrayList<Order>(game.getDislodgedRegions().size());
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
				
			}else{
				
				//otherwise, pick a random destination for the unit and retreat to there.
				randomInt = random.nextInt(potentialDestinations.size());
				orders.add(new RTOOrder(unit, me, potentialDestinations.get(randomInt)));			
			}
		}
			
			
		return orders;
	}
	
	private List<Order> generateRandomBuildOrders(int nBuilds) {
		
		//list to store our orders
		List<Order> orders = new ArrayList<Order>(nBuilds);
		
		//we can build in any region of a province that is:
		//1. a home province, and
		//2. owned by us, and
		//3. currently not occupied (controlled)
		
		// Create a list of such available provinces.
		List<Province> availableProvinces = new ArrayList<Province>();
		
		//get all available provinces:
		for(Province province : me.getHomes()){ //loop over all my Home Supply Centers
			
			if(me.isOwning(province) && !me.isControlling(province)){ //check that i am the current owner and that I do not have any units in that province.
				availableProvinces.add(province);
			}
		}

		
		//fill the list of orders
		for(int i=0; i<nBuilds && availableProvinces.size() > 0; i++){
			
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
		while(orders.size() < nBuilds){
			orders.add(new WVEOrder(me));
		}
		
		
		return orders;
	}

	private List<Order> generateRandomRemoveOrders(int nRemoves) {
		
		//list to store our orders
		List<Order> orders = new ArrayList<Order>(nRemoves);
		
		//list containing our units
		List<Region> units = new ArrayList<Region>(me.getControlledRegions().size());
		for (Region region : me.getControlledRegions()) {
			units.add(region);
		}
		
		for(int i=0; i<nRemoves && units.size() > 0; i++){
			
			int randomInt = random.nextInt(units.size());
			Region unit = units.remove(randomInt);
			orders.add(new REMOrder(me, unit));
			
		}
		
		return orders;
	}
	
	
	public BasicDeal generateRandomDeal(){
		
		//Get the names of all the powers that are connected to the negotiation server (some players may be non-negotiating agents, so they are not connected.)
		List<String> negotiatingPowers = negoClient.getRegisteredNames();
		
		//Make a copy of this list that only contains powers that are still alive.
		// (A power is dead when it has lost all its armies and fleet)
		List<Power> aliveNegotiatingPowers = new ArrayList<Power>(7);
		for(String powerName : negotiatingPowers){
			
			Power negotiatingPower = game.getPower(powerName);
			
			if( ! game.isDead(negotiatingPower)){
				aliveNegotiatingPowers.add(negotiatingPower);
			}
		}
		
		int numAliveNegoPowers = aliveNegotiatingPowers.size();
		if(numAliveNegoPowers < 2){
			return null;
		}
		
		
		//Let's generate 3 random demilitarized zones.
		List<DMZ> demilitarizedZones = new ArrayList<DMZ>(3);
		for(int i=0; i<3; i++){
			
			//1. Create a list of powers for the DMZ
			ArrayList<Power> powers = new ArrayList<Power>(2);
			
			//1a. add myself to the list
			powers.add(me);
			
			//1b. add a random other power to the list.
			Power randomPower = me;
			while(randomPower.equals(me)){
				
				int numNegoPowers = aliveNegotiatingPowers.size();
				randomPower = aliveNegotiatingPowers.get(random.nextInt(numNegoPowers));
			}
			powers.add(randomPower);
			
			//2. Create a list of provinces for the DMZ.
			ArrayList<Province> provinces = new ArrayList<Province>();
			for(int j=0; j<3; j++){
				int numProvinces = this.game.getProvinces().size();
				Province randomProvince = this.game.getProvinces().get(random.nextInt(numProvinces));
				provinces.add(randomProvince);
			}
			
			
			//The RandomNegotiator only generates deals for the current year and phase. 
			// However, you can pick any year and phase here, as long as they do not lie in the past.
			// (actually, you can also propose deals for rounds in the past, but it doesn't make any sense
			//  since you obviously cannot obey such deals).
			demilitarizedZones.add(new DMZ( game.getYear(), game.getPhase(), powers, provinces));

		}
		
		
		
		//let's generate 3 random orderCommitments
		List<OrderCommitment> randomOrderCommitments = new ArrayList<OrderCommitment>();
		
		//get all units of the negotiating powers.
		List<Region> units = new ArrayList<Region>();
		for(Power power : aliveNegotiatingPowers){
			units.addAll(power.getControlledRegions());
		}
		
		for(int i=0; i<3; i++){
			
			//Pick a random unit and remove it from the list
			if(units.size() == 0){
				break;
			}
			Region randomUnit = units.remove(random.nextInt(units.size()));
			
			//Get the corresponding power
			Power power = game.getController(randomUnit);
			
			//Determine a list of potential destinations for the unit.
			// a Region is a potential destination for a unit if it is adjacent to that unit (or it is the current location of the unit)
			//  and the Province is not demilitarized for the Power controlling that unit.
			List<Region> potentialDestinations = new ArrayList<Region>();
			
			//Create a list of adjacent regions, including the current location of the unit.
			List<Region> adjacentRegions = new ArrayList<>(randomUnit.getAdjacentRegions());
			adjacentRegions.add(randomUnit);
		
			for(Region adjacentRegion : adjacentRegions){
				
				Province adjacentProvince = adjacentRegion.getProvince();
				
				//Check that the adjacent Region is not demilitarized for the power controlling the unit.
				boolean isDemilitarized = false;
				for(DMZ dmz : demilitarizedZones){
					if(dmz.getPowers().contains(power) && dmz.getProvinces().contains(adjacentProvince)){
						isDemilitarized = true;
						break;
					}
					
				}
				
				//If it is not demilitarized, then we can add the region to the list of potential destinations.
				if(!isDemilitarized){
					potentialDestinations.add(adjacentRegion);
				}
			}
			
			
			int numPotentialDestinations = potentialDestinations.size();
			if(numPotentialDestinations > 0){
				
				Region randomDestination = potentialDestinations.get(random.nextInt(numPotentialDestinations));
				
				Order randomOrder;
				if(randomDestination.equals(randomUnit)){
					randomOrder = new HLDOrder(power, randomUnit);
				}else{
					randomOrder = new MTOOrder(power, randomUnit, randomDestination);
				}
				// Of course we could also propose random support orders, but we don't do that here.
				
				
				//We only generate deals for the current year and phase. 
				// However, you can pick any year and phase here, as long as they do not lie in the past.
				// (actually, you can also propose deals for rounds in the past, but it doesn't make any sense
				//  since you obviously cannot obey such deals).
				randomOrderCommitments.add(new OrderCommitment(game.getYear(), game.getPhase(), randomOrder));
			}

			
		}
		
		

		
		return new BasicDeal(randomOrderCommitments, demilitarizedZones);
		
	}
	
	

	
	/**
	 * This method is automatically called after every phase. 
	 * 
	 * It is not necessary to implement it.
	 * 
	 * @param gameState
	 */
	@Override
	public void phaseEnd(GameState gameState) {
		
		//To prevent games from taking too long, we automatically propose a draw after
		// the 1903 FAL phase.
		if((game.getYear() == finalYear && game.getPhase() == Phase.FAL) || game.getYear() > finalYear){
			proposeDraw();
		}
		
	}
	
	/**
	 * You can call this method if you want to propose a draw.
	 * 
	 * If all players that are not yet eliminated propose a draw in the same phase, then
	 * the server ends the game.
	 * 
	 * Copy-paste this method into your own bot if you want it to be able to propose draws.
	 */
	void proposeDraw(){
		try {
			comm.sendMessage(new String[]{"DRW"});
		} catch (CommException e) {
			e.printStackTrace();
		}
	}
	

	
	

	/**
	 * This method is automatically called when the game is over.
	 * 
	 * The message contains about the names of the players, the powers they played and the 
	 * number of supply centers owned at the end of the game.
	 * 
	 */
	@Override
	public void handleSMR(String[] message) {
		
		//write the log file.
		this.logger.writeToFile();
		
		//disconnect from the game server.
		this.comm.stop();
		
		//disconnect from the negotiation server.
		this.negoClient.closeConnection();
		
		//Call exit to stop the player.
		exit();
		

	}
	
	
	/**
	 * This method is automatically called if you submit an illegal order for one of your units.
	 * 
	 * It is highly recommended to copy-paste this method into your own bot because it allows you to 
	 * see what went wrong if it accidentally submitted a wrong order.
	 * 
	 * @param message
	 */
	@Override
	public void submissionError(String[] message) {
		
		
		//[THX, (, (, AUS, AMY, BUD, ), MTO, MAR, ), (, FAR, )]
		
		if(message.length < 2){
			logger.logln("submissionError() " + Arrays.toString(message), true);
			return;
		}
		
		String errorType = message[message.length - 2];
		
		String illegalOrder = "";
		for(int i=2; i<message.length-4; i++){
			illegalOrder += message[i] + " ";
		}
		
		logger.logln("Illegal order submitted: " + illegalOrder, true);
		
		switch (errorType) {
		case "FAR":
			logger.logln("Reason: Unit is trying to move to a non-adjacent region, or is trying to support a move to a non-adjacent region.", true);
			break;
		case "NSP":
			logger.logln("Reason: No such province.", true);
			break;
		case "NSU":
			logger.logln("Reason: No such unit.", true);
			break;
		case "NAS":
			logger.logln("Reason: Not at sea (for a convoying fleet)", true);
			break;
		case "NSF":
			logger.logln("Reason: No such fleet (in VIA section of CTO or the unit performing a CVY)", true);
			break;
		case "NSA":
			logger.logln("Reason: No such army (for unit being ordered to CTO or for unit being CVYed)", true);
			break;
		case "NYU":
			logger.logln("Reason: Not your unit", true);
			break;
		case "NRN":
			logger.logln("Reason: No retreat needed for this unit", true);
			break;
		case "NVR":
			logger.logln("Reason: Not a valid retreat space", true);
			break;
		case "YSC":
			logger.logln("Reason: Not your supply centre", true);
			break;
		case "ESC":
			logger.logln("Reason: Not an empty supply centre", true);
			break;
		case "HSC":
			logger.logln("Reason: Not a home supply centre", true);
			break;
		case "NSC":
			logger.logln("Reason: Not a supply centre", true);
			break;
		case "CST":
			logger.logln("Reason: No coast specified for fleet build in StP, or an attempt to build a fleet inland, or an army at sea.", true);
			break;
		case "NMB":
			logger.logln("Reason: No more builds allowed", true);
			break;
		case "NMR":
			logger.logln("Reason: No more removals allowed", true);
			break;
		case "NRS":
			logger.logln("Reason: Not the right season", true);
			break;
		default:
			
			logger.logln("submissionError() Received error message of unknown type: " + Arrays.toString(message), true);
			
			break;
		}
		
			//MBV means: Order is OK.

		
	}
}
