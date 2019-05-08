package ddejonge.bandana.exampleAgents;

import java.io.File;
import java.io.IOException;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.text.ParseException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Random;
import java.util.Vector;

import es.csic.iiia.fabregues.dip.Player;
import es.csic.iiia.fabregues.dip.board.Dislodgement;
import es.csic.iiia.fabregues.dip.board.Game;
import es.csic.iiia.fabregues.dip.board.GameState;
import es.csic.iiia.fabregues.dip.board.Phase;
import es.csic.iiia.fabregues.dip.board.Power;
import es.csic.iiia.fabregues.dip.board.Province;
import es.csic.iiia.fabregues.dip.board.Region;
import es.csic.iiia.fabregues.dip.comm.CommException;
import es.csic.iiia.fabregues.dip.comm.IComm;
import es.csic.iiia.fabregues.dip.orders.DSBOrder;
import es.csic.iiia.fabregues.dip.orders.HLDOrder;
import es.csic.iiia.fabregues.dip.orders.MTOOrder;
import es.csic.iiia.fabregues.dip.orders.Order;
import es.csic.iiia.fabregues.dip.orders.RTOOrder;
import es.csic.iiia.fabregues.dip.orders.SUPMTOOrder;
import es.csic.iiia.fabregues.dip.orders.SUPOrder;
import es.csic.iiia.fabregues.dip.comm.daide.DaideComm;
import ddejonge.bandana.dbraneTactics.DBraneTactics;
import ddejonge.bandana.dbraneTactics.Plan;
import ddejonge.bandana.negoProtocol.DMZ;
import ddejonge.bandana.negoProtocol.Deal;
import ddejonge.bandana.negoProtocol.BasicDeal;
import ddejonge.bandana.negoProtocol.DiplomacyNegoClient;
import ddejonge.bandana.negoProtocol.DiplomacyProposal;
import ddejonge.bandana.negoProtocol.OrderCommitment;
import ddejonge.bandana.tools.Logger;
import ddejonge.bandana.tools.Utilities;
import ddejonge.negoServer.Message;
import ddejonge.negoServer.NegotiationClient.STATUS;


/**
 * This agent is an example that shows how you can implement a negotiating agent
 * on top of the strategic module of D-Brane.
 * 
 * 
 * @author Dave de Jonge
 *
 */
public class DBraneExampleBot extends Player{

	public static final int DEFAULT_GAME_SERVER_PORT = 16713;
	public static final int DEFAULT_NEGO_SERVER_PORT = 16714;
	
	//Unless specified otherwise in the command line, this agent will always propose a draw after this year.
	public static final int DEFAULT_FINAL_YEAR = 2000; 
	
	//The time in milliseconds this agent takes to negotiate each round.
	public final int NEGOTIATION_LENGTH = 3000; 
	
	/**
	 * Main method to start the agent.
	 * @param args
	 */
	public static void main(String[] args){
		
		
		//set the default name, game server port, and log path for the agent. 
		String name = "D-Brane Tactics Example Agent";
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
			
			//set the path to store the log file
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
					System.out.println("main() The port number argument is not a valid integer: " + args[i+1]);
					return;
				}
			}
			
			//set the port number of the negotiation server
			if(args[i].equals("-negoPort") && args.length > i+1){
				
				try{
					negoPort = Integer.parseInt(args[i+1]);
				}catch (NumberFormatException e) {
					System.out.println("main() The port number argument is not a valid integer: " + args[i+1]);
					return;
				}
			}
			
		}
		
		//Create the folder to store its log files.
		File logFolder = new File(logPath);
		logFolder.mkdirs();
		
		DBraneExampleBot exampleAgent = new DBraneExampleBot(name, finalYear, logPath, gameServerPort, negoPort);
		
		//Connect to the game server.
		try{
			exampleAgent.start(exampleAgent.comm);
		}catch (Exception e) {
			e.printStackTrace();
		}
		
		//Make sure the log file is written to hard disk when the agent is shut down.
		final DBraneExampleBot exAgent = exampleAgent;
		Runtime.getRuntime().addShutdownHook(new Thread(new Runnable() {
	        public void run() {
	        	exAgent.logger.writeToFile();
	        }
	    }));
	}
	
	//FIELDS
	DBraneTactics dbraneTactics = new DBraneTactics();

	//Random number generator.
	private Random random = new Random();
	
	/**Client to connect with the game server.*/
	private IComm comm;
	
	/**To connect with the negotiation server.*/
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
	 * which in this example is done in the init() method of the DBraneExampleBot.  
	 * 
	 * Furthermore, note that the Player class also defines a log field which should not be confused with this one.
	 * That logger is the logger provided by the
	 * DipGame framework which logs all the communication between game server and the agent.
	 * 
	 * */
	private Logger logger = new Logger();
	
	/**A list to store all deals that we are committed to.*/
	ArrayList<BasicDeal> confirmedDeals = new ArrayList<BasicDeal>();
	
	DBraneExampleBot(String name, int finalYear, String logPath, int gameServerPort, int negoServerPort){
		super(logPath);
		
		this.name = name;
		this.finalYear = finalYear;
		
		//Initialize the clients
		try {
			InetAddress gameServerIp = InetAddress.getLocalHost();
			
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
			logger.logln(this.getClass().getSimpleName() + ".init() " + this.me.getName() + " Connection with negotiator correctly established. Ready to start negotiating!");
		}else{
			logger.logln(this.getClass().getSimpleName() + ".init() " + this.me.getName() + " connection failed! " + this.negoClient.getStatus(), true);
		}
		logger.writeToFile();
	
	}
	
	
	/**
	 * This method is called once, at the start of the game, when we have obtained the Game object.
	 * It is called after the first NOW message is received.
	 * (The NOW message contains the current phase and the positions of all the units.)
	 */
	@Override
	public void start() {
	}
	
	
	@Override
	public List<Order> play() {
		
		logger.logln();
		logger.logln("PHASE: " + game.getPhase() + " " + game.getYear());
		
		//The orders to return.
		ArrayList<Order> myOrders = new ArrayList<Order>();
		
	
		//list to be filled with all our allies. This means that we will not attack any supply center owned by any the powers in this list, 
		// and will assume that none of these powers will attack any supply center owned by us.
		//In this example we just create a fixed coalition structure. When implementing a real player you should of course come up with some smarter algorithm that
		// determines the coalition structure based on agreements made and supports given in previous rounds.  
		List<Power> myAllies = getAllies(game);
		
		
		//Test whether any of the deals we are committed to have become in valid.
		// A deal is invalid if it has an order for a unit that is not at that location.
		// e.g. There is an order for France to move an army from PIC to PAR, but FRA currently does not have an
		//  army at PIC.
		// This can happen if you make deals for future rounds, but the game develops in an unexpected manner.
		// e.g. you agree to move an army from BEL to PIC in the current round, and then to move from PIC to PAR 
		// in the next round. However, the move from BEL to PIC fails.
		ArrayList<BasicDeal> invalidDeals = new ArrayList<BasicDeal>();
		for(BasicDeal confirmedDeal : confirmedDeals){
			if(Utilities.testValidity(game, confirmedDeal) != null){
				invalidDeals.add(confirmedDeal);
				logger.logln("play() Deal has become invalid: " + confirmedDeal, true);
			}
		}
		//Remove all invalid deals from the list of confirmed deals.
		confirmedDeals.removeAll(invalidDeals);
		
		
		
		if(game.getPhase() == Phase.SPR || game.getPhase() == Phase.FAL){
			

			
			//MOVE PHASE
			//*1 ANALYZE the current world state. The results of the analysis are stored in a WorldState object. 
			//This object will next be used by determineBestPlan().
			
			
			//*2 NEGOTIATE!
			long negotiationDeadline = System.currentTimeMillis() + NEGOTIATION_LENGTH; //let's give the agent 3 seconds to negotiate.
			negotiate(myAllies, negotiationDeadline);
			
			
			//*3. DETERMINE BEST PLAN
			//Let the D-Brane Tactics module determine a plan that obeys the given deals.

			
			//First check whether the deals that we have negotiated are consistent.

			logger.logln();
			logger.logln("Confirmed Deals: " + confirmedDeals);
			
			// Test whether they are consistent. If yes, this method will return null. If not, it will return a string with an explanation what's wrong.
			// Note that in general, this will not happen because the Notary only confirms deals that are consistent with previously confirmed deals.
			// This is only required in case the consistency checking mechanism of the Notary has been turned off.
			String report = Utilities.testConsistency(game, confirmedDeals);
			
			if(report != null){
				
				//The confirmed deals are inconsistent! Print out the reason why.
				logger.logln(this.getClass().getSimpleName() + ".play() I am committed to inconsistent deals: " + report, true); 
			
			}else{
			
				//Now let the D-Brane Tactics module determine a plan of action that is consistent with the agreement.
				Plan plan = dbraneTactics.determineBestPlan(game, me, confirmedDeals, myAllies);
			
	
				if(plan == null){
					
					// If the D-Brane Tactics module returns null it means that it didn't manage to find a consistent plan.
					// Normally this should not happen because we have already checked that the agreements are consistent. 
					// Nevertheless, we take into account that this may happen, just in case there is a bug.
					
					logger.logln(this.getClass().getSimpleName() + ".play() " + this.me.getName() + " *** D-BraneTactics did not manage to find a plan obeying the following deals: " + confirmedDeals, true);
					
				}else{
					
					//if everything went okay dbraneTactics returned a Plan object
					// containing an order for each of our units, which are consistent with our commitments.
					
					//Add the orders of the plan to the list of orders we are going to return.
					myOrders.addAll(plan.getMyOrders());
					
					
					
						
					//THIS CODE BELOW IS JUST FOR DEBUGGING. 
					// Collect all OrderCommitments and Demilitarized Zones 
					// that we must obey the current turn and print them out in the log file.
					List<Order> committedOrders = new ArrayList<Order>();
					List<DMZ> demilitarizedZones = new ArrayList<DMZ>();
					for(BasicDeal deal : confirmedDeals){
						
						for(DMZ dmz : deal.getDemilitarizedZones()){
							
							if(dmz.getPhase().equals(game.getPhase()) && dmz.getYear() == game.getYear()){
								if(dmz.getPowers().contains(me)){
									demilitarizedZones.add(dmz);
								}
							}
						}
						
						for(OrderCommitment orderCommitment : deal.getOrderCommitments()){
							
							if(orderCommitment.getPhase().equals(game.getPhase()) && orderCommitment.getYear() == game.getYear()){
								if(orderCommitment.getOrder().getPower().equals(me)){
									committedOrders.add(orderCommitment.getOrder());
								}
							}
							
						}
					}

					logger.logln("Commitments to obey this turn: " + committedOrders + " " + demilitarizedZones);
					
				}
			}
			
	
			
			//For any unit that, for whatever reason, still doesn't have an order, add a hold order.
			// (Normally, this should only be necessary in case dbraneTactics didn't return a plan because the commitments were
			//  inconsistent. However, we call this method anyway, just in case something went wrong.).
			myOrders = Utilities.addHoldOrders(me, myOrders);
			
			
			logger.logln("I am submitting: " + myOrders);
			logger.writeToFile();
			
			return myOrders;
			
		}else if(game.getPhase() == Phase.SUM || game.getPhase() == Phase.AUT){
			
			//RETREAT PHASE
			logger.writeToFile();
			return generateRandomRetreats();
			
		}else{
			
			//BUILD PHASE 
			logger.writeToFile();
			return dbraneTactics.getWinterOrders(game, me, myAllies);
		}
		
		
		
		
		
	}

	
	

	/**
	 * After each power has submitted its orders, this method is called several times: 
	 * once for each order submitted by any power.
	 * 
	 * You can use this to verify whether your allies have obeyed their agreements.
	 * 
	 * @param order An order submitted by any of the other powers.
	 */
	@Override
	public void receivedOrder(Order order) {
		
	}
	
	
	List<Power> getAllies(Game game){
		
		ArrayList<Power> allies = new ArrayList<>(1);
		allies.add(me);
		
		//A real agent would use some algotithm to determine its allies. 
		//Here however, we just fill the list with 'me'.
		
		return allies;
		
	}
	
	private List<Order> generateRandomRetreats() {
		
		List<Order> orders = new ArrayList<Order>(game.getDislodgedRegions().size());
		int randomInt;
		
		HashMap<Region, Dislodgement> units = game.getDislodgedRegions();
		List<Region> dislodgedUnits = game.getDislodgedRegions(me);
		
		for (Region region : dislodgedUnits) {
			Dislodgement dislodgement = units.get(region);
			List<Region> dest = new ArrayList<Region>();

			dest.addAll(dislodgement.getRetreateTo());
			
			if (dest.size() == 0) {
				orders.add(new DSBOrder(region, me));
			}else{
				randomInt = random.nextInt(dest.size());
				orders.add(new RTOOrder(region, me, dest.get(randomInt)));			
			}
		}
			
			
		return orders;
	}
	
	
	
	
	public void negotiate(List<Power> myAllies, long negotiationDeadline) {
		
		BasicDeal newDealToPropose = null;
		
		
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
					
					// Note: if all agents involved in a proposal have accepted the proposal, then you will not receive an ACCEPT
					// message from the last agent that accepted it. Instead, you will directly receive a CONFIRM message from the
					// Protocol Manager.
					
				}else if(receivedMessage.getPerformative().equals(DiplomacyNegoClient.PROPOSE)){
					
					DiplomacyProposal receivedProposal = (DiplomacyProposal)receivedMessage.getContent();
					
					this.logger.logln("RandomNegotiator.negotiate() Received proposal: " + receivedProposal);
					
					BasicDeal deal = (BasicDeal)receivedProposal.getProposedDeal();
					
					boolean outDated = false;
					
					for(DMZ dmz : deal.getDemilitarizedZones()){
						
						// Sometimes we may receive messages too late, so we check if the proposal does not
						// refer to some round of the game that has already passed.
						if( isHistory(dmz.getPhase(), dmz.getYear())){
							outDated = true;
							break;
						}
						
						//TODO: decide whether this DMZ is acceptable or not (in combination with the rest of the proposed deal).
						/*
						List<Power> powers = dmz.getPowers();
						List<Province> provinces = dmz.getProvinces();
						*/

					}
					for(OrderCommitment orderCommitment : deal.getOrderCommitments()){
						
						
						// Sometimes we may receive messages too late, so we check if the proposal does not
						// refer to some round of the game that has already passed.
						if( isHistory(orderCommitment.getPhase(), orderCommitment.getYear())){
							outDated = true;
							break;
						}
						
						//TODO: decide whether this order commitment is acceptable or not (in combination with the rest of the proposed deal).
						/*Order order = orderCommitment.getOrder();*/
					}
					
					//If the deal is not outdated, then check that it is consistent with the deals we are already committed to.
					String consistencyReport = null;
					if(!outDated){
					
						List<BasicDeal> commitments = new ArrayList<BasicDeal>();
						commitments.addAll(this.confirmedDeals);
						commitments.add(deal);
						consistencyReport = Utilities.testConsistency(game, commitments);
						
						
					}
					
					if(!outDated && consistencyReport == null){
						
						// This agent simply flips a coin to determine whether to accept the proposal or not.
						if(random.nextInt(2) == 0){ // accept with 50% probability.
							this.negoClient.acceptProposal(receivedProposal.getId());
							this.logger.logln("RandomNegotiator.negotiate()  Accepting: " + receivedProposal);
						}
					}
					
										
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
					List<BasicDeal> deals = new ArrayList<BasicDeal>(2);
					deals.add(confirmedDeal);
					for(DiplomacyProposal standingProposal : this.negoClient.getUnconfirmedProposals()){
						
						//add this proposal to the list of deals.
						deals.add((BasicDeal)standingProposal.getProposedDeal());
						
						if(Utilities.testConsistency(game, deals) != null){
							this.negoClient.rejectProposal(standingProposal.getId());
						}
						
						//remove the deal again from the list, so that we can add the next standing deal to the list in the next iteration.
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
					
					this.logger.logln("Received a message of unhandled type: " + receivedMessage.getPerformative() + ". Message content: " + receivedMessage.getContent().toString(), true);
					
				}
			
			}
			
			
			
			//STEP 2:  try to find a proposal to make, and if we do find one, propose it.
			
			if(newDealToPropose == null){ //we only make one proposal per round, so we skip this if we have already proposed something.
				newDealToPropose = searchForNewDealToPropose(myAllies);
				
				if(newDealToPropose != null){
					
					try {
						this.logger.logln("RandomNegotiator.negotiate() Proposing: " + newDealToPropose);
						this.negoClient.proposeDeal(newDealToPropose);
	
					} catch (IOException e) {
						e.printStackTrace();
					}
				}
			}
			
			try {
				Thread.sleep(250);
			} catch (InterruptedException e) {
			}
			
			
		}
	}

	
	BasicDeal searchForNewDealToPropose(List<Power> myAllies){
		
		BasicDeal bestDeal = null;
		Plan bestPlan = null;

		//Get a copy of our list of current commitments.
		ArrayList<BasicDeal> commitments = new ArrayList<BasicDeal>(this.confirmedDeals);
		
		//First, let's see what happens if we do not make any new commitments.
		bestPlan = this.dbraneTactics.determineBestPlan(game, me, commitments, myAllies);
		
		//If our current commitments are already inconsistent then we certainly
		// shouldn't make any more commitments.
		if(bestPlan == null){
			return null;
		}
		
		//let's generate 10 random deals and pick the best one.
		for(int i=0; i<10; i++){
			
			//generate a random deal.
			BasicDeal randomDeal = generateRandomDeal();
			
			if(randomDeal == null){
				continue;
			}
			
			
			//add it to the list containing our existing commitments so that dBraneTactics can determine a plan.
			commitments.add(randomDeal);

			
			//Ask the D-Brane Tactical Module what it would do under these commitments.
			Plan plan = this.dbraneTactics.determineBestPlan(game, me, commitments, myAllies);
			
			//Check if the returned plan is better than the best plan found so far.
			if(plan != null && plan.getValue() > bestPlan.getValue()){
				bestPlan = plan;
				bestDeal = randomDeal;
			}
			
			
			//Remove the randomDeal from the list, for the next iteration.
			commitments.remove(commitments.size()-1);
			
			//NOTE: the value returned by plan.getValue() represents the number of Supply Centers that the D-Brane Tactical Module
			// expects to conquer in the current round under the given commitments.
			//
			// Of course, this is only a rough indication of which plan is truly the "best". After all, sometimes it is better
			// not to try to conquer as many Supply Centers as you can directly, but rather organize your armies and only attack in a later
			// stage.
			// Therefore, you may want to implement your own algorithm to determine which plan is the best.
			// You can call plan.getMyOrders() to retrieve the complete list of orders that D-Brane has chosen for you under the given commitments. 
			
		}
		
		
		return bestDeal;
		

		
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
		
		//if there are less than 2 negotiating powers left alive (only me), then it makes no sense to negotiate.
		int numAliveNegoPowers = aliveNegotiatingPowers.size();
		if(numAliveNegoPowers < 2){
			return null;
		}
		
		
		
		//Let's generate 3 random demilitarized zones.
		List<DMZ> demilitarizedZones = new ArrayList<DMZ>(3);
		for(int i=0; i<3; i++){
			
			//1. Create a list of powers
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
			
			//2. Create a list containing 3 random provinces.
			ArrayList<Province> provinces = new ArrayList<Province>();
			for(int j=0; j<3; j++){
				int numProvinces = this.game.getProvinces().size();
				Province randomProvince = this.game.getProvinces().get(random.nextInt(numProvinces));
				provinces.add(randomProvince);
			}
			
			
			//This agent only generates deals for the current year and phase. 
			// However, you can pick any year and phase here, as long as they do not lie in the past.
			// (actually, you can also propose deals for rounds in the past, but it doesn't make any sense
			//  since you obviously cannot obey such deals).
			demilitarizedZones.add(new DMZ( game.getYear(), game.getPhase(), powers, provinces));

		}
		
		
		
		
		//let's generate 3 random OrderCommitments
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
		
		BasicDeal deal = new BasicDeal(randomOrderCommitments, demilitarizedZones);

		
		return deal;
		
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
		// the FAL phase of the final year.
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
			logger.logln(this.getClass().getSimpleName() + ".submissionError() " + Arrays.toString(message), true);
			return;
		}
		
		String errorType = message[message.length - 2];
		
		String illegalOrder = "";
		for(int i=2; i<message.length-4; i++){
			illegalOrder += message[i] + " ";
		}
		
		logger.logln(this.getClass().getSimpleName() + ".submissionError() Illegal order submitted: " + illegalOrder, true);
		
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
	
}
